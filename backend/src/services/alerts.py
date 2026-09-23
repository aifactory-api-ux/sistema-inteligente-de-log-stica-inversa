# backend/src/services/alerts.py

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


class AlertService:

    def create_alert(
        self,
        alert_id: str,
        alert_type: str,
        priority: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO alerts (alert_id, type, priority, message, metadata, created_at)
                VALUES (:alert_id, :alert_type, :priority, :message, :metadata, :created_at)
                RETURNING id, alert_id, type, priority, message, metadata, created_at
            """)
            result = db.execute(query, {
                "alert_id": alert_id,
                "alert_type": alert_type,
                "priority": priority,
                "message": message,
                "metadata": str(metadata) if metadata else None,
                "created_at": datetime.utcnow(),
            }).fetchone()
            db.commit()
            return {
                "id": str(result[0]),
                "alert_id": result[1],
                "type": result[2],
                "priority": result[3],
                "message": result[4],
                "metadata": result[5],
                "created_at": result[6].isoformat() if result[6] else None,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
        finally:
            db.close()

    def get_alerts(
        self,
        acknowledged: Optional[bool] = None,
        priority: Optional[str] = None,
        alert_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = """
                SELECT id, alert_id, type, priority, message, acknowledged,
                       acknowledged_by, acknowledged_at, metadata, created_at
                FROM alerts
                WHERE 1=1
            """
            params = {}
            if acknowledged is not None:
                query += " AND acknowledged = :acknowledged"
                params["acknowledged"] = acknowledged
            if priority:
                query += " AND priority = :priority"
                params["priority"] = priority
            if alert_type:
                query += " AND type = :alert_type"
                params["alert_type"] = alert_type
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            results = db.execute(text(query), params).fetchall()
            alerts = []
            for row in results:
                alerts.append({
                    "id": str(row[0]),
                    "alert_id": row[1],
                    "type": row[2],
                    "priority": row[3],
                    "message": row[4],
                    "acknowledged": row[5],
                    "acknowledged_by": row[6],
                    "acknowledged_at": row[7].isoformat() if row[7] else None,
                    "metadata": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                })
            return alerts
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            raise
        finally:
            db.close()

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> dict:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                UPDATE alerts
                SET acknowledged = true, acknowledged_by = :acknowledged_by,
                    acknowledged_at = :acknowledged_at
                WHERE alert_id = :alert_id
                RETURNING id, alert_id, type, priority, message, acknowledged,
                          acknowledged_by, acknowledged_at, metadata, created_at
            """)
            result = db.execute(query, {
                "alert_id": alert_id,
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": datetime.utcnow(),
            }).fetchone()
            db.commit()
            if not result:
                raise ValueError(f"Alert not found: {alert_id}")
            return {
                "id": str(result[0]),
                "alert_id": result[1],
                "type": result[2],
                "priority": result[3],
                "message": result[4],
                "acknowledged": result[5],
                "acknowledged_by": result[6],
                "acknowledged_at": result[7].isoformat() if result[7] else None,
                "metadata": result[8],
                "created_at": result[9].isoformat() if result[9] else None,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error acknowledging alert: {e}")
            raise
        finally:
            db.close()

    def get_unacknowledged_count(self) -> int:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("SELECT COUNT(*) FROM alerts WHERE acknowledged = false")
            count = db.execute(query).scalar() or 0
            return int(count)
        finally:
            db.close()

    def check_inspection_saturation(self, threshold: int = 50) -> Optional[dict]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                SELECT COUNT(*) FROM returns
                WHERE status = 'INSPECCION'
            """)
            count = db.execute(query).scalar() or 0
            if count >= threshold:
                alert_query = text("""
                    SELECT alert_id FROM alerts
                    WHERE type = 'INSPECTION_SATURATION'
                    AND acknowledged = false
                    AND created_at >= :since
                """)
                since = datetime.utcnow() - timedelta(hours=1)
                existing = db.execute(alert_query, {"since": since}).fetchone()
                if not existing:
                    return {
                        "type": "INSPECTION_SATURATION",
                        "priority": "HIGH" if count >= threshold else "MEDIUM",
                        "message": f"Cola de inspeccion ha alcanzado {count} solicitudes (umbral: {threshold})",
                        "metadata": {"current_count": count, "threshold": threshold},
                    }
            return None
        finally:
            db.close()

    def check_kam_pending_alert(self, threshold: int = 10) -> Optional[dict]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                SELECT COUNT(*) FROM returns
                WHERE status = 'EXCEPTION' AND requires_kam_approval = true
            """)
            count = db.execute(query).scalar() or 0
            if count >= threshold:
                alert_query = text("""
                    SELECT alert_id FROM alerts
                    WHERE type = 'B2B_APPROVAL_PENDING'
                    AND acknowledged = false
                    AND created_at >= :since
                """)
                since = datetime.utcnow() - timedelta(hours=1)
                existing = db.execute(alert_query, {"since": since}).fetchone()
                if not existing:
                    return {
                        "type": "B2B_APPROVAL_PENDING",
                        "priority": "HIGH",
                        "message": f"{count} solicitudes B2B pendientes de aprobacion KAM (umbral: {threshold})",
                        "metadata": {"current_count": count, "threshold": threshold},
                    }
            return None
        finally:
            db.close()

    def check_return_rate_spike(self, threshold_pct: float = 15.0) -> Optional[dict]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            query = text("""
                SELECT COUNT(*) FROM returns
                WHERE created_at >= :today_start
            """)
            count = db.execute(query, {"today_start": today_start}).scalar() or 0
            avg_daily = count / 1.0
            if avg_daily > threshold_pct:
                alert_query = text("""
                    SELECT alert_id FROM alerts
                    WHERE type = 'RETURN_RATE_SPIKE'
                    AND acknowledged = false
                    AND created_at >= :since
                """)
                since = datetime.utcnow() - timedelta(hours=1)
                existing = db.execute(alert_query, {"since": since}).fetchone()
                if not existing:
                    return {
                        "type": "RETURN_RATE_SPIKE",
                        "priority": "CRITICAL",
                        "message": f"Tasa de devolucion ha superado el {threshold_pct}%",
                        "metadata": {"current_rate": avg_daily, "threshold": threshold_pct},
                    }
            return None
        finally:
            db.close()

    def delete_old_alerts(self, days: int = 30) -> int:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = text("DELETE FROM alerts WHERE created_at < :cutoff AND acknowledged = true")
            result = db.execute(query, {"cutoff": cutoff})
            db.commit()
            return result.rowcount
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting old alerts: {e}")
            raise
        finally:
            db.close()


alert_service = AlertService()
