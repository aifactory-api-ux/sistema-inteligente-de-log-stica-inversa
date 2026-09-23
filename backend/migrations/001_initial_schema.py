# backend/migrations/001_initial_schema.py

"""
Initial database schema migration for Sistema Inteligente de Logística Inversa
Version: 1.0.0
Date: 2026-09-23
"""

from typing import List
from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Boolean, Text,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from shared.database import Base


class ReturnRequestEntity(Base):
    """Return request entity for database storage"""
    __tablename__ = "return_requests"

    trace_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    channel = Column(String(10), nullable=False)
    customer_id = Column(String(50), nullable=False, index=True)
    customer_type = Column(String(50), nullable=False)
    order_reference = Column(String(100), nullable=False)
    invoice_reference = Column(String(100), nullable=True)

    items = Column(JSON, nullable=False)
    total_items = Column(Integer, nullable=False)
    total_value = Column(Numeric(12, 2), nullable=False)
    total_weight_kg = Column(Numeric(10, 3), nullable=False, default=0)
    total_volume_m3 = Column(Numeric(10, 4), nullable=False, default=0)

    return_reason = Column(String(20), nullable=False)
    return_reason_description = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="PENDIENTE", index=True)

    destination = Column(String(20), nullable=True)
    return_method = Column(String(20), nullable=True)
    decision_score = Column(Integer, nullable=True)
    decision_explanation = Column(Text, nullable=True)
    prompt_version = Column(String(20), nullable=False, default="v1.0.0")

    estimated_refund = Column(Numeric(12, 2), nullable=True)
    credit_note_value = Column(Numeric(12, 2), nullable=True)
    pre_approval_status = Column(String(20), nullable=True)

    drop_off_qr_code = Column(Text, nullable=True)
    drop_off_point_id = Column(String(50), nullable=True)
    scheduled_pickup_at = Column(DateTime, nullable=True)
    pickup_address = Column(JSON, nullable=True)
    tracking_number = Column(String(50), nullable=True, index=True)

    requires_kam_approval = Column(Boolean, nullable=False, default=False)
    kam_approver_id = Column(String(50), nullable=True)
    kam_approval_at = Column(DateTime, nullable=True)
    kam_comments = Column(Text, nullable=True)

    created_by = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False, default="decision-engine-v1")
    processing_time_ms = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_return_requests_created_at", "created_at"),
        Index("ix_return_requests_channel_status", "channel", "status"),
        Index("ix_return_requests_destination", "destination"),
    )


class AlertEntity(Base):
    """Alert entity for operational alerts"""
    __tablename__ = "alerts"

    alert_id = Column(String(50), primary_key=True)
    trace_id = Column(UUID(as_uuid=True), nullable=True)
    type = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    source = Column(String(100), nullable=False)
    related_return_id = Column(String(50), nullable=True, index=True)
    related_batch_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_alerts_priority_acknowledged", "priority", "acknowledged_at"),
        Index("ix_alerts_created_at_desc", created_at.desc()),
    )


class TrackingEventEntity(Base):
    """Tracking event entity for return timeline"""
    __tablename__ = "tracking_events"

    event_id = Column(String(50), primary_key=True)
    trace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    return_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    location = Column(String(200), nullable=False)
    description = Column(String(500), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    actor = Column(String(100), nullable=False)

    __table_args__ = (
        Index("ix_tracking_events_return_timestamp", "return_id", "timestamp"),
    )


class DropOffPointEntity(Base):
    """Drop-off point location entity"""
    __tablename__ = "drop_off_points"

    point_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    max_weight_kg = Column(Numeric(10, 3), nullable=False)
    max_volume_m3 = Column(Numeric(10, 4), nullable=False)
    available = Column(Boolean, nullable=False, default=True)
    operating_hours = Column(String(200), nullable=False)
    distance_km = Column(Numeric(8, 2), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class BatchUploadEntity(Base):
    """Batch upload entity for B2B CSV processing"""
    __tablename__ = "batch_uploads"

    batch_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), nullable=False, index=True)
    total_records = Column(Integer, nullable=False)
    valid_records = Column(Integer, nullable=False)
    invalid_records = Column(Integer, nullable=False)
    records = Column(JSON, nullable=False)
    total_value = Column(Numeric(12, 2), nullable=False)
    warnings = Column(JSON, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100), nullable=False)

    __table_args__ = (
        Index("ix_batch_uploads_customer_status", "customer_id", "status"),
        Index("ix_batch_uploads_created_at", "created_at"),
    )


class PickupEntity(Base):
    """Pickup scheduling entity"""
    __tablename__ = "pickups"

    pickup_id = Column(String(50), primary_key=True, index=True)
    return_id = Column(String(50), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False)
    pickup_address = Column(JSON, nullable=False)
    contact_phone = Column(String(20), nullable=True)
    tracking_number = Column(String(50), nullable=True, unique=True)
    estimated_duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="SCHEDULED")
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_pickups_status", "status"),
        Index("ix_pickups_return_id", "return_id"),
    )


class UserEntity(Base):
    """User entity for authentication and authorization"""
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    permissions = Column(JSON, nullable=False, default=list)
    email = Column(String(255), nullable=True)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('B2C_USER', 'B2B_USER', 'SUPERVISOR', 'KAM', 'ADMIN')"),
        Index("ix_users_role", "role"),
    )


class KAMApprovalEntity(Base):
    """KAM approval entity for B2B batch approvals"""
    __tablename__ = "kam_approvals"

    approval_id = Column(String(50), primary_key=True, index=True)
    return_id = Column(String(50), nullable=False, index=True)
    batch_id = Column(String(50), nullable=True, index=True)
    approved_by = Column(String(50), nullable=False)
    approved_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    comments = Column(Text, nullable=True)
    conditions = Column(JSON, nullable=True)
    action = Column(String(20), nullable=False)

    __table_args__ = (
        Index("ix_kam_approvals_return_id", "return_id"),
        Index("ix_kam_approvals_batch_id", "batch_id"),
    )


class ScoringWeightsEntity(Base):
    """Scoring weights configuration entity"""
    __tablename__ = "scoring_weights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    relevance = Column(Numeric(5, 2), nullable=False, default=1.0)
    urgency = Column(Numeric(5, 2), nullable=False, default=1.0)
    impact = Column(Numeric(5, 2), nullable=False, default=1.0)
    value_threshold = Column(Numeric(10, 2), nullable=False, default=50.00)
    weight_threshold_kg = Column(Numeric(10, 3), nullable=False, default=5.0)
    volume_threshold_m3 = Column(Numeric(10, 4), nullable=False, default=0.05)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)


class PromptConfigEntity(Base):
    """Prompt version configuration entity"""
    __tablename__ = "prompt_configs"

    version = Column(String(20), primary_key=True)
    prompt_text = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100), nullable=False)


class ReportEntity(Base):
    """Report generation entity"""
    __tablename__ = "reports"

    report_id = Column(String(50), primary_key=True, index=True)
    format = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="GENERATING")
    file_path = Column(String(500), nullable=True)
    filters = Column(JSON, nullable=False)
    include_kpis = Column(Boolean, nullable=False, default=True)
    include_alerts = Column(Boolean, nullable=False, default=True)
    include_returns = Column(Boolean, nullable=False, default=True)
    requested_by = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_reports_status", "status"),
        Index("ix_reports_requested_by", "requested_by"),
    )


def upgrade(connection) -> None:
    """Apply database schema migration"""
    Base.metadata.create_all(bind=connection)


def downgrade(connection) -> None:
    """Rollback database schema migration"""
    Base.metadata.drop_all(bind=connection)
