# backend/src/schemas.py

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class ReturnItemSchema(BaseModel):
    sku: str = Field(..., max_length=50)
    product_name: str = Field(..., max_length=255)
    quantity: int = Field(..., ge=1, le=9999)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    volume_m3: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    reason_code: str = Field(..., max_length=20)
    reason_description: Optional[str] = Field(None, max_length=500)
    condition: str = Field(default="NEW", max_length=20)
    batch_id: Optional[str] = Field(None, max_length=50)
    is_customized: bool = Field(default=False)


class ReturnRequestCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    channel: str = Field(..., pattern="^(B2C|B2B)$")
    customer_id: str = Field(..., max_length=50)
    customer_type: str = Field(..., max_length=50)
    order_reference: str = Field(..., max_length=100)
    invoice_reference: Optional[str] = Field(None, max_length=100)

    items: list[ReturnItemSchema] = Field(..., min_length=1, max_length=100)

    return_reason: str = Field(..., max_length=20)
    return_reason_description: Optional[str] = Field(None, max_length=500)

    pickup_address: Optional[dict] = Field(None)
    preferred_drop_off_id: Optional[str] = Field(None, max_length=50)
    preferred_time_slot: Optional[str] = Field(None, max_length=50)

    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)

    kam_approval_reference: Optional[str] = Field(None, max_length=100)


class ReturnRequestResponseSchema(BaseModel):
    trace_id: UUID
    return_id: str
    created_at: datetime
    updated_at: datetime

    channel: str
    customer_id: str
    customer_type: str
    order_reference: str
    invoice_reference: Optional[str] = None

    items: list[ReturnItemSchema]
    total_items: int
    total_value: Decimal
    total_weight_kg: Decimal
    total_volume_m3: Decimal

    return_reason: str
    return_reason_description: Optional[str] = None

    status: str
    destination: Optional[str] = None
    return_method: Optional[str] = None
    decision_score: Optional[int] = Field(None, ge=0, le=100)
    decision_explanation: Optional[str] = None

    estimated_refund: Optional[Decimal] = None
    credit_note_value: Optional[Decimal] = None
    pre_approval_status: Optional[str] = None

    drop_off_qr_code: Optional[str] = None
    drop_off_point_id: Optional[str] = None
    scheduled_pickup_at: Optional[datetime] = None
    pickup_address: Optional[dict] = None
    tracking_number: Optional[str] = None

    requires_kam_approval: bool = False
    kam_approver_id: Optional[str] = None
    kam_approval_at: Optional[datetime] = None
    kam_comments: Optional[str] = None

    created_by: str
    processing_time_ms: Optional[int] = None


class ReturnsListResponseSchema(BaseModel):
    items: list[ReturnRequestResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReturnsFiltersSchema(BaseModel):
    channel: Optional[str] = Field(None, pattern="^(B2C|B2B)$")
    status: Optional[str] = None
    destination: Optional[str] = None
    customer_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class LoginRequestSchema(BaseModel):
    username: str = Field(..., max_length=100)
    password: str = Field(..., min_length=1)


class UserSchema(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    permissions: list[str] = Field(default_factory=list)
    customer_id: Optional[str] = None
    is_active: bool = True


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class AuthResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserSchema


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class HealthResponseSchema(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: dict[str, str]


class DecisionInputSchema(BaseModel):
    channel: str = Field(..., pattern="^(B2C|B2B)$")
    customer_type: str
    items: list[ReturnItemSchema] = Field(default_factory=list)
    total_value: Decimal
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    item_count: int
    return_reason: str
    has_kam_approval: bool = False


class DecisionResultSchema(BaseModel):
    destination: str
    return_method: str
    score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    factors: dict[str, float] = Field(default_factory=dict)
    business_rule_applied: str
    requires_kam_approval: bool = False
    processing_time_ms: int


class ErrorResponseSchema(BaseModel):
    detail: str
    code: Optional[str] = None
    errors: Optional[list[dict]] = None


class MessageResponseSchema(BaseModel):
    message: str
    success: bool = True


class BatchUploadRecordSchema(BaseModel):
    row_number: int
    sku: str
    product_name: str
    quantity: int = Field(..., ge=1, le=9999)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    volume_m3: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    reason_code: str = Field(..., max_length=20)
    reason_description: Optional[str] = Field(None, max_length=500)
    condition: str = Field(default="NEW", max_length=20)
    batch_id: Optional[str] = Field(None, max_length=50)
    is_customized: bool = Field(default=False)
    is_valid: bool = True
    validation_errors: list[str] = Field(default_factory=list)


class BatchUploadResponseSchema(BaseModel):
    batch_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    records: list[BatchUploadRecordSchema]
    processing_time_ms: int
    status: str = Field(..., max_length=20)


class BatchUploadCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., max_length=50)
    order_reference: str = Field(..., max_length=100)
    invoice_reference: Optional[str] = Field(None, max_length=100)
    return_reason: str = Field(..., max_length=20)
    return_reason_description: Optional[str] = Field(None, max_length=500)
    pickup_address: Optional[dict] = Field(None)
    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)


class KAMApprovalSchema(BaseModel):
    kam_comments: Optional[str] = Field(None, max_length=500)


class KAMApprovalResponseSchema(BaseModel):
    return_id: str
    status: str
    destination: str
    return_method: str
    kam_approved_by: str
    kam_approved_at: datetime
    message: str


class KPIDashboardResponseSchema(BaseModel):
    return_rate: float
    return_rate_delta: float
    avg_cycle_time_hours: float
    avg_cycle_time_delta: float
    avg_recovery_cost: Decimal
    avg_recovery_cost_delta: Decimal
    value_recovery_rate: float
    value_recovery_rate_delta: float
    total_returns_today: int
    total_returns_today_delta: int
    inspection_queue_size: int
    pickup_pending_count: int
    kam_pending_count: int
    last_updated: datetime


class DestinationDistributionResponseSchema(BaseModel):
    CARRIL_RAPIDO: int = 0
    OUTLET: int = 0
    RECICLAJE: int = 0
    KEEP_IT: int = 0
    INSPECCION_B2B: int = 0
    total: int = 0


class AlertSchema(BaseModel):
    alert_id: str
    type: str
    priority: str
    message: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    metadata: Optional[str] = None
    created_at: str


class AlertsListResponseSchema(BaseModel):
    alerts: list[AlertSchema]
    total: int


class KPIAlertsResponseSchema(BaseModel):
    alert_id: str
    type: str
    priority: str
    message: str
    acknowledged: bool
    created_at: datetime
