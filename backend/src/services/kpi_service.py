# backend/src/services/kpi_service.py

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


class KPIService:

    def calculate_return_rate(self, days: int = 30) -> tuple[float, float]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            period_start = today_start - timedelta(days=days)
            prev_period_start = period_start - timedelta(days=days)

            current_query = text("""
                SELECT COUNT(*) FROM returns
                WHERE created_at >= :period_start AND created_at < :today_start
            """)
            prev_query = text("""
                SELECT COUNT(*) FROM returns
                WHERE created_at >= :prev_start AND created_at < :period_start
            """)

            current_count = db.execute(current_query, {
                "period_start": period_start,
                "today_start": today_start
            }).scalar() or 0

            prev_count = db.execute(prev_query, {
                "prev_start": prev_period_start,
                "period_start": period_start
            }).scalar() or 0

            current_rate = (current_count / days) * 100 if days > 0 else 0
            prev_rate = (prev_count / days) * 100 if days > 0 else 0
            delta = current_rate - prev_rate

            return round(current_rate, 2), round(delta, 2)
        finally:
            db.close()

    def calculate_avg_cycle_time_hours(self, days: int = 7) -> tuple[float, float]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            period_start = today_start - timedelta(days=days)
            prev_period_start = period_start - timedelta(days=days)

            current_query = text("""
                SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 3600)
                FROM returns
                WHERE created_at >= :period_start
                AND updated_at IS NOT NULL
                AND status IN ('PROCESADO', 'ENTREGADO')
            """)
            prev_query = text("""
                SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 3600)
                FROM returns
                WHERE created_at >= :prev_start AND created_at < :period_start
                AND updated_at IS NOT NULL
                AND status IN ('PROCESADO', 'ENTREGADO')
            """)

            current_avg = db.execute(current_query, {"period_start": period_start}).scalar() or 0
            prev_avg = db.execute(prev_query, {
                "prev_start": prev_period_start,
                "period_start": period_start
            }).scalar() or 0

            current_avg = float(current_avg) if current_avg else 0.0
            prev_avg = float(prev_avg) if prev_avg else 0.0
            delta = current_avg - prev_avg

            return round(current_avg, 2), round(delta, 2)
        finally:
            db.close()

    def calculate_avg_recovery_cost(self, days: int = 7) -> tuple[Decimal, Decimal]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            period_start = today_start - timedelta(days=days)
            prev_period_start = period_start - timedelta(days=days)

            current_query = text("""
                SELECT AVG(estimated_reimbursement)
                FROM returns
                WHERE created_at >= :period_start
                AND status IN ('PROCESADO', 'ENTREGADO')
            """)
            prev_query = text("""
                SELECT AVG(estimated_reimbursement)
                FROM returns
                WHERE created_at >= :prev_start AND created_at < :period_start
                AND status IN ('PROCESADO', 'ENTREGADO')
            """)

            current_avg = db.execute(current_query, {"period_start": period_start}).scalar() or Decimal("0")
            prev_avg = db.execute(prev_query, {
                "prev_start": prev_period_start,
                "period_start": period_start
            }).scalar() or Decimal("0")

            if isinstance(current_avg, float):
                current_avg = Decimal(str(current_avg))
            if isinstance(prev_avg, float):
                prev_avg = Decimal(str(prev_avg))

            delta = current_avg - prev_avg

            return round(current_avg, 2), round(delta, 2)
        finally:
            db.close()

    def calculate_value_recovery_rate(self, days: int = 30) -> tuple[float, float]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            period_start = today_start - timedelta(days=days)
            prev_period_start = period_start - timedelta(days=days)

            current_query = text("""
                SELECT
                    COALESCE(SUM(CASE WHEN destination IN ('CARRIL_RAPIDO', 'OUTLET')
                        THEN estimated_reimbursement ELSE 0 END), 0) as recovered,
                    COALESCE(SUM(estimated_reimbursement), 0) as total
                FROM returns
                WHERE created_at >= :period_start
            """)
            prev_query = text("""
                SELECT
                    COALESCE(SUM(CASE WHEN destination IN ('CARRIL_RAPIDO', 'OUTLET')
                        THEN estimated_reimbursement ELSE 0 END), 0) as recovered,
                    COALESCE(SUM(estimated_reimbursement), 0) as total
                FROM returns
                WHERE created_at >= :prev_start AND created_at < :period_start
            """)

            current_result = db.execute(current_query, {"period_start": period_start}).fetchone()
            prev_result = db.execute(prev_query, {
                "prev_start": prev_period_start,
                "period_start": period_start
            }).fetchone()

            current_recovered = float(current_result[0]) if current_result[0] else 0.0
            current_total = float(current_result[1]) if current_result[1] else 0.0
            prev_recovered = float(prev_result[0]) if prev_result[0] else 0.0
            prev_total = float(prev_result[1]) if prev_result[1] else 0.0

            current_rate = (current_recovered / current_total * 100) if current_total > 0 else 0.0
            prev_rate = (prev_recovered / prev_total * 100) if prev_total > 0 else 0.0
            delta = current_rate - prev_rate

            return round(current_rate, 2), round(delta, 2)
        finally:
            db.close()

    def get_total_returns_today(self) -> tuple[int, int]:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)

            current_query = text("""
                SELECT COUNT(*) FROM returns
                WHERE created_at >= :today_start
            """)
            prev_query = text("""
                SELECT COUNT(*) FROM returns
                WHERE created_at >= :yesterday_start AND created_at < :today_start
            """)

            current_count = db.execute(current_query, {"today_start": today_start}).scalar() or 0
            prev_count = db.execute(prev_query, {
                "yesterday_start": yesterday_start,
                "today_start": today_start
            }).scalar() or 0

            delta = current_count - prev_count

            return int(current_count), int(delta)
        finally:
            db.close()

    def get_inspection_queue_size(self) -> int:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                SELECT COUNT(*) FROM returns
                WHERE status = 'INSPECCION'
            """)
            count = db.execute(query).scalar() or 0
            return int(count)
        finally:
            db.close()

    def get_pickup_pending_count(self) -> int:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                SELECT COUNT(*) FROM returns
                WHERE status = 'APROBADO' AND method = 'PICKUP'
                AND pickup_scheduled_at IS NULL
            """)
            count = db.execute(query).scalar() or 0
            return int(count)
        finally:
            db.close()

    def get_kam_pending_count(self) -> int:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                SELECT COUNT(*) FROM returns
                WHERE status = 'EXCEPTION' AND requires_kam_approval = true
            """)
            count = db.execute(query).scalar() or 0
            return int(count)
        finally:
            db.close()

    def get_destination_distribution(self) -> dict:
        from src.db.database import SessionLocal
        db = SessionLocal()
        try:
            query = text("""
                SELECT destination, COUNT(*) as count
                FROM returns
                WHERE destination IS NOT NULL
                GROUP BY destination
            """)
            results = db.execute(query).fetchall()

            distribution = {
                "CARRIL_RAPIDO": 0,
                "OUTLET": 0,
                "RECICLAJE": 0,
                "KEEP_IT": 0,
                "INSPECCION_B2B": 0,
            }

            for row in results:
                dest = row[0]
                count = row[1]
                if dest in distribution:
                    distribution[dest] = int(count)

            total = sum(distribution.values())
            return {**distribution, "total": total}
        finally:
            db.close()

    def get_kpi_dashboard(self) -> dict:
        return_rate, return_rate_delta = self.calculate_return_rate()
        avg_cycle_time, avg_cycle_time_delta = self.calculate_avg_cycle_time_hours()
        avg_recovery_cost, avg_recovery_cost_delta = self.calculate_avg_recovery_cost()
        value_recovery_rate, value_recovery_rate_delta = self.calculate_value_recovery_rate()
        total_returns_today, total_returns_today_delta = self.get_total_returns_today()
        inspection_queue_size = self.get_inspection_queue_size()
        pickup_pending_count = self.get_pickup_pending_count()
        kam_pending_count = self.get_kam_pending_count()

        return {
            "return_rate": return_rate,
            "return_rate_delta": return_rate_delta,
            "avg_cycle_time_hours": avg_cycle_time,
            "avg_cycle_time_delta": avg_cycle_time_delta,
            "avg_recovery_cost": avg_recovery_cost,
            "avg_recovery_cost_delta": avg_recovery_cost_delta,
            "value_recovery_rate": value_recovery_rate,
            "value_recovery_rate_delta": value_recovery_rate_delta,
            "total_returns_today": total_returns_today,
            "total_returns_today_delta": total_returns_today_delta,
            "inspection_queue_size": inspection_queue_size,
            "pickup_pending_count": pickup_pending_count,
            "kam_pending_count": kam_pending_count,
            "last_updated": datetime.utcnow(),
        }


kpi_service = KPIService()