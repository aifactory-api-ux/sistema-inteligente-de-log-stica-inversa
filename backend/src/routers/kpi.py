# backend/src/routers/kpi.py

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.schemas import (
    KPIDashboardResponseSchema,
    DestinationDistributionResponseSchema,
    UserSchema,
)
from src.routers.auth import get_current_active_user
from src.services.kpi_service import kpi_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/dashboard", response_model=KPIDashboardResponseSchema)
async def get_kpi_dashboard(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder al panel de control"
        )

    try:
        dashboard_data = kpi_service.get_kpi_dashboard()

        return KPIDashboardResponseSchema(
            return_rate=dashboard_data["return_rate"],
            return_rate_delta=dashboard_data["return_rate_delta"],
            avg_cycle_time_hours=dashboard_data["avg_cycle_time_hours"],
            avg_cycle_time_delta=dashboard_data["avg_cycle_time_delta"],
            avg_recovery_cost=dashboard_data["avg_recovery_cost"],
            avg_recovery_cost_delta=dashboard_data["avg_recovery_cost_delta"],
            value_recovery_rate=dashboard_data["value_recovery_rate"],
            value_recovery_rate_delta=dashboard_data["value_recovery_rate_delta"],
            total_returns_today=dashboard_data["total_returns_today"],
            total_returns_today_delta=dashboard_data["total_returns_today_delta"],
            inspection_queue_size=dashboard_data["inspection_queue_size"],
            pickup_pending_count=dashboard_data["pickup_pending_count"],
            kam_pending_count=dashboard_data["kam_pending_count"],
            last_updated=dashboard_data["last_updated"],
        )
    except Exception as e:
        logger.error(f"Error fetching KPI dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el panel de KPIs: {str(e)}"
        )


@router.get("/destinations", response_model=DestinationDistributionResponseSchema)
async def get_destination_distribution(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a la distribucion de destinos"
        )

    try:
        distribution = kpi_service.get_destination_distribution()

        return DestinationDistributionResponseSchema(
            CARRIL_RAPIDO=distribution.get("CARRIL_RAPIDO", 0),
            OUTLET=distribution.get("OUTLET", 0),
            RECICLAJE=distribution.get("RECICLAJE", 0),
            KEEP_IT=distribution.get("KEEP_IT", 0),
            INSPECCION_B2B=distribution.get("INSPECCION_B2B", 0),
            total=distribution.get("total", 0),
        )
    except Exception as e:
        logger.error(f"Error fetching destination distribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la distribucion de destinos: {str(e)}"
        )


@router.get("/history", response_model=list[dict])
async def get_kpi_history(
    days: int = Query(30, ge=1, le=365),
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder al historial de KPIs"
        )

    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as return_count,
                AVG(estimated_reimbursement) as avg_cost,
                COUNT(CASE WHEN destination IN ('CARRIL_RAPIDO', 'OUTLET')
                    THEN 1 END) as recovered_count
            FROM returns
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)

        results = db.execute(query, {"days": days}).fetchall()

        history = []
        for row in results:
            history.append({
                "date": row[0].isoformat() if row[0] else None,
                "return_count": row[1] or 0,
                "avg_cost": float(row[2]) if row[2] else 0.0,
                "recovered_count": row[3] or 0,
            })

        return history
    except Exception as e:
        logger.error(f"Error fetching KPI history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el historial de KPIs: {str(e)}"
        )
    finally:
        db.close()