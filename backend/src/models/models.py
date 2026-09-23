# backend/src/models/models.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
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


class UserRole(str, Enum):
    B2C_USER = "B2C_USER"
    B2B_USER = "B2B_USER"
    SUPERVISOR = "SUPERVISOR"
    KAM = "KAM"
    ADMIN = "ADMIN"


class BatchUploadStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Address(BaseModel):
    street: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(default="ES", max_length=2)


class ReturnItem(BaseModel):
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


class ReturnRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    channel: ReturnChannel
    customer_id: str = Field(..., max_length=50)
    customer_type: str = Field(..., max_length=50)
    order_reference: str = Field(..., max_length=100)
    invoice_reference: Optional[str] = Field(None, max_length=100)
    items: list[ReturnItem] = Field(..., min_length=1, max_length=100)
    return_reason: str = Field(..., max_length=20)
    return_reason_description: Optional[str] = Field(None, max_length=500)
    pickup_address: Optional[dict] = Field(None)
    preferred_drop_off_id: Optional[str] = Field(None, max_length=50)
    preferred_time_slot: Optional[str] = Field(None, max_length=50)
    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    kam_approval_reference: Optional[str] = Field(None, max_length=100)


class ReturnRequest(BaseModel):
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
    return_reason: str
    return_reason_description: Optional[str] = None
    pickup_address: Optional[dict] = None
    preferred_drop_off_id: Optional[str] = None
    preferred_time_slot: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    status: ReturnStatus = ReturnStatus.PENDIENTE
    destination: Optional[ReturnDestination] = None
    method: Optional[ReturnMethod] = None
    estimated_reimbursement: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    qr_code: Optional[str] = None
    qr_code_expires_at: Optional[datetime] = None
    pickup_scheduled_at: Optional[datetime] = None
    pickup_carrier: Optional[str] = None
    kam_approval_reference: Optional[str] = None
    kam_approved_by: Optional[str] = None
    kam_approved_at: Optional[datetime] = None
    is_approved: bool = False
    rejection_reason: Optional[str] = None
    metadata: Optional[dict] = None
    batch_id: Optional[str] = None


class DecisionInput(BaseModel):
    channel: ReturnChannel
    customer_type: str
    items: list[ReturnItem]
    total_items: int
    total_weight_kg: Optional[Decimal] = None
    total_volume_m3: Optional[Decimal] = None
    return_reason: str
    is_batch: bool = False
    batch_id: Optional[str] = None


class DecisionResult(BaseModel):
    destination: ReturnDestination
    method: ReturnMethod
    status: ReturnStatus
    estimated_reimbursement: Decimal
    rule_applied: str
    explanation: str
    keep_it_reason: Optional[str] = None
    inspection_required: bool = False
    kam_approval_required: bool = False


class KPIMetrics(BaseModel):
    return_rate: Decimal
    return_rate_delta: Decimal = Decimal("0")
    avg_cycle_time_hours: Decimal
    avg_cycle_time_delta: Decimal = Decimal("0")
    avg_recovery_cost: Decimal
    avg_recovery_cost_delta: Decimal = Decimal("0")
    value_recovery_rate: Decimal
    value_recovery_rate_delta: Decimal = Decimal("0")
    total_returns_today: int = 0
    total_returns_today_delta: int = 0
    inspection_queue_size: int = 0
    pickup_pending_count: int = 0
    kam_pending_count: int = 0


class DestinationDistribution(BaseModel):
    CARRIL_RAPIDO: int = 0
    OUTLET: int = 0
    RECICLAJE: int = 0
    KEEP_IT: int = 0
    INSPECCION_B2B: int = 0


class Alert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    alert_id: str = Field(..., max_length=50)
    type: AlertType
    priority: AlertPriority
    message: str = Field(..., max_length=500)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    role: UserRole
    customer_id: Optional[str] = Field(None, max_length=50)
    full_name: str = Field(..., max_length=255)
    hashed_password: str = Field(..., max_length=255)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BatchUploadRecord(BaseModel):
    row_number: int
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
    is_valid: bool = True
    validation_errors: list[str] = []


class BatchUpload(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    batch_id: str = Field(..., max_length=50)
    customer_id: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    records: list[BatchUploadRecord] = []
    total_value: Decimal = Decimal("0.00")
    status: BatchUploadStatus = BatchUploadStatus.PENDING
    processing_time_ms: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class DropOffPoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    point_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    address: Address
    latitude: Decimal = Field(..., decimal_places=6)
    longitude: Decimal = Field(..., decimal_places=6)
    max_weight_kg: Decimal = Field(..., ge=0, decimal_places=3)
    max_volume_m3: Decimal = Field(..., ge=0, decimal_places=4)
    opening_hours: str = Field(..., max_length=100)
    available: bool = True


class TimeSlot(BaseModel):
    id: str = Field(..., max_length=50)
    date: str = Field(..., max_length=10)
    start_time: str = Field(..., max_length=10)
    end_time: str = Field(..., max_length=10)
    available: bool = True


class PickupSchedulingRequest(BaseModel):
    return_id: str = Field(..., max_length=50)
    selected_slot_id: str = Field(..., max_length=50)
    pickup_address: Address
    special_instructions: Optional[str] = Field(None, max_length=500)


class NotificationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str = Field(..., pattern="^(success|error|warning|info)$")
    title: str = Field(..., max_length=100)
    message: str = Field(..., max_length=500)
    read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QRCodeData(BaseModel):
    token: str
    return_id: str
    trace_id: str
    channel: str
    expires_at: datetime


__all__ = [
    "Address",
    "Alert",
    "AlertPriority",
    "AlertType",
    "BatchUpload",
    "BatchUploadRecord",
    "BatchUploadStatus",
    "DecisionInput",
    "DecisionResult",
    "DestinationDistribution",
    "DropOffPoint",
    "KPIMetrics",
    "NotificationItem",
    "PickupSchedulingRequest",
    "QRCodeData",
    "ReturnChannel",
    "ReturnDestination",
    "ReturnItem",
    "ReturnMethod",
    "ReturnRequest",
    "ReturnRequestCreate",
    "ReturnStatus",
    "TimeSlot",
    "User",
    "UserRole",
]
