# backend/src/routers/__init__.py

from src.routers import auth
from src.routers import returns
from src.routers import kam
from src.routers import batch
from src.routers import kpi
from src.routers import reports
from src.routers import control_tower
from src.routers import admin
from src.routers import decision
from src.routers import dropoff
from src.routers import pickup

__all__ = ["auth", "returns", "kam", "batch", "kpi", "reports", "control_tower", "admin", "decision", "dropoff", "pickup"]
