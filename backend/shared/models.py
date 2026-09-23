# backend/shared/models.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class ReturnChannel(str, Enum):
    B2C = "B2C"
    B2B = "B2B"


class ReturnDestination(str, Enum):
    CARRIL_RAPIDO = "CARRIL_RAPIDO"
    OUTLET = "OUTLET"
    RECICLAJE = "RECICLAJE"
    KEEP_IT = "KEEP_IT"
    INSPECCION_B2B = "INSPECCION_B2B"


class ReturnStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADO = "APROBADO"
    PRE_APROBADO = "PRE_APROBADO"
    RECHAZADO = "RECHAZADO"
    EN_TRANSITO = "EN_TRANSITO"
    ENTREGADO = "ENTREGADO"
    INSPECCION = "INSPECCION"
    PROCESADO = "PROCESADO"
    EXCEPTION = "EXCEPTION"


class ReturnMethod(str, Enum):
    DROP_OFF = "DROP_OFF"
    PICKUP = "PICKUP"
    KEEP_IT = "KEEP_IT"


class AlertPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    INSPECTION_SATURATION = "INSPECTION_SATURATION"
    B2B_APPROVAL_PENDING = "B2B_APPROVAL_PENDING"
    RETURN_RATE_SPIKE = "RETURN_RATE_SPIKE"
    CYCLE_TIME_EXCEEDED = "CYCLE_TIME_EXCEEDED"
    COST_THRESHOLD_BREACH = "COST_THRESHOLD_BREACH"


class ReturnItem(BaseModel):
    """Single item within a return request"""
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit")
    product_name: str = Field(..., max_length=255)
    quantity: int = Field(..., ge=1, le=9999)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    volume_m3: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    reason_code: str = Field(..., max_length=20)
    reason_description: Optional[str] = Field(None, max_length=500)
    condition: str = Field(default="NEW", max_length=20)
    batch_id: Optional[str] = Field(None, max_length=50)


class ReturnRequestCreate(BaseModel):
    """Request body for creating a new return"""
    model_config = ConfigDict(str_strip_whitespace=True)

    channel: ReturnChannel
    customer_id: str = Field(..., max_length=50)
    customer_type: str = Field(..., max_length=50)
    order_reference: str = Field(..., max_length=100)
    invoice_reference: Optional[str] = Field(None, max_length=100)

    items: list[ReturnItem] = Field(..., min_length=1, max_length=100)

    return_reason: str = Field(..., max_length=20)
    return_reason_description: Optional[str] = Field(None, max_length=500)

    pickup_address: Optional[dict] = Field(None, description="Address object for pickup")
    preferred_drop_off_id: Optional[str] = Field(None, max_length=50)
    preferred_time_slot: Optional[str] = Field(None, max_length=50)

    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)

    kam_approval_reference: Optional[str] = Field(None, max_length=100)


class ReturnRequest(BaseModel):
    """Complete return request with all metadata"""
    model_config = ConfigDict(str_strip_whitespace=True)

    trace_id: UUID = Field(default_factory=uuid4)
    return_id: str = Field(..., max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    channel: ReturnChannel
    customer_id: str
    customer_type: str
    order_reference: str
    invoice_reference: Optional[str] = None

    items: list[ReturnItem]
    total_items: int = Field(..., ge=1)
    total_value: Decimal = Field(..., ge=0, decimal_places=2)
    total_weight_kg: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3)
    total_volume_m3: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)

    return_reason: str
    return_reason_description: Optional[str] = None

    status: ReturnStatus = ReturnStatus.PENDIENTE

    destination: Optional[ReturnDestination] = None
    return_method: Optional[ReturnMethod] = None
    decision_score: Optional[int] = Field(None, ge=0, le=100)
    decision_explanation: Optional[str] = None
    prompt_version: str = Field(default="v1.0.0")

    estimated_refund: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    credit_note_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    pre_approval_status: Optional[str] = Field(None, max_length=20)

    drop_off_qr_code: Optional[str] = Field(None, description="Base64 encoded QR image")
    drop_off_point_id: Optional[str] = None
    scheduled_pickup_at: Optional[datetime] = None
    pickup_address: Optional[dict] = None
    tracking_number: Optional[str] = None

    requires_kam_approval: bool = False
    kam_approver_id: Optional[str] = None
    kam_approval_at: Optional[datetime] = None
    kam_comments: Optional[str] = None

    created_by: str = Field(..., max_length=100)
    model_version: str = Field(default="decision-engine-v1")
    processing_time_ms: Optional[int] = None


class DecisionInput(BaseModel):
    """Input to the decision engine"""
    channel: ReturnChannel
    customer_type: str
    total_value: Decimal
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    item_count: int
    return_reason: str
    has_kam_approval: bool = False


class DecisionResult(BaseModel):
    """Output from the decision engine"""
    destination: ReturnDestination
    return_method: ReturnMethod
    score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    factors: dict[str, float] = Field(default_factory=dict)
    business_rule_applied: str
    requires_kam_approval: bool = False
    processing_time_ms: int


class ScoringDimensions(BaseModel):
    """Scoring dimensions for decision engine"""
    relevance: int = Field(..., ge=0, le=33)
    urgency: int = Field(..., ge=0, le=33)
    impact: int = Field(..., ge=0, le=33)
    overall_score: int = Field(..., ge=0, le=100, description="Sum of dimensions")

    @classmethod
    def from_raw_scores(cls, relevance: int, urgency: int, impact: int) -> "ScoringDimensions":
        overall = relevance + urgency + impact
        return cls(relevance=relevance, urgency=urgency, impact=impact, overall_score=overall)


class BatchUploadRecord(BaseModel):
    """Single record parsed from CSV upload"""
    row_number: int
    sku: str
    quantity: int
    reason_code: str
    batch_id: Optional[str] = None
    validation_status: str = "PENDING"
    validation_errors: list[str] = Field(default_factory=list)


class BatchUploadResponse(BaseModel):
    """Response after processing CSV upload"""
    batch_id: str = Field(..., max_length=50)
    total_records: int
    valid_records: int
    invalid_records: int
    records: list[BatchUploadRecord]
    total_value: Decimal
    warnings: list[str] = Field(default_factory=list)
    processing_time_ms: int


class BatchApprovalAction(BaseModel):
    """KAM action on batch"""
    batch_id: str
    action: str = Field(..., pattern="^(APPROVE|REJECT|REQUEST_INFO)$")
    kam_id: str
    comments: Optional[str] = None


class KPIMetrics(BaseModel):
    """Control Tower KPI values"""
    return_rate: float = Field(..., ge=0, le=100, description="Percentage")
    cycle_time_hours: float = Field(..., ge=0)
    avg_recovery_cost: Decimal = Field(..., ge=0, decimal_places=2)
    value_recovery_rate: float = Field(..., ge=0, le=100, description="Percentage")
    total_returns_today: int
    total_value_today: Decimal

    return_rate_delta: float
    cycle_time_delta: float
    recovery_cost_delta: float
    recovery_rate_delta: float

    return_rate_history: list[float]
    cycle_time_history: list[float]
    recovery_cost_history: list[float]
    recovery_rate_history: list[float]


class DestinationDistribution(BaseModel):
    """Destination distribution percentages"""
    CARRIL_RAPIDO: float = Field(..., ge=0, le=100)
    OUTLET: float = Field(..., ge=0, le=100)
    RECICLAJE: float = Field(..., ge=0, le=100)
    KEEP_IT: float = Field(..., ge=0, le=100)
    INSPECCION_B2B: float = Field(..., ge=0, le=100)

    total: float = Field(default=100.0)

    @classmethod
    def from_counts(cls, counts: dict[str, int]) -> "DestinationDistribution":
        total = sum(counts.values())
        if total == 0:
            return cls(**{k: 0.0 for k in ["CARRIL_RAPIDO", "OUTLET", "RECICLAJE", "KEEP_IT", "INSPECCION_B2B"]})
        return cls(**{k: round((v / total) * 100, 2) for k, v in counts.items()})


class Alert(BaseModel):
    """Operational alert"""
    model_config = ConfigDict(str_strip_whitespace=True)

    alert_id: str = Field(..., max_length=50)
    trace_id: Optional[UUID] = None
    type: AlertType
    priority: AlertPriority
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=500)
    source: str = Field(..., max_length=100)
    related_return_id: Optional[str] = None
    related_batch_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class AlertAcknowledgement(BaseModel):
    """Acknowledge an alert"""
    alert_id: str
    acknowledged_by: str


class TrackingEvent(BaseModel):
    """Single tracking event"""
    event_id: str
    trace_id: UUID
    return_id: str
    status: ReturnStatus
    location: str = Field(..., max_length=200)
    description: str = Field(..., max_length=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = Field(..., max_length=100)


class TrackingTimeline(BaseModel):
    """Full tracking timeline for a return"""
    return_id: str
    events: list[TrackingEvent]
    estimated_delivery: Optional[datetime] = None
    last_updated: datetime


class DropOffPoint(BaseModel):
    """Authorized drop-off location"""
    point_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    address: str = Field(..., max_length=500)
    latitude: float
    longitude: float
    max_weight_kg: Decimal
    max_volume_m3: Decimal
    available: bool = True
    operating_hours: str = Field(..., max_length=200)
    distance_km: Optional[float] = None


class NearestDropOffPointsRequest(BaseModel):
    """Request nearest drop-off points"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_results: int = Field(default=5, ge=1, le=20)
    max_weight_kg: Optional[Decimal] = None
    max_volume_m3: Optional[Decimal] = None


class ReportFilters(BaseModel):
    """Filters for report generation"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    channel: Optional[ReturnChannel] = None
    destination: Optional[ReturnDestination] = None
    status: Optional[ReturnStatus] = None
    customer_id: Optional[str] = None
    alert_priority: Optional[AlertPriority] = None


class ReportRequest(BaseModel):
    """Request report generation"""
    format: str = Field(..., pattern="^(PDF|HTML|CSV)$")
    filters: ReportFilters
    include_kpis: bool = True
    include_alerts: bool = True
    include_returns: bool = True
    requested_by: str


class ScoringWeights(BaseModel):
    """Admin-configurable scoring weights"""
    relevance: float = Field(default=1.0, ge=0, le=10)
    urgency: float = Field(default=1.0, ge=0, le=10)
    impact: float = Field(default=1.0, ge=0, le=10)
    value_threshold: Decimal = Field(default=Decimal("50.00"), ge=0)
    weight_threshold_kg: Decimal = Field(default=Decimal("5.0"), ge=0)
    volume_threshold_m3: Decimal = Field(default=Decimal("0.05"), ge=0)


class PromptConfig(BaseModel):
    """Prompt version management"""
    version: str = Field(..., max_length=20)
    prompt_text: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class User(BaseModel):
    """User model for authentication"""
    user_id: str = Field(..., max_length=50)
    username: str = Field(..., max_length=100)
    role: str = Field(..., max_length=20)
    permissions: list[str] = Field(default_factory=list)
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=200)


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    user: User


class PickupSlot(BaseModel):
    """Available pickup time slot"""
    slot_id: str = Field(..., max_length=50)
    date: str = Field(..., max_length=10)
    time_slot: str = Field(..., max_length=50)
    available: bool = True


class PickupScheduleRequest(BaseModel):
    """Request to schedule a pickup"""
    return_id: str = Field(..., max_length=50)
    pickup_address: dict = Field(..., description="Address object")
    preferred_date: str = Field(..., max_length=10)
    preferred_time_slot: str = Field(..., max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    special_instructions: Optional[str] = Field(None, max_length=500)


class PickupScheduleResponse(BaseModel):
    """Response after scheduling pickup"""
    pickup_id: str = Field(..., max_length=50)
    return_id: str = Field(..., max_length=50)
    scheduled_at: datetime
    pickup_address: dict
    contact_phone: Optional[str] = None
    tracking_number: str = Field(..., max_length=50)
    estimated_duration_minutes: int
    status: str = Field(default="SCHEDULED", max_length=20)


class KAMApprovalRequest(BaseModel):
    """KAM approval action request"""
    comments: Optional[str] = Field(None, max_length=500)
    conditions: Optional[list[str]] = None


class KAMApprovalResponse(BaseModel):
    """KAM approval action response"""
    approval_id: str = Field(..., max_length=50)
    return_id: str = Field(..., max_length=50)
    approved_by: str = Field(..., max_length=50)
    approved_at: datetime
    comments: Optional[str] = None
    conditions: Optional[list[str]] = None
