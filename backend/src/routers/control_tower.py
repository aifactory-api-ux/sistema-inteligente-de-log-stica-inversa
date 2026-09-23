# backend/src/routers/control_tower.py

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.schemas import (
    AlertSchema,
    AlertsListResponseSchema,
    UserSchema,
)
from src.routers.auth import get_current_active_user
from src.services.alerts import alert_service
from src.services.kpi_service import kpi_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/control-tower", tags=["control-tower"])


@router.get("/alerts", response_model=AlertsListResponseSchema)
async def get_alerts(
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a alertas"
        )

    try:
        alerts = alert_service.get_alerts(
            acknowledged=acknowledged,
            priority=priority,
            alert_type=alert_type,
            limit=limit,
            offset=offset,
        )

        alert_schemas = []
        for alert in alerts:
            alert_schemas.append(AlertSchema(
                alert_id=alert["alert_id"],
                type=alert["type"],
                priority=alert["priority"],
                message=alert["message"],
                acknowledged=alert["acknowledged"],
                acknowledged_by=alert.get("acknowledged_by"),
                acknowledged_at=alert.get("acknowledged_at"),
                metadata=alert.get("metadata"),
                created_at=alert["created_at"],
            ))

        return AlertsListResponseSchema(
            alerts=alert_schemas,
            total=len(alert_schemas),
        )
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener alertas: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertSchema)
async def acknowledge_alert(
    alert_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para reconocer alertas"
        )

    try:
        alert = alert_service.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=current_user.username,
        )

        return AlertSchema(
            alert_id=alert["alert_id"],
            type=alert["type"],
            priority=alert["priority"],
            message=alert["message"],
            acknowledged=alert["acknowledged"],
            acknowledged_by=alert.get("acknowledged_by"),
            acknowledged_at=alert.get("acknowledged_at"),
            metadata=alert.get("metadata"),
            created_at=alert["created_at"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reconocer alerta: {str(e)}"
        )


@router.get("/distribution")
async def get_distribution(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a la distribucion"
        )

    try:
        distribution = kpi_service.get_destination_distribution()
        return distribution
    except Exception as e:
        logger.error(f"Error fetching distribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la distribucion: {str(e)}"
        )


@router.get("/kpis")
async def get_kpis(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a los KPIs"
        )

    try:
        kpis = kpi_service.get_kpi_dashboard()
        return kpis
    except Exception as e:
        logger.error(f"Error fetching KPIs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener KPIs: {str(e)}"
        )


@router.get("/realtime")
async def get_realtime(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a datos en tiempo real"
        )

    try:
        from src.db.database import SessionLocal
        db = SessionLocal()

        query = text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'PENDIENTE') as pending_count,
                COUNT(*) FILTER (WHERE status = 'EN_TRANSITO') as in_transit_count,
                COUNT(*) FILTER (WHERE status = 'INSPECCION') as inspection_count,
                COUNT(*) FILTER (WHERE status = 'PROCESADO') as processed_count,
                COUNT(*) FILTER (WHERE status = 'EXCEPTION') as exception_count,
                COUNT(*) FILTER (WHERE acknowledged = false) as unread_alerts
            FROM (
                SELECT status FROM returns
                UNION ALL
                SELECT 'ALERT' as status FROM alerts WHERE acknowledged = false
            ) combined
        """)

        result = db.execute(query).fetchone()
        db.close()

        return {
            "pending": result[0] if result[0] else 0,
            "in_transit": result[1] if result[1] else 0,
            "inspection": result[2] if result[2] else 0,
            "processed": result[3] if result[3] else 0,
            "exceptions": result[4] if result[4] else 0,
            "unread_alerts": result[5] if result[5] else 0,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching realtime data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener datos en tiempo real: {str(e)}"
        )


@router.get("/returns")
async def get_control_tower_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a los returns"
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
        if channel:
            where_clauses.append("channel = :channel")
            params["channel"] = channel

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_query = text(f"SELECT COUNT(*) FROM returns WHERE {where_sql}")
        total = db.execute(count_query, params).scalar()

        select_query = text(f"""
            SELECT return_id, trace_id, channel, customer_id, customer_type,
                   status, destination, method, total_items, total_value,
                   created_at, updated_at
            FROM returns
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params["limit"] = page_size
        params["offset"] = offset

        results = db.execute(select_query, params).fetchall()

        items = []
        for row in results:
            items.append({
                "return_id": row[0],
                "trace_id": str(row[1]),
                "channel": row[2],
                "customer_id": row[3],
                "customer_type": row[4],
                "status": row[5],
                "destination": row[6],
                "method": row[7],
                "total_items": row[8],
                "total_value": float(row[9]) if row[9] else 0,
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
            })

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    except Exception as e:
        logger.error(f"Error fetching control tower returns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener returns: {str(e)}"
        )
    finally:
        db.close()