# backend/src/routers/batch.py

import io
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.schemas import (
    ReturnItemSchema,
    BatchUploadRecordSchema,
    BatchUploadResponseSchema,
    UserSchema,
)
from src.routers.auth import get_current_active_user
from src.services.batch_processor import batch_processor, BatchRecord
from src.services.qr_generator import qr_generator
from src.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batches", tags=["batch"])


def generate_batch_id() -> str:
    year = datetime.utcnow().year
    unique_part = str(uuid4())[:8].upper()
    return f"BAT-{year}-{unique_part}"


def generate_return_id() -> str:
    year = datetime.utcnow().year
    unique_part = str(uuid4())[:8].upper()
    return f"RET-{year}-{unique_part}"


def calculate_totals(items: list) -> tuple[int, Decimal, Decimal, Decimal]:
    total_items = sum(item.get("quantity", 1) for item in items)
    total_value = sum(
        Decimal(str(item.get("unit_price", 0))) * item.get("quantity", 1)
        for item in items
    )
    total_weight = sum(
        Decimal(str(item.get("weight_kg", 0))) * item.get("quantity", 1)
        for item in items
    )
    total_volume = sum(
        Decimal(str(item.get("volume_m3", 0))) * item.get("quantity", 1)
        for item in items
    )
    return total_items, total_value, total_weight, total_volume


def item_to_dict(item) -> dict:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return {
        "sku": item.sku,
        "product_name": item.product_name,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price),
        "weight_kg": float(item.weight_kg) if item.weight_kg else None,
        "volume_m3": float(item.volume_m3) if item.volume_m3 else None,
        "reason_code": item.reason_code,
        "reason_description": item.reason_description,
        "condition": item.condition,
        "batch_id": item.batch_id,
        "is_customized": getattr(item, "is_customized", False),
    }


def validate_batch_record(row: dict, row_number: int) -> tuple[BatchUploadRecordSchema, bool, list[str]]:
    errors = []

    if not row.get("sku"):
        errors.append("SKU es requerido")
    if not row.get("product_name"):
        errors.append("product_name es requerido")

    try:
        quantity = int(row.get("quantity", 0))
        if quantity < 1 or quantity > 9999:
            errors.append("quantity debe estar entre 1 y 9999")
    except (ValueError, TypeError):
        errors.append("quantity debe ser un numero entero valido")

    try:
        unit_price = Decimal(str(row.get("unit_price", 0)))
        if unit_price < 0:
            errors.append("unit_price no puede ser negativo")
    except (ValueError, TypeError):
        errors.append("unit_price debe ser un numero valido")

    weight_kg = None
    if row.get("weight_kg"):
        try:
            weight_kg = Decimal(str(row.get("weight_kg")))
            if weight_kg < 0:
                errors.append("weight_kg no puede ser negativo")
        except (ValueError, TypeError):
            errors.append("weight_kg debe ser un numero valido")

    volume_m3 = None
    if row.get("volume_m3"):
        try:
            volume_m3 = Decimal(str(row.get("volume_m3")))
            if volume_m3 < 0:
                errors.append("volume_m3 no puede ser negativo")
        except (ValueError, TypeError):
            errors.append("volume_m3 debe ser un numero valido")

    if not row.get("reason_code"):
        errors.append("reason_code es requerido")

    is_valid = len(errors) == 0

    record = BatchUploadRecordSchema(
        row_number=row_number,
        sku=str(row.get("sku", "")),
        product_name=str(row.get("product_name", "")),
        quantity=int(row.get("quantity", 1)),
        unit_price=Decimal(str(row.get("unit_price", 0))),
        weight_kg=weight_kg,
        volume_m3=volume_m3,
        reason_code=str(row.get("reason_code", "")),
        reason_description=row.get("reason_description"),
        condition=str(row.get("condition", "NEW")),
        batch_id=row.get("batch_id"),
        is_customized=bool(row.get("is_customized", False)),
        is_valid=is_valid,
        validation_errors=errors,
    )

    return record, is_valid, errors


@router.post("/upload", response_model=BatchUploadResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_batch(
    file: UploadFile = File(...),
    customer_id: str = Form(...),
    order_reference: str = Form(...),
    invoice_reference: str = Form(None),
    return_reason: str = Form(...),
    return_reason_description: str = Form(None),
    contact_email: str = Form(...),
    contact_phone: str = Form(None),
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal

    if current_user.role not in ["B2B_USER", "SUPERVISOR", "KAM", "ADMIN"]:
        logger.warning(
            f"User {current_user.username} with role {current_user.role} "
            f"attempted to upload batch without proper permissions"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para subir lotes B2B"
        )

    db = SessionLocal()
    start_time = time.time()

    try:
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser un CSV"
            )

        contents = await file.read()
        try:
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al leer el archivo CSV: {str(e)}"
            )

        required_columns = ["sku", "product_name", "quantity", "unit_price", "reason_code"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Columnas requeridas faltantes en CSV: {', '.join(missing_columns)}"
            )

        batch_id = generate_batch_id()
        records = []
        valid_count = 0
        invalid_count = 0

        for idx, row in df.iterrows():
            row_number = idx + 1
            row_dict = row.to_dict()
            row_dict["batch_id"] = batch_id

            record, is_valid, errors = validate_batch_record(row_dict, row_number)

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1

            records.append(record)

        processing_time = int((time.time() - start_time) * 1000)

        batch_query = text("""
            INSERT INTO batch_uploads (
                batch_id, customer_id, total_records, valid_records,
                invalid_records, records, status, processing_time_ms,
                uploaded_at
            ) VALUES (
                :batch_id, :customer_id, :total_records, :valid_records,
                :invalid_records, :records, :status, :processing_time_ms,
                :uploaded_at
            )
        """)

        db.execute(batch_query, {
            "batch_id": batch_id,
            "customer_id": customer_id,
            "total_records": len(records),
            "valid_records": valid_count,
            "invalid_records": invalid_count,
            "records": [r.model_dump() for r in records],
            "status": "PENDING" if invalid_count == 0 else "PARTIAL",
            "processing_time_ms": processing_time,
            "uploaded_at": datetime.utcnow(),
        })
        db.commit()

        logger.info(f"Batch {batch_id} uploaded by user {current_user.username}: {valid_count} valid, {invalid_count} invalid")

        return BatchUploadResponseSchema(
            batch_id=batch_id,
            total_records=len(records),
            valid_records=valid_count,
            invalid_records=invalid_count,
            records=records,
            processing_time_ms=processing_time,
            status="PENDING" if invalid_count == 0 else "PARTIAL",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing batch upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el lote: {str(e)}"
        )
    finally:
        db.close()


@router.get("/{batch_id}", response_model=BatchUploadResponseSchema)
async def get_batch_status(
    batch_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT batch_id, customer_id, total_records, valid_records,
                   invalid_records, records, status, processing_time_ms,
                   uploaded_at
            FROM batch_uploads
            WHERE batch_id = :batch_id
        """)

        result = db.execute(query, {"batch_id": batch_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {batch_id} no encontrado"
            )

        records_data = result[4]
        records = [BatchUploadRecordSchema(**r) for r in records_data]

        return BatchUploadResponseSchema(
            batch_id=result[0],
            total_records=result[2],
            valid_records=result[3],
            invalid_records=result[4],
            records=records,
            processing_time_ms=result[7],
            status=result[6],
        )
    finally:
        db.close()


@router.post("/{batch_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_batch(
    batch_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal

    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores y KAM pueden procesar lotes"
        )

    db = SessionLocal()
    try:
        batch_query = text("""
            SELECT batch_id, customer_id, total_records, valid_records,
                   invalid_records, records, status, processing_time_ms,
                   uploaded_at
            FROM batch_uploads
            WHERE batch_id = :batch_id
        """)

        result = db.execute(batch_query, {"batch_id": batch_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {batch_id} no encontrado"
            )

        records_data = result[4]
        records = [BatchRecord.from_dict(r) for r in records_data]

        valid_records = [r for r in records if r.is_valid]
        if not valid_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay registros validos para procesar"
            )

        items_data = []
        for record in valid_records:
            items_data.append({
                "sku": record.sku,
                "product_name": record.product_name,
                "quantity": record.quantity,
                "unit_price": float(record.unit_price),
                "weight_kg": float(record.weight_kg) if record.weight_kg else None,
                "volume_m3": float(record.volume_m3) if record.volume_m3 else None,
                "reason_code": record.reason_code,
                "reason_description": record.reason_description,
                "condition": record.condition,
                "batch_id": batch_id,
                "is_customized": record.is_customized,
            })

        total_items, total_value, total_weight, total_volume = calculate_totals(items_data)

        decision = decision_engine.evaluate(
            channel="B2B",
            customer_type="CORPORATE",
            items=items_data,
            total_items=total_items,
            total_value=total_value,
            total_weight_kg=total_weight,
            total_volume_m3=total_volume,
            return_reason="BATCH_RETURN",
            is_batch=True,
            batch_id=batch_id,
        )

        trace_id = str(uuid4())

        for record in valid_records:
            return_id = generate_return_id()
            return_query = text("""
                INSERT INTO returns (
                    return_id, trace_id, channel, customer_id, customer_type,
                    order_reference, invoice_reference, items, total_items,
                    total_value, total_weight_kg, total_volume_m3, return_reason,
                    return_reason_description, contact_email, contact_phone, status,
                    destination, method, decision_score, decision_explanation,
                    estimated_reimbursement, requires_kam_approval, created_by,
                    processing_time_ms, batch_id, created_at, updated_at
                ) VALUES (
                    :return_id, :trace_id, :channel, :customer_id, :customer_type,
                    :order_reference, :invoice_reference, :items, :total_items,
                    :total_value, :total_weight_kg, :total_volume_m3, :return_reason,
                    :return_reason_description, :contact_email, :contact_phone, :status,
                    :destination, :method, :decision_score, :decision_explanation,
                    :estimated_reimbursement, :requires_kam_approval, :created_by,
                    :processing_time_ms, :batch_id, :created_at, :updated_at
                )
            """)

            item_data = [i for i in items_data if i.get("batch_id") == batch_id and i["sku"] == record.sku]
            item = item_data[0] if item_data else items_data[0]

            db.execute(return_query, {
                "return_id": return_id,
                "trace_id": trace_id,
                "channel": "B2B",
                "customer_id": result[1],
                "customer_type": "CORPORATE",
                "order_reference": "BATCH",
                "invoice_reference": None,
                "items": [item],
                "total_items": record.quantity,
                "total_value": record.unit_price * record.quantity,
                "total_weight_kg": (record.weight_kg * record.quantity) if record.weight_kg else Decimal("0"),
                "total_volume_m3": (record.volume_m3 * record.quantity) if record.volume_m3 else Decimal("0"),
                "return_reason": "BATCH_RETURN",
                "return_reason_description": f"Procesado desde lote {batch_id}",
                "contact_email": "batch@system.local",
                "contact_phone": None,
                "status": decision.status,
                "destination": decision.destination,
                "method": decision.return_method,
                "decision_score": decision.score,
                "decision_explanation": decision.explanation,
                "estimated_reimbursement": decision.estimated_refund,
                "requires_kam_approval": decision.requires_kam_approval,
                "created_by": current_user.username,
                "processing_time_ms": decision.processing_time_ms,
                "batch_id": batch_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })

        update_batch_query = text("""
            UPDATE batch_uploads
            SET status = 'COMPLETED'
            WHERE batch_id = :batch_id
        """)
        db.execute(update_batch_query, {"batch_id": batch_id})

        db.commit()

        logger.info(f"Batch {batch_id} processed by {current_user.username}: {len(valid_records)} returns created")

        return {
            "batch_id": batch_id,
            "status": "COMPLETED",
            "returns_created": len(valid_records),
            "destination": decision.destination,
            "method": decision.return_method,
            "requires_kam_approval": decision.requires_kam_approval,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el lote: {str(e)}"
        )
    finally:
        db.close()


@router.get("/", response_model=list)
async def list_batches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["B2B_USER", "SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para listar lotes"
        )

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        offset = (page - 1) * page_size

        where_clauses = []
        params = {}

        if status_filter:
            where_clauses.append("status = :status")
            params["status"] = status_filter
        if customer_id:
            where_clauses.append("customer_id = :customer_id")
            params["customer_id"] = customer_id

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_query = text(f"SELECT COUNT(*) FROM batch_uploads WHERE {where_sql}")
        total = db.execute(count_query, params).scalar()

        select_query = text(f"""
            SELECT batch_id, customer_id, total_records, valid_records,
                   invalid_records, status, processing_time_ms, uploaded_at
            FROM batch_uploads
            WHERE {where_sql}
            ORDER BY uploaded_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params["limit"] = page_size
        params["offset"] = offset

        results = db.execute(select_query, params).fetchall()

        batches = []
        for row in results:
            batches.append({
                "batch_id": row[0],
                "customer_id": row[1],
                "total_records": row[2],
                "valid_records": row[3],
                "invalid_records": row[4],
                "status": row[5],
                "processing_time_ms": row[6],
                "uploaded_at": row[7].isoformat() if row[7] else None,
            })

        return batches
    finally:
        db.close()


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar lotes"
        )

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("SELECT batch_id FROM batch_uploads WHERE batch_id = :batch_id")
        existing = db.execute(check_query, {"batch_id": batch_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {batch_id} no encontrado"
            )

        delete_query = text("DELETE FROM batch_uploads WHERE batch_id = :batch_id")
        db.execute(delete_query, {"batch_id": batch_id})
        db.commit()

        logger.info(f"Batch {batch_id} deleted by user {current_user.username}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el lote: {str(e)}"
        )
    finally:
        db.close()


@router.post("/{batch_id}/approve", status_code=status.HTTP_201_CREATED)
async def approve_batch(
    batch_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("SELECT batch_id, status FROM batch_uploads WHERE batch_id = :batch_id")
        existing = db.execute(check_query, {"batch_id": batch_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {batch_id} no encontrado"
            )

        update_query = text("""
            UPDATE batch_uploads
            SET status = 'APPROVED'
            WHERE batch_id = :batch_id
        """)
        db.execute(update_query, {"batch_id": batch_id})
        db.commit()

        logger.info(f"Batch {batch_id} approved by user {current_user.username}")

        return {
            "batch_id": batch_id,
            "status": "APPROVED",
            "approved_by": current_user.username,
            "approved_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aprobar el lote: {str(e)}"
        )
    finally:
        db.close()


@router.post("/{batch_id}/reject", status_code=status.HTTP_201_CREATED)
async def reject_batch(
    batch_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("SELECT batch_id, status FROM batch_uploads WHERE batch_id = :batch_id")
        existing = db.execute(check_query, {"batch_id": batch_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote {batch_id} no encontrado"
            )

        update_query = text("""
            UPDATE batch_uploads
            SET status = 'REJECTED'
            WHERE batch_id = :batch_id
        """)
        db.execute(update_query, {"batch_id": batch_id})
        db.commit()

        logger.info(f"Batch {batch_id} rejected by user {current_user.username}")

        return {
            "batch_id": batch_id,
            "status": "REJECTED",
            "rejected_by": current_user.username,
            "rejected_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al rechazar el lote: {str(e)}"
        )
    finally:
        db.close()


def require_kam_role(current_user: UserSchema) -> UserSchema:
    if current_user.role not in ["KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol KAM o ADMIN para esta accion"
        )
    return current_user
