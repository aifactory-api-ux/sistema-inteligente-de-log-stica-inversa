# backend/src/routers/kam.py

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.schemas import (
    UserSchema,
    KAMApprovalSchema,
    KAMApprovalResponseSchema,
)
from src.routers.auth import get_current_active_user
from src.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kam", tags=["kam"])


def require_kam_role(current_user: UserSchema) -> UserSchema:
    if current_user.role not in ["KAM", "ADMIN"]:
        logger.warning(
            f"User {current_user.username} with role {current_user.role} "
            f"attempted to access KAM-protected endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol KAM o ADMIN para esta accion"
        )
    return current_user


@router.post("/approve/{return_id}", response_model=KAMApprovalResponseSchema)
async def approve_return(
    return_id: str,
    approval_data: KAMApprovalSchema,
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        query = text("""
            SELECT return_id, channel, customer_id, customer_type,
                   items, total_items, total_value, total_weight_kg,
                   total_volume_m3, return_reason, status, destination,
                   method, requires_kam_approval, is_approved,
                   batch_id, created_by
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        if result[13] is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La devolucion {return_id} no requiere aprobacion KAM"
            )

        if result[14] is True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La devolucion {return_id} ya fue aprobada"
            )

        items_data = result[4] if isinstance(result[4], list) else []
        total_items = result[5]
        total_value = Decimal(str(result[6])) if result[6] else Decimal("0")
        total_weight_kg = Decimal(str(result[7])) if result[7] else Decimal("0")
        total_volume_m3 = Decimal(str(result[8])) if result[8] else Decimal("0")

        decision = decision_engine.evaluate(
            channel=result[1],
            customer_type=result[3],
            items=items_data,
            total_items=total_items,
            total_value=total_value,
            total_weight_kg=total_weight_kg,
            total_volume_m3=total_volume_m3,
            return_reason=result[9],
            has_kam_approval=True,
            is_batch=result[15] is not None,
            batch_id=result[15],
        )

        approved_at = datetime.utcnow()

        update_query = text("""
            UPDATE returns
            SET status = :status,
                destination = :destination,
                method = :method,
                is_approved = :is_approved,
                kam_approved_by = :kam_approved_by,
                kam_approval_at = :kam_approval_at,
                kam_comments = :kam_comments,
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)

        db.execute(update_query, {
            "status": decision.status,
            "destination": decision.destination,
            "method": decision.return_method,
            "is_approved": True,
            "kam_approved_by": current_user.username,
            "kam_approval_at": approved_at,
            "kam_comments": approval_data.kam_comments,
            "updated_at": approved_at,
            "return_id": return_id,
        })

        if decision.return_method == "PICKUP":
            alert_query = text("""
                INSERT INTO alerts (
                    alert_id, type, priority, message,
                    metadata, created_at
                ) VALUES (
                    :alert_id, :type, :priority, :message,
                    :metadata, :created_at
                )
            """)

            alert_id = f"ALT-{datetime.utcnow().year}-{str(uuid4())[:8].upper()}"
            db.execute(alert_query, {
                "alert_id": alert_id,
                "type": "B2B_APPROVAL_PENDING",
                "priority": "LOW",
                "message": f"Lote B2B {return_id} aprobado por KAM {current_user.username}. Pickup programado.",
                "metadata": {"return_id": return_id, "approved_by": current_user.username},
                "created_at": approved_at,
            })

        db.commit()

        logger.info(
            f"Return {return_id} approved by KAM {current_user.username}. "
            f"Destination: {decision.destination}, Method: {decision.return_method}"
        )

        return KAMApprovalResponseSchema(
            return_id=return_id,
            status=decision.status,
            destination=decision.destination,
            return_method=decision.return_method,
            kam_approved_by=current_user.username,
            kam_approved_at=approved_at,
            message=f"Devolucion {return_id} aprobada exitosamente.pickup programado para recogida."
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aprobar la devolucion: {str(e)}"
        )
    finally:
        db.close()


@router.get("/pending", response_model=list)
async def list_pending_approvals(
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        query = text("""
            SELECT return_id, channel, customer_id, customer_type,
                   total_items, total_value, return_reason,
                   status, created_at, created_by
            FROM returns
            WHERE requires_kam_approval = true
              AND is_approved = false
              AND status = 'EXCEPTION'
            ORDER BY created_at ASC
        """)

        results = db.execute(query).fetchall()

        pending = []
        for row in results:
            pending.append({
                "return_id": row[0],
                "channel": row[1],
                "customer_id": row[2],
                "customer_type": row[3],
                "total_items": row[4],
                "total_value": float(row[5]) if row[5] else 0,
                "return_reason": row[6],
                "status": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "created_by": row[9],
            })

        return pending

    finally:
        db.close()


@router.get("/pending-approvals", response_model=list)
async def get_pending_approvals(
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        query = text("""
            SELECT return_id, channel, customer_id, customer_type,
                   total_items, total_value, return_reason,
                   status, created_at, created_by
            FROM returns
            WHERE requires_kam_approval = true
              AND is_approved = false
              AND status = 'EXCEPTION'
            ORDER BY created_at ASC
        """)

        results = db.execute(query).fetchall()

        pending = []
        for row in results:
            pending.append({
                "approval_id": f"APR-{row[0]}",
                "return_id": row[0],
                "channel": row[1],
                "customer_id": row[2],
                "customer_type": row[3],
                "total_items": row[4],
                "total_value": float(row[5]) if row[5] else 0,
                "return_reason": row[6],
                "status": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "created_by": row[9],
            })

        return pending

    finally:
        db.close()


@router.get("/approval-history", response_model=list)
async def get_approval_history(
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        query = text("""
            SELECT return_id, channel, customer_id, customer_type,
                   total_items, total_value, return_reason,
                   status, kam_approved_by, kam_approval_at, kam_comments,
                   created_at
            FROM returns
            WHERE is_approved = true
              AND kam_approval_at IS NOT NULL
            ORDER BY kam_approval_at DESC
            LIMIT 100
        """)

        results = db.execute(query).fetchall()

        history = []
        for row in results:
            history.append({
                "return_id": row[0],
                "channel": row[1],
                "customer_id": row[2],
                "customer_type": row[3],
                "total_items": row[4],
                "total_value": float(row[5]) if row[5] else 0,
                "return_reason": row[6],
                "status": row[7],
                "approved_by": row[8],
                "approved_at": row[9].isoformat() if row[9] else None,
                "comments": row[10],
                "created_at": row[11].isoformat() if row[11] else None,
            })

        return history

    finally:
        db.close()


@router.post("/approvals", response_model=dict)
async def create_approval_request(
    return_id: str,
    comments: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        check_query = text("""
            SELECT return_id, status, requires_kam_approval
            FROM returns
            WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        approval_id = f"APR-{return_id}"

        return {
            "approval_id": approval_id,
            "return_id": return_id,
            "status": "PENDING",
            "requested_by": current_user.username,
            "requested_at": datetime.utcnow().isoformat(),
            "comments": comments,
        }

    finally:
        db.close()


@router.post("/approvals/{approval_id}", response_model=dict)
async def process_approval(
    approval_id: str,
    action: str,
    comments: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    if action not in ["APPROVE", "REJECT"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accion debe ser APPROVE o REJECT"
        )

    return_id = approval_id.replace("APR-", "") if approval_id.startswith("APR-") else approval_id

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        check_query = text("""
            SELECT return_id, status, requires_kam_approval, is_approved
            FROM returns
            WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        if action == "APPROVE":
            update_query = text("""
                UPDATE returns
                SET is_approved = true,
                    kam_approved_by = :kam_approved_by,
                    kam_approval_at = :kam_approval_at,
                    kam_comments = :kam_comments,
                    status = 'APROBADO',
                    updated_at = :updated_at
                WHERE return_id = :return_id
            """)

            db.execute(update_query, {
                "kam_approved_by": current_user.username,
                "kam_approval_at": datetime.utcnow(),
                "kam_comments": comments,
                "updated_at": datetime.utcnow(),
                "return_id": return_id,
            })
            db.commit()

            logger.info(f"Return {return_id} approved via KAM approvals endpoint by {current_user.username}")

            return {
                "approval_id": approval_id,
                "return_id": return_id,
                "action": "APPROVED",
                "processed_by": current_user.username,
                "processed_at": datetime.utcnow().isoformat(),
                "comments": comments,
            }
        else:
            update_query = text("""
                UPDATE returns
                SET is_approved = false,
                    rejection_reason = :rejection_reason,
                    status = 'RECHAZADO',
                    updated_at = :updated_at
                WHERE return_id = :return_id
            """)

            db.execute(update_query, {
                "rejection_reason": comments or "Rechazado por KAM",
                "updated_at": datetime.utcnow(),
                "return_id": return_id,
            })
            db.commit()

            logger.info(f"Return {return_id} rejected via KAM approvals endpoint by {current_user.username}")

            return {
                "approval_id": approval_id,
                "return_id": return_id,
                "action": "REJECTED",
                "processed_by": current_user.username,
                "processed_at": datetime.utcnow().isoformat(),
                "comments": comments,
            }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing approval {approval_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar aprobacion: {str(e)}"
        )
    finally:
        db.close()


@router.post("/rejections/{approval_id}", response_model=dict)
async def reject_approval(
    approval_id: str,
    rejection_reason: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_kam_role(current_user)

    return_id = approval_id.replace("APR-", "") if approval_id.startswith("APR-") else approval_id

    from src.db.database import SessionLocal
    db = SessionLocal()

    try:
        check_query = text("""
            SELECT return_id, status, requires_kam_approval
            FROM returns
            WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        update_query = text("""
            UPDATE returns
            SET is_approved = false,
                rejection_reason = :rejection_reason,
                status = 'RECHAZADO',
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)

        db.execute(update_query, {
            "rejection_reason": rejection_reason or "Rechazado por KAM",
            "updated_at": datetime.utcnow(),
            "return_id": return_id,
        })
        db.commit()

        logger.info(f"Return {return_id} rejected via KAM rejections endpoint by {current_user.username}")

        return {
            "approval_id": approval_id,
            "return_id": return_id,
            "status": "REJECTED",
            "rejected_by": current_user.username,
            "rejected_at": datetime.utcnow().isoformat(),
            "rejection_reason": rejection_reason,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting approval {approval_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al rechazar aprobacion: {str(e)}"
        )
    finally:
        db.close()