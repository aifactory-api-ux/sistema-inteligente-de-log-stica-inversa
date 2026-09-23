# backend/src/routers/pickup.py

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.schemas import UserSchema
from src.routers.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pickup", tags=["pickup"])


def generate_pickup_id() -> str:
    year = datetime.utcnow().year
    unique_part = str(uuid4())[:8].upper()
    return f"PCK-{year}-{unique_part}"


@router.get("/slots")
async def get_pickup_slots(
    return_id: Optional[str] = Query(None, description="ID de la devolucion para consultar disponibilidad"),
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["B2C_USER", "B2B_USER", "SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver slots de recogida"
        )

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        if return_id:
            check_query = text("SELECT return_id, method FROM returns WHERE return_id = :return_id")
            result = db.execute(check_query, {"return_id": return_id}).fetchone()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Devolucion {return_id} no encontrada"
                )
            if result[1] != "PICKUP":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Esta devolucion no requiere pickup"
                )

        base_date = datetime.utcnow().date()
        slots = []

        for day_offset in range(1, 8):
            current_date = base_date + timedelta(days=day_offset)

            if current_date.weekday() >= 5:
                continue

            for hour in [9, 10, 11, 14, 15, 16]:
                slot_date = current_date.strftime("%Y-%m-%d")
                slot_id = f"SLOT-{slot_date.replace('-','')}-{hour:02d}00"

                slots.append({
                    "id": slot_id,
                    "date": slot_date,
                    "start_time": f"{hour:02d}:00",
                    "end_time": f"{hour + 1:02d}:00" if hour < 17 else "18:00",
                    "available": True,
                    "capacity": 10,
                    "booked": 0,
                })

        return {
            "slots": slots,
            "total": len(slots),
            "available_count": len([s for s in slots if s["available"]]),
        }
    finally:
        db.close()


@router.post("/schedule")
async def schedule_pickup(
    return_id: str,
    slot_id: str,
    pickup_address: dict,
    special_instructions: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("""
            SELECT return_id, status, method, channel, customer_id
            FROM returns
            WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        if result[2] != "PICKUP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta devolucion no utiliza metodo Pickup"
            )

        if result[1] not in ["APROBADO", "PRE_APROBADO"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La devolucion debe estar aprobada antes de programar pickup"
            )

        pickup_id = generate_pickup_id()
        scheduled_at = datetime.utcnow() + timedelta(hours=24)

        update_query = text("""
            UPDATE returns
            SET pickup_scheduled_at = :scheduled_at,
                pickup_carrier = :carrier,
                status = 'EN_TRANSITO',
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)

        db.execute(update_query, {
            "scheduled_at": scheduled_at,
            "carrier": "LOGISTICA_INVERSA_DEFAULT",
            "updated_at": datetime.utcnow(),
            "return_id": return_id,
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
            "status": "EN_TRANSITO",
            "location": "CENTRO_LOGISTICO",
            "description": f"Pickup programado para {slot_id}. Direccion: {pickup_address.get('street', 'N/A')}",
            "created_at": datetime.utcnow(),
        })

        db.commit()

        logger.info(f"Pickup scheduled for return {return_id} by user {current_user.username}")

        return {
            "pickup_id": pickup_id,
            "return_id": return_id,
            "slot_id": slot_id,
            "scheduled_at": scheduled_at.isoformat(),
            "status": "PROGRAMADO",
            "pickup_address": pickup_address,
            "carrier": "LOGISTICA_INVERSA_DEFAULT",
            "tracking_id": tracking_id,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling pickup for return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al programar pickup: {str(e)}"
        )
    finally:
        db.close()


@router.get("/{return_id}")
async def get_pickup_status(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, status, method, pickup_scheduled_at,
                   pickup_carrier, pickup_address
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        tracking_query = text("""
            SELECT tracking_id, status, location, description, created_at
            FROM return_tracking
            WHERE return_id = :return_id
            ORDER BY created_at DESC
        """)

        tracking_results = db.execute(tracking_query, {"return_id": return_id}).fetchall()

        tracking_events = []
        for row in tracking_results:
            tracking_events.append({
                "tracking_id": row[0],
                "status": row[1],
                "location": row[2],
                "description": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            })

        pickup_address = result[5] if isinstance(result[5], dict) else {}

        return {
            "return_id": result[0],
            "status": result[1],
            "method": result[2],
            "pickup_scheduled_at": result[3].isoformat() if result[3] else None,
            "pickup_carrier": result[4],
            "pickup_address": pickup_address,
            "tracking_events": tracking_events,
        }
    finally:
        db.close()


@router.delete("/{return_id}")
async def cancel_pickup(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para cancelar pickups"
        )

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("""
            SELECT return_id, status, method, pickup_scheduled_at
            FROM returns
            WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        if result[2] != "PICKUP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta devolucion no tiene pickup programado"
            )

        update_query = text("""
            UPDATE returns
            SET pickup_scheduled_at = NULL,
                pickup_carrier = NULL,
                status = 'APROBADO',
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)
        db.execute(update_query, {
            "updated_at": datetime.utcnow(),
            "return_id": return_id,
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
            "status": "CANCELADO",
            "location": "SISTEMA",
            "description": f"Pickup cancelado por {current_user.username}",
            "created_at": datetime.utcnow(),
        })

        db.commit()

        logger.info(f"Pickup cancelled for return {return_id} by user {current_user.username}")

        return {
            "return_id": return_id,
            "status": "CANCELADO",
            "message": "Pickup cancelado exitosamente",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling pickup for return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar pickup: {str(e)}"
        )
    finally:
        db.close()


@router.put("/{return_id}/reschedule")
async def reschedule_pickup(
    return_id: str,
    slot_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        check_query = text("""
            SELECT return_id, status, method, pickup_scheduled_at
            FROM returns
            WHERE return_id = :return_id
        """)
        result = db.execute(check_query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        if result[2] != "PICKUP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta devolucion no tiene pickup programado"
            )

        new_scheduled_at = datetime.utcnow() + timedelta(hours=48)

        update_query = text("""
            UPDATE returns
            SET pickup_scheduled_at = :scheduled_at,
                updated_at = :updated_at
            WHERE return_id = :return_id
        """)

        db.execute(update_query, {
            "scheduled_at": new_scheduled_at,
            "updated_at": datetime.utcnow(),
            "return_id": return_id,
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
            "status": "REPROGRAMADO",
            "location": "SISTEMA",
            "description": f"Pickup reprogramado a slot {slot_id} por {current_user.username}",
            "created_at": datetime.utcnow(),
        })

        db.commit()

        logger.info(f"Pickup rescheduled for return {return_id} by user {current_user.username}")

        return {
            "return_id": return_id,
            "slot_id": slot_id,
            "scheduled_at": new_scheduled_at.isoformat(),
            "status": "REPROGRAMADO",
            "message": "Pickup reprogramado exitosamente",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rescheduling pickup for return {return_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reprogramar pickup: {str(e)}"
        )
    finally:
        db.close()
