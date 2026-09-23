# backend/src/routers/returns.py

import logging
import time
import qrcode
import io
import base64
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import io

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.schemas import (
    ReturnRequestCreateSchema,
    ReturnRequestResponseSchema,
    ReturnsListResponseSchema,
    ReturnsFiltersSchema,
    DecisionInputSchema,
    DecisionResultSchema,
    UserSchema,
    ErrorResponseSchema,
    BatchUploadRecordSchema,
    BatchUploadResponseSchema,
    BatchUploadCreateSchema,
)
from src.routers.auth import get_current_active_user
from src.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/returns", tags=["returns"])


def generate_return_id() -> str:
    year = datetime.utcnow().year
    unique_part = str(uuid4())[:8].upper()
    return f"RET-{year}-{unique_part}"


def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    return qr_base64


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


@router.post("", response_model=ReturnRequestResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_return(
    return_data: ReturnRequestCreateSchema,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        return_id = generate_return_id()
        trace_id = str(uuid4())
        created_at = datetime.utcnow()

        items_data = [item_to_dict(item) for item in return_data.items]
        total_items, total_value, total_weight, total_volume = calculate_totals(items_data)

        decision = decision_engine.evaluate(
            channel=return_data.channel,
            customer_type=return_data.customer_type,
            items=items_data,
            total_items=total_items,
            total_value=total_value,
            total_weight_kg=total_weight,
            total_volume_m3=total_volume,
            return_reason=return_data.return_reason,
        )

        qr_code_data = None
        if decision.return_method == "DROP_OFF":
            token_data = f"RET:{return_id}:{trace_id}"
            qr_code_data = generate_qr_code(token_data)

        query = text("""
            INSERT INTO returns (
                return_id, trace_id, channel, customer_id, customer_type,
                order_reference, invoice_reference, items, total_items,
                total_value, total_weight_kg, total_volume_m3, return_reason,
                return_reason_description, pickup_address, preferred_drop_off_id,
                preferred_time_slot, contact_email, contact_phone, status,
                destination, method, decision_score, decision_explanation,
                estimated_reimbursement, qr_code, drop_off_point_id,
                requires_kam_approval, created_by, processing_time_ms,
                created_at, updated_at
            ) VALUES (
                :return_id, :trace_id, :channel, :customer_id, :customer_type,
                :order_reference, :invoice_reference, :items, :total_items,
                :total_value, :total_weight_kg, :total_volume_m3, :return_reason,
                :return_reason_description, :pickup_address, :preferred_drop_off_id,
                :preferred_time_slot, :contact_email, :contact_phone, :status,
                :destination, :method, :decision_score, :decision_explanation,
                :estimated_reimbursement, :qr_code, :drop_off_point_id,
                :requires_kam_approval, :created_by, :processing_time_ms,
                :created_at, :updated_at
            )
        """)

        db.execute(query, {
            "return_id": return_id,
            "trace_id": trace_id,
            "channel": return_data.channel,
            "customer_id": return_data.customer_id,
            "customer_type": return_data.customer_type,
            "order_reference": return_data.order_reference,
            "invoice_reference": return_data.invoice_reference,
            "items": items_data,
            "total_items": total_items,
            "total_value": total_value,
            "total_weight_kg": total_weight,
            "total_volume_m3": total_volume,
            "return_reason": return_data.return_reason,
            "return_reason_description": return_data.return_reason_description,
            "pickup_address": return_data.pickup_address,
            "preferred_drop_off_id": return_data.preferred_drop_off_id,
            "preferred_time_slot": return_data.preferred_time_slot,
            "contact_email": return_data.contact_email,
            "contact_phone": return_data.contact_phone,
            "status": decision.status,
            "destination": decision.destination,
            "method": decision.return_method,
            "decision_score": decision.score,
            "decision_explanation": decision.explanation,
            "estimated_reimbursement": decision.estimated_refund,
            "qr_code": qr_code_data,
            "drop_off_point_id": return_data.preferred_drop_off_id,
            "requires_kam_approval": decision.requires_kam_approval,
            "created_by": current_user.username,
            "processing_time_ms": decision.processing_time_ms,
            "created_at": created_at,
            "updated_at": created_at,
        })
        db.commit()

        logger.info(f"Return {return_id} created by user {current_user.username}")

        return ReturnRequestResponseSchema(
            trace_id=UUID(trace_id),
            return_id=return_id,
            created_at=created_at,
            updated_at=created_at,
            channel=return_data.channel,
            customer_id=return_data.customer_id,
            customer_type=return_data.customer_type,
            order_reference=return_data.order_reference,
            invoice_reference=return_data.invoice_reference,
            items=return_data.items,
            total_items=total_items,
            total_value=total_value,
            total_weight_kg=total_weight,
            total_volume_m3=total_volume,
            return_reason=return_data.return_reason,
            return_reason_description=return_data.return_reason_description,
            status=decision.status,
            destination=decision.destination,
            return_method=decision.return_method,
            decision_score=decision.score,
            decision_explanation=decision.explanation,
            estimated_refund=decision.estimated_refund,
            drop_off_qr_code=qr_code_data,
            requires_kam_approval=decision.requires_kam_approval,
            created_by=current_user.username,
            processing_time_ms=decision.processing_time_ms,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating return: {str(e)}"
        )
    finally:
        db.close()


@router.get("/trace/{trace_id}", response_model=ReturnRequestResponseSchema)
async def get_return_by_trace(
    trace_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, trace_id, channel, customer_id, customer_type,
                   order_reference, invoice_reference, items, total_items,
                   total_value, total_weight_kg, total_volume_m3, return_reason,
                   return_reason_description, contact_email, contact_phone, status,
                   destination, method, decision_score, decision_explanation,
                   estimated_reimbursement, qr_code, drop_off_point_id,
                   requires_kam_approval, created_by, processing_time_ms,
                   created_at, updated_at
            FROM returns
            WHERE trace_id = :trace_id::uuid
        """)

        result = db.execute(query, {"trace_id": trace_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return with trace_id {trace_id} not found"
            )

        return ReturnRequestResponseSchema(
            trace_id=result[1],
            return_id=result[0],
            channel=result[2],
            customer_id=result[3],
            customer_type=result[4],
            order_reference=result[5],
            invoice_reference=result[6],
            items=result[7],
            total_items=result[8],
            total_value=result[9],
            total_weight_kg=result[10],
            total_volume_m3=result[11],
            return_reason=result[12],
            return_reason_description=result[13],
            contact_email=result[14],
            contact_phone=result[15],
            status=result[16],
            destination=result[17],
            return_method=result[18],
            decision_score=result[19],
            decision_explanation=result[20],
            estimated_refund=result[21],
            drop_off_qr_code=result[22],
            drop_off_point_id=result[23],
            requires_kam_approval=result[24],
            created_by=result[25],
            processing_time_ms=result[26],
            created_at=result[27],
            updated_at=result[28],
        )
    finally:
        db.close()


@router.get("/{return_id}", response_model=ReturnRequestResponseSchema)
async def get_return(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, trace_id, channel, customer_id, customer_type,
                   order_reference, invoice_reference, items, total_items,
                   total_value, total_weight_kg, total_volume_m3, return_reason,
                   return_reason_description, pickup_address, preferred_drop_off_id,
                   preferred_time_slot, contact_email, contact_phone, status,
                   destination, method, decision_score, decision_explanation,
                   estimated_reimbursement, qr_code, qr_code_expires_at,
                   drop_off_point_id, scheduled_pickup_at, pickup_address_json,
                   pickup_carrier, tracking_number, kam_approval_reference,
                   kam_approver_id, kam_approval_at, kam_comments,
                   requires_kam_approval, is_approved, rejection_reason,
                   metadata, batch_id, created_by, prompt_version,
                   model_version, processing_time_ms, created_at, updated_at
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found"
            )

        return ReturnRequestResponseSchema(
            trace_id=result[1],
            return_id=result[0],
            channel=result[2],
            customer_id=result[3],
            customer_type=result[4],
            order_reference=result[5],
            invoice_reference=result[6],
            items=result[7],
            total_items=result[8],
            total_value=result[9],
            total_weight_kg=result[10],
            total_volume_m3=result[11],
            return_reason=result[12],
            return_reason_description=result[13],
            preferred_drop_off_id=result[15],
            preferred_time_slot=result[16],
            contact_email=result[17],
            contact_phone=result[18],
            status=result[19],
            destination=result[20],
            return_method=result[21],
            decision_score=result[22],
            decision_explanation=result[23],
            estimated_refund=result[24],
            drop_off_qr_code=result[25],
            drop_off_point_id=result[27],
            scheduled_pickup_at=result[28],
            pickup_address=result[29],
            tracking_number=result[31],
            requires_kam_approval=result[34],
            kam_approver_id=result[36],
            kam_approval_at=result[37],
            kam_comments=result[38],
            created_by=result[42],
            processing_time_ms=result[44],
            created_at=result[45],
            updated_at=result[46],
        )
    finally:
        db.close()


@router.get("", response_model=ReturnsListResponseSchema)
async def list_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    channel: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    destination: Optional[str] = None,
    customer_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        offset = (page - 1) * page_size

        where_clauses = []
        params = {}

        if channel:
            where_clauses.append("channel = :channel")
            params["channel"] = channel
        if status_filter:
            where_clauses.append("status = :status")
            params["status"] = status_filter
        if destination:
            where_clauses.append("destination = :destination")
            params["destination"] = destination
        if customer_id:
            where_clauses.append("customer_id = :customer_id")
            params["customer_id"] = customer_id
        if date_from:
            where_clauses.append("created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            where_clauses.append("created_at <= :date_to")
            params["date_to"] = date_to

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        order_direction = "DESC" if sort_order == "desc" else "ASC"
        allowed_sort_fields = ["created_at", "status", "destination", "total_value"]
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        count_query = text(f"SELECT COUNT(*) FROM returns WHERE {where_sql}")
        total = db.execute(count_query, params).scalar()

        select_query = text(f"""
            SELECT return_id, trace_id, channel, customer_id, customer_type,
                   order_reference, invoice_reference, items, total_items,
                   total_value, total_weight_kg, total_volume_m3, return_reason,
                   return_reason_description, contact_email, contact_phone, status,
                   destination, method, decision_score, decision_explanation,
                   estimated_reimbursement, qr_code, drop_off_point_id,
                   requires_kam_approval, created_by, processing_time_ms,
                   created_at, updated_at
            FROM returns
            WHERE {where_sql}
            ORDER BY {sort_by} {order_direction}
            LIMIT :limit OFFSET :offset
        """)

        params["limit"] = page_size
        params["offset"] = offset

        results = db.execute(select_query, params).fetchall()

        items = []
        for row in results:
            items.append(ReturnRequestResponseSchema(
                trace_id=row[1],
                return_id=row[0],
                channel=row[2],
                customer_id=row[3],
                customer_type=row[4],
                order_reference=row[5],
                invoice_reference=row[6],
                items=row[7],
                total_items=row[8],
                total_value=row[9],
                total_weight_kg=row[10],
                total_volume_m3=row[11],
                return_reason=row[12],
                return_reason_description=row[13],
                contact_email=row[14],
                contact_phone=row[15],
                status=row[16],
                destination=row[17],
                return_method=row[18],
                decision_score=row[19],
                decision_explanation=row[20],
                estimated_refund=row[21],
                drop_off_qr_code=row[22],
                drop_off_point_id=row[23],
                requires_kam_approval=row[24],
                created_by=row[25],
                processing_time_ms=row[26],
                created_at=row[27],
                updated_at=row[28],
            ))

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return ReturnsListResponseSchema(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    finally:
        db.close()


@router.post("/evaluate", response_model=DecisionResultSchema)
async def evaluate_return(
    decision_input: DecisionInputSchema,
    current_user: UserSchema = Depends(get_current_active_user),
):
    start_time = time.time()

    items_data = [item_to_dict(item) for item in decision_input.items]

    decision = decision_engine.evaluate(
        channel=decision_input.channel,
        customer_type=decision_input.customer_type,
        items=items_data,
        total_items=decision_input.item_count,
        total_value=decision_input.total_value,
        total_weight_kg=decision_input.total_weight_kg,
        total_volume_m3=decision_input.total_volume_m3,
        return_reason=decision_input.return_reason,
        has_kam_approval=decision_input.has_kam_approval,
    )

    processing_time = int((time.time() - start_time) * 1000)

    return DecisionResultSchema(
        destination=decision.destination,
        return_method=decision.return_method,
        score=decision.score,
        confidence=decision.confidence,
        explanation=decision.explanation,
        factors=decision.factors,
        business_rule_applied=decision.business_rule_applied,
        requires_kam_approval=decision.requires_kam_approval,
        processing_time_ms=processing_time,
    )


@router.put("/{return_id}", response_model=ReturnRequestResponseSchema)
async def update_return(
    return_id: str,
    return_data: dict,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("SELECT return_id FROM returns WHERE return_id = :return_id")
        existing = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found"
            )

        update_fields = []
        params = {"return_id": return_id, "updated_at": datetime.utcnow()}

        allowed_fields = [
            "status", "destination", "method", "estimated_reimbursement",
            "qr_code", "drop_off_point_id", "scheduled_pickup_at",
            "pickup_carrier", "tracking_number", "kam_comments",
            "is_approved", "rejection_reason", "metadata"
        ]

        for field in allowed_fields:
            if field in return_data:
                update_fields.append(f"{field} = :{field}")
                params[field] = return_data[field]

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )

        update_fields.append("updated_at = :updated_at")

        update_query = text(f"""
            UPDATE returns
            SET {', '.join(update_fields)}
            WHERE return_id = :return_id
        """)

        db.execute(update_query, params)
        db.commit()

        logger.info(f"Return {return_id} updated by user {current_user.username}")

        return await get_return(return_id, current_user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating return: {str(e)}"
        )
    finally:
        db.close()


@router.delete("/{return_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_return(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar devoluciones"
        )

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("SELECT return_id FROM returns WHERE return_id = :return_id")
        existing = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found"
            )

        delete_query = text("DELETE FROM returns WHERE return_id = :return_id")
        db.execute(delete_query, {"return_id": return_id})
        db.commit()

        logger.info(f"Return {return_id} deleted by user {current_user.username}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting return: {str(e)}"
        )
    finally:
        db.close()


@router.post("/{return_id}/acknowledge", response_model=dict)
async def acknowledge_return(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("""
            SELECT return_id, status, channel, customer_id
            FROM returns WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found"
            )

        update_query = text("""
            UPDATE returns
            SET status = 'ENTREGADO',
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)

        db.execute(update_query, {
            "return_id": return_id,
            "updated_at": datetime.utcnow(),
        })

        tracking_query = text("""
            INSERT INTO return_tracking (
                tracking_id, return_id, status, location,
                description, created_at
            ) VALUES (
                :tracking_id, :return_id, :status, :location,
                :description, :created_at
            )
        """)

        tracking_id = f"TRK-{datetime.utcnow().year}-{str(uuid4())[:8].upper()}"
        db.execute(tracking_query, {
            "tracking_id": tracking_id,
            "return_id": return_id,
            "status": "ENTREGADO",
            "location": "CENTRO_LOGISTICO",
            "description": f"Devolucion reconocida por {current_user.username}",
            "created_at": datetime.utcnow(),
        })

        db.commit()

        logger.info(f"Return {return_id} acknowledged by user {current_user.username}")

        return {
            "return_id": return_id,
            "status": "ENTREGADO",
            "acknowledged_by": current_user.username,
            "acknowledged_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error acknowledging return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error acknowledging return: {str(e)}"
        )
    finally:
        db.close()


@router.post("/{return_id}/evaluate", response_model=DecisionResultSchema)
async def re_evaluate_return(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, channel, customer_id, customer_type,
                   items, total_items, total_value, total_weight_kg,
                   total_volume_m3, return_reason, status
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found"
            )

        items_data = result[4] if isinstance(result[4], list) else []

        decision = decision_engine.evaluate(
            channel=result[1],
            customer_type=result[3],
            items=items_data,
            total_items=result[5],
            total_value=Decimal(str(result[6])) if result[6] else Decimal("0"),
            total_weight_kg=Decimal(str(result[7])) if result[7] else Decimal("0"),
            total_volume_m3=Decimal(str(result[8])) if result[8] else Decimal("0"),
            return_reason=result[9],
        )

        update_query = text("""
            UPDATE returns
            SET status = :status,
                destination = :destination,
                method = :method,
                decision_score = :decision_score,
                decision_explanation = :decision_explanation,
                processing_time_ms = :processing_time_ms,
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)

        db.execute(update_query, {
            "status": decision.status,
            "destination": decision.destination,
            "method": decision.return_method,
            "decision_score": decision.score,
            "decision_explanation": decision.explanation,
            "processing_time_ms": decision.processing_time_ms,
            "updated_at": datetime.utcnow(),
            "return_id": return_id,
        })

        db.commit()

        logger.info(f"Return {return_id} re-evaluated by user {current_user.username}")

        return DecisionResultSchema(
            destination=decision.destination,
            return_method=decision.return_method,
            score=decision.score,
            confidence=decision.confidence,
            explanation=decision.explanation,
            factors=decision.factors,
            business_rule_applied=decision.business_rule_applied,
            requires_kam_approval=decision.requires_kam_approval,
            processing_time_ms=decision.processing_time_ms,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error re-evaluating return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error re-evaluating return: {str(e)}"
        )
    finally:
        db.close()


@router.get("/{return_id}/tracking")
async def get_return_tracking(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("SELECT return_id FROM returns WHERE return_id = :return_id")
        existing = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Return {return_id} not found"
            )

        tracking_query = text("""
            SELECT tracking_id, return_id, status, location,
                   description, created_at
            FROM return_tracking
            WHERE return_id = :return_id
            ORDER BY created_at ASC
        """)

        results = db.execute(tracking_query, {"return_id": return_id}).fetchall()

        events = []
        for row in results:
            events.append({
                "tracking_id": row[0],
                "return_id": row[1],
                "status": row[2],
                "location": row[3],
                "description": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
            })

        return {
            "return_id": return_id,
            "events": events,
            "total_events": len(events),
        }
    finally:
        db.close()
