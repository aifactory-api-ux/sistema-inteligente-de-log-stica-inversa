# SPEC.md

## Sistema Inteligente de Logística Inversa — Technical Specification

**Project Name**: Sistema Inteligente de Logística Inversa  
**Project ID**: a1f531ec-0bee-42c5-b6c2-0eae037a17ec  
**Contract Version**: 1.1  
**Generated**: 2026-09-23T16:10:44Z  
**Status**: Production Implementation

---

## 1. TECHNOLOGY STACK

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18.x | UI framework |
| Vite | 5.x | Build tool and dev server |
| TypeScript | 5.x | Type safety |
| React Router | 6.x | Client-side routing |
| Zustand | 4.x | State management |
| Tailwind CSS | 3.x | Utility-first styling |
| Recharts | 2.x | Data visualization (KPIs, distribution bars) |
| qrcode.react | 3.x | QR code generation |
| react-dropzone | 14.x | File upload (BatchUploadZone) |
| date-fns | 3.x | Date formatting |
| lucide-react | latest | Icon library |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core application |
| FastAPI | 0.109.x | REST API framework |
| Pydantic | 2.x | Data validation |
| Uvicorn | 0.27.x | ASGI server |
| python-multipart | 0.0.9 | Multipart file uploads |
| pandas | 2.x | CSV parsing and processing |
| qrcode | 7.x | QR code image generation |
| Pillow | 10.x | Image processing |
| jinja2 | 3.x | Email/notification templates |
| weasyprint | 60.x | PDF report generation |
| prometheus-client | 0.19.x | Metrics exposition |
| opentelemetry-api | 1.22.x | Distributed tracing |
| opentelemetry-sdk | 1.22.x | Tracing implementation |
| structlog | 24.x | Structured logging |

### Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL 15+ | Primary database |
| Redis 7+ | Session cache, rate limiting |
| Docker | Containerization |
| Docker Compose | Local development orchestration |

---

## 2. DATA CONTRACTS

### Python/Pydantic Models (Backend)

```python
# shared/models.py

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
    CARRIL_RAPIDO = "CARRIL_RAPIDO"      # Fast Lane
    OUTLET = "OUTLET"                      # Outlet resale
    RECICLAJE = "RECICLAJE"                # Textile recycling
    KEEP_IT = "KEEP_IT"                    # Return to stock
    INSPECCION_B2B = "INSPECCION_B2B"      # B2B incident inspection

class ReturnStatus(str, Enum):
    PENDIENTE = "PENDIENTE"                # Pending evaluation
    APROBADO = "APROBADO"                  # Approved
    PRE_APROBADO = "PRE_APROBADO"          # Pre-approved
    RECHAZADO = "RECHAZADO"                # Rejected
    EN_TRANSITO = "EN_TRANSITO"           # In transit
    ENTREGADO = "ENTREGADO"                # Delivered
    INSPECCION = "INSPECCION"              # Under inspection
    PROCESADO = "PROCESADO"                # Processed
    EXCEPTION = "EXCEPTION"                # Exception requiring KAM approval

class ReturnMethod(str, Enum):
    DROP_OFF = "DROP_OFF"                  # QR code drop-off point
    PICKUP = "PICKUP"                     # Scheduled pickup
    KEEP_IT = "KEEP_IT"                   # No return needed

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

# === CORE RETURN MODEL ===

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
    
    # Decision engine results
    destination: Optional[ReturnDestination] = None
    return_method: Optional[ReturnMethod] = None
    decision_score: Optional[int] = Field(None, ge=0, le=100)
    decision_explanation: Optional[str] = None
    prompt_version: str = Field(default="v1.0.0")
    
    # Financial
    estimated_refund: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    credit_note_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    pre_approval_status: Optional[str] = Field(None, max_length=20)
    
    # Logistics
    drop_off_qr_code: Optional[str] = Field(None, description="Base64 encoded QR image")
    drop_off_point_id: Optional[str] = None
    scheduled_pickup_at: Optional[datetime] = None
    pickup_address: Optional[dict] = None
    tracking_number: Optional[str] = None
    
    # KAM approval
    requires_kam_approval: bool = False
    kam_approver_id: Optional[str] = None
    kam_approval_at: Optional[datetime] = None
    kam_comments: Optional[str] = None
    
    # Audit
    created_by: str = Field(..., max_length=100)
    prompt_version: str = Field(default="v1.0.0")
    model_version: str = Field(default="decision-engine-v1")
    processing_time_ms: Optional[int] = None

# === DECISION ENGINE ===

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

# === BATCH PROCESSING (B2B) ===

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

# === KPIs AND METRICS ===

class KPIMetrics(BaseModel):
    """Control Tower KPI values"""
    return_rate: float = Field(..., ge=0, le=100, description="Percentage")
    cycle_time_hours: float = Field(..., ge=0)
    avg_recovery_cost: Decimal = Field(..., ge=0, decimal_places=2)
    value_recovery_rate: float = Field(..., ge=0, le=100, description="Percentage")
    total_returns_today: int
    total_value_today: Decimal
    
    # Deltas (trend indicators)
    return_rate_delta: float
    cycle_time_delta: float
    recovery_cost_delta: float
    recovery_rate_delta: float
    
    # Sparkline data (last 7 days)
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

# === ALERTS ===

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

# === TRACKING ===

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

# === DROP-OFF POINTS ===

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

# === REPORTS ===

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

# === ADMIN CONFIGURATION ===

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
```

### TypeScript Interfaces (Frontend)

```typescript
// frontend/src/types/models.ts

export enum ReturnChannel {
  B2C = "B2C",
  B2B = "B2B",
}

export enum ReturnDestination {
  CARRIL_RAPIDO = "CARRIL_RAPIDO",
  OUTLET = "OUTLET",
  RECICLAJE = "RECICLAJE",
  KEEP_IT = "KEEP_IT",
  INSPECCION_B2B = "INSPECCION_B2B",
}

export enum ReturnStatus {
  PENDIENTE = "PENDIENTE",
  APROBADO = "APROBADO",
  PRE_APROBADO = "PRE_APROBADO",
  RECHAZADO = "RECHAZADO",
  EN_TRANSITO = "EN_TRANSITO",
  ENTREGADO = "ENTREGADO",
  INSPECCION = "INSPECCION",
  PROCESADO = "PROCESADO",
  EXCEPTION = "EXCEPTION",
}

export enum ReturnMethod {
  DROP_OFF = "DROP_OFF",
  PICKUP = "PICKUP",
  KEEP_IT = "KEEP_IT",
}

export enum AlertPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum AlertType {
  INSPECTION_SATURATION = "INSPECTION_SATURATION",
  B2B_APPROVAL_PENDING = "B2B_APPROVAL_PENDING",
  RETURN_RATE_SPIKE = "RETURN_RATE_SPIKE",
  CYCLE_TIME_EXCEEDED = "CYCLE_TIME_EXCEEDED",
  COST_THRESHOLD_BREACH = "COST_THRESHOLD_BREACH",
}

export interface Address {
  street: string;
  city: string;
  postal_code: string;
  country: string;
  latitude?: number;
  longitude?: number;
}

export interface ReturnItem {
  sku: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  weight_kg?: number;
  volume_m3?: number;
  reason_code: string;
  reason_description?: string;
  condition: string;
  batch_id?: string;
}

export interface ReturnRequestCreate {
  channel: ReturnChannel;
  customer_id: string;
  customer_type: string;
  order_reference: string;
  invoice_reference?: string;
  items: ReturnItem[];
  return_reason: string;
  return_reason_description?: string;
  pickup_address?: Address;
  preferred_drop_off_id?: string;
  preferred_time_slot?: string;
  contact_email: string;
  contact_phone?: string;
  kam_approval_reference?: string;
}

export interface ReturnRequest {
  trace_id: string;
  return_id: string;
  created_at: string;
  updated_at: string;
  channel: ReturnChannel;
  customer_id: string;
  customer_type: string;
  order_reference: string;
  invoice_reference?: string;
  items: ReturnItem[];
  total_items: number;
  total_value: number;
  total_weight_kg: number;
  total_volume_m3: number;
  return_reason: string;
  return_reason_description?: string;
  status: ReturnStatus;
  destination?: ReturnDestination;
  return_method?: ReturnMethod;
  decision_score?: number;
  decision_explanation?: string;
  estimated_refund?: number;
  credit_note_value?: number;
  pre_approval_status?: string;
  drop_off_qr_code?: string;
  drop_off_point_id?: string;
  scheduled_pickup_at?: string;
  pickup_address?: Address;
  tracking_number?: string;
  requires_kam_approval: boolean;
  kam_approver_id?: string;
  kam_approval_at?: string;
  kam_comments?: string;
  created_by: string;
  prompt_version: string;
  model_version: string;
  processing_time_ms?: number;
}

export interface DecisionResult {
  destination: ReturnDestination;
  return_method: ReturnMethod;
  score: number;
  confidence: number;
  explanation: string;
  factors: Record<string, number>;
  business_rule_applied: string;
  requires_kam_approval: boolean;
  processing_time_ms: number;
}

export interface ScoringDimensions {
  relevance: number;
  urgency: number;
  impact: number;
  overall_score: number;
}

export interface BatchUploadRecord {
  row_number: number;
  sku: string;
  quantity: number;
  reason_code: string;
  batch_id?: string;
  validation_status: string;
  validation_errors: string[];
}

export interface BatchUploadResponse {
  batch_id: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  records: BatchUploadRecord[];
  total_value: number;
  warnings: string[];
  processing_time_ms: number;
}

export interface KPIMetrics {
  return_rate: number;
  cycle_time_hours: number;
  avg_recovery_cost: number;
  value_recovery_rate: number;
  total_returns_today: number;
  total_value_today: number;
  return_rate_delta: number;
  cycle_time_delta: number;
  recovery_cost_delta: number;
  recovery_rate_delta: number;
  return_rate_history: number[];
  cycle_time_history: number[];
  recovery_cost_history: number[];
  recovery_rate_history: number[];
}

export interface DestinationDistribution {
  CARRIL_RAPIDO: number;
  OUTLET: number;
  RECICLAJE: number;
  KEEP_IT: number;
  INSPECCION_B2B: number;
  total: number;
}

export interface Alert {
  alert_id: string;
  trace_id?: string;
  type: AlertType;
  priority: AlertPriority;
  title: string;
  message: string;
  source: string;
  related_return_id?: string;
  related_batch_id?: string;
  created_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
}

export interface TrackingEvent {
  event_id: string;
  trace_id: string;
  return_id: string;
  status: ReturnStatus;
  location: string;
  description: string;
  timestamp: string;
  actor: string;
}

export interface TrackingTimeline {
  return_id: string;
  events: TrackingEvent[];
  estimated_delivery?: string;
  last_updated: string;
}

export interface DropOffPoint {
  point_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  max_weight_kg: number;
  max_volume_m3: number;
  available: boolean;
  operating_hours: string;
  distance_km?: number;
}

export interface ReportFilters {
  date_from?: string;
  date_to?: string;
  channel?: ReturnChannel;
  destination?: ReturnDestination;
  status?: ReturnStatus;
  customer_id?: string;
  alert_priority?: AlertPriority;
}

export interface ReportRequest {
  format: "PDF" | "HTML" | "CSV";
  filters: ReportFilters;
  include_kpis: boolean;
  include_alerts: boolean;
  include_returns: boolean;
  requested_by: string;
}

export interface ProfileOption {
  id: string;
  label: string;
  description: string;
  icon: string;
  type: "B2C" | "B2B";
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  priority: AlertPriority;
  timestamp: string;
  read: boolean;
}
```

---

## 3. API ENDPOINTS

### Base URL Configuration
- Development: `http://localhost:21001/api/v1`
- Production: `https://api.logistica-inversa.com/api/v1`

### Authentication Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Authenticate user and receive JWT token |
| POST | `/auth/refresh` | Refresh expired JWT token |
| POST | `/auth/logout` | Invalidate current session |
| GET | `/auth/me` | Get current authenticated user profile |

**POST /auth/login**
```json
// Request
{
  "username": "string",
  "password": "string"
}
// Response 200
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "string",
    "username": "string",
    "role": "B2C_USER | B2B_USER | SUPERVISOR | KAM | ADMIN",
    "permissions": ["string"]
  }
}
```

### Return Management Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/returns` | Create a new return request (B2C single item or B2B) |
| GET | `/returns` | List returns with filters and pagination |
| GET | `/returns/{return_id}` | Get return details by return_id |
| GET | `/returns/trace/{trace_id}` | Get return details by trace_id |
| PUT | `/returns/{return_id}` | Update return status or details |
| DELETE | `/returns/{return_id}` | Cancel/delete a pending return |
| POST | `/returns/{return_id}/evaluate` | Re-evaluate an existing return |
| GET | `/returns/{return_id}/tracking` | Get tracking timeline |
| POST | `/returns/{return_id}/acknowledge` | Acknowledge receipt of return |

**POST /returns**
```json
// Request Body (ReturnRequestCreate)
{
  "channel": "B2C | B2B",
  "customer_id": "string",
  "customer_type": "string",
  "order_reference": "string",
  "invoice_reference": "string | null",
  "items": [
    {
      "sku": "string",
      "product_name": "string",
      "quantity": 1,
      "unit_price": 99.99,
      "weight_kg": 0.5,
      "volume_m3": 0.002,
      "reason_code": "DEFECTIVE | WRONG_ITEM | CHANGED_MIND | OTHER",
      "reason_description": "string | null",
      "condition": "NEW | OPENED | DAMAGED",
      "batch_id": "string | null"
    }
  ],
  "return_reason": "string",
  "return_reason_description": "string | null",
  "pickup_address": {
    "street": "string",
    "city": "string",
    "postal_code": "string",
    "country": "string",
    "latitude": 40.4168,
    "longitude": -3.7038
  } | null,
  "preferred_drop_off_id": "string | null",
  "preferred_time_slot": "string | null",
  "contact_email": "user@example.com",
  "contact_phone": "+34612345678",
  "kam_approval_reference": "string | null"
}
// Response 201
{
  "trace_id": "uuid",
  "return_id": "RET-2026-000001",
  "created_at": "2026-09-23T16:00:00Z",
  "status": "PRE_APROBADO | PENDIENTE",
  "destination": "CARRIL_RAPIDO | OUTLET | RECICLAJE | KEEP_IT | INSPECCION_B2B",
  "return_method": "DROP_OFF | PICKUP | KEEP_IT",
  "decision_score": 75,
  "decision_explanation": "string",
  "estimated_refund": 89.99,
  "credit_note_value": null,
  "pre_approval_status": "APPROVED | PENDING_KAM | REJECTED",
  "drop_off_qr_code": "base64_encoded_image | null",
  "drop_off_point_id": "string | null",
  "scheduled_pickup_at": "2026-09-25T09:00:00Z | null",
  "requires_kam_approval": false,
  "processing_time_ms": 234
}
```

**GET /returns**
```json
// Query Parameters
{
  "page": 1,
  "page_size": 20,
  "channel": "B2C | B2B | null",
  "status": "string | null",
  "destination": "string | null",
  "customer_id": "string | null",
  "date_from": "ISO8601 | null",
  "date_to": "ISO8601 | null",
  "sort_by": "created_at | status | destination | total_value",
  "sort_order": "asc | desc"
}
// Response 200
{
  "items": [ReturnRequest],
  "total": 1500,
  "page": 1,
  "page_size": 20,
  "total_pages": 75
}
```

### Decision Engine Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/decision/evaluate` | Evaluate a return and get destination/method |
| GET | `/decision/explain/{return_id}` | Get detailed explanation for a decision |
| GET | `/decision/rules` | Get current business rules configuration |
| GET | `/decision/scoring` | Get scoring dimension weights |

**POST /decision/evaluate**
```json
// Request
{
  "channel": "B2C | B2B",
  "customer_type": "string",
  "total_value": 150.00,
  "total_weight_kg": 2.5,
  "total_volume_m3": 0.01,
  "item_count": 3,
  "return_reason": "DEFECTIVE",
  "has_kam_approval": false
}
// Response 200
{
  "destination": "CARRIL_RAPIDO",
  "return_method": "DROP_OFF",
  "score": 82,
  "confidence": 0.95,
  "explanation": "Alta probabilidad de valor recuperable. Producto defectuoso en plazo.",
  "factors": {
    "value_factor": 0.8,
    "condition_factor": 0.7,
    "timeline_factor": 0.9
  },
  "business_rule_applied": "VALUE_THRESHOLD_APPROVED",
  "requires_kam_approval": false,
  "processing_time_ms": 156
}
```

### Batch Upload Endpoints (B2B)

| Method | Path | Description |
|---|---|---|
| POST | `/batches/upload` | Upload CSV for batch return processing |
| GET | `/batches/{batch_id}` | Get batch processing status |
| GET | `/batches` | List all batches with filters |
| POST | `/batches/{batch_id}/approve` | KAM approves a batch |
| POST | `/batches/{batch_id}/reject` | KAM rejects a batch |
| DELETE | `/batches/{batch_id}` | Cancel/delete a batch |

**POST /batches/upload**
```json
// Request: multipart/form-data
// file: CSV file (required)
// customer_id: string (required)
// return_reason: string (required)
// kam_approval_reference: string (optional)

// CSV Format:
// sku,quantity,reason_code,batch_id,weight_kg,volume_m3
// SKU001,5,DEFECTIVE,BATCH-A,2.5,0.01
// SKU002,3,WRONG_ITEM,,1.5,0.005

// Response 200
{
  "batch_id": "BATCH-2026-000001",
  "total_records": 25,
  "valid_records": 23,
  "invalid_records": 2,
  "records": [
    {
      "row_number": 1,
      "sku": "SKU001",
      "quantity": 5,
      "reason_code": "DEFECTIVE",
      "batch_id": "BATCH-A",
      "validation_status": "VALID",
      "validation_errors": []
    }
  ],
  "total_value": 1250.00,
  "warnings": ["SKU003 has unknown condition"],
  "processing_time_ms": 456
}
```

### QR Code and Drop-off Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/dropoff/points` | Get nearest authorized drop-off points |
| GET | `/dropoff/points/{point_id}` | Get drop-off point details |
| GET | `/dropoff/qr/{return_id}` | Get/regenerate QR code for return |
| GET | `/dropoff/instructions/{return_id}` | Get packaging and drop-off instructions |

**GET /dropoff/points**
```json
// Query Parameters
{
  "latitude": 40.4168,
  "longitude": -3.7038,
  "max_results": 5,
  "max_weight_kg": 10.0,
  "max_volume_m3": 0.05
}
// Response 200
{
  "points": [
    {
      "point_id": "DROP-001",
      "name": "Punto Drop-off Centro Comercial",
      "address": "Calle Gran Vía 1, Madrid",
      "latitude": 40.4175,
      "longitude": -3.7025,
      "max_weight_kg": 20.0,
      "max_volume_m3": 0.1,
      "available": true,
      "operating_hours": "L-V 09:00-21:00, S 10:00-14:00",
      "distance_km": 0.5
    }
  ]
}
```

### Pickup Scheduling Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/pickup/slots` | Get available pickup time slots |
| POST | `/pickup/schedule` | Schedule a pickup for return |
| GET | `/pickup/{return_id}` | Get pickup details |
| PUT | `/pickup/{return_id}/reschedule` | Reschedule pickup time |
| DELETE | `/pickup/{return_id}` | Cancel scheduled pickup |

**POST /pickup/schedule**
```json
// Request
{
  "return_id": "RET-2026-000001",
  "pickup_address": {
    "street": "string",
    "city": "string",
    "postal_code": "string",
    "country": "Spain",
    "latitude": 40.4168,
    "longitude": -3.7038
  },
  "preferred_date": "2026-09-25",
  "preferred_time_slot": "09:00-12:00",
  "contact_phone": "+34612345678",
  "special_instructions": "string | null"
}
// Response 200
{
  "pickup_id": "PICKUP-2026-000001",
  "return_id": "RET-2026-000001",
  "scheduled_at": "2026-09-25T09:00:00Z",
  "pickup_address": {...},
  "contact_phone": "+34612345678",
  "tracking_number": "TRK-ABC123",
  "estimated_duration_minutes": 30,
  "status": "SCHEDULED"
}
```

### Control Tower / Dashboard Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/control-tower/kpis` | Get current KPI metrics |
| GET | `/control-tower/distribution` | Get destination distribution |
| GET | `/control-tower/alerts` | Get active alerts |
| POST | `/control-tower/alerts/{alert_id}/acknowledge` | Acknowledge an alert |
| GET | `/control-tower/returns` | Get paginated returns for table |
| GET | `/control-tower/realtime` | WebSocket endpoint for real-time updates |

**GET /control-tower/kpis**
```json
// Response 200
{
  "return_rate": 8.5,
  "cycle_time_hours": 4.2,
  "avg_recovery_cost": 12.50,
  "value_recovery_rate": 78.3,
  "total_returns_today": 127,
  "total_value_today": 15230.50,
  "return_rate_delta": -0.3,
  "cycle_time_delta": 0.2,
  "recovery_cost_delta": -1.2,
  "recovery_rate_delta": 2.1,
  "return_rate_history": [8.2, 8.4, 8.6, 8.5, 8.7, 8.5, 8.5],
  "cycle_time_history": [4.0, 4.1, 4.3, 4.2, 4.1, 4.2, 4.2],
  "recovery_cost_history": [13.5, 13.2, 12.8, 13.0, 12.7, 12.6, 12.5],
  "recovery_rate_history": [75.0, 76.2, 77.0, 77.5, 78.0, 78.1, 78.3]
}
```

**GET /control-tower/distribution**
```json
// Response 200
{
  "CARRIL_RAPIDO": 35.5,
  "OUTLET": 22.3,
  "RECICLAJE": 15.8,
  "KEEP_IT": 18.2,
  "INSPECCION_B2B": 8.2,
  "total": 100.0
}
```

**GET /control-tower/alerts**
```json
// Query Parameters
{
  "priority": "CRITICAL | HIGH | MEDIUM | LOW | null",
  "acknowledged": "true | false | null",
  "limit": 50
}
// Response 200
{
  "alerts": [
    {
      "alert_id": "ALT-2026-000001",
      "trace_id": "uuid",
      "type": "INSPECTION_SATURATION",
      "priority": "HIGH",
      "title": "Saturación en zona de inspección",
      "message": "Capacidad al 95% en центр Madrid Norte. 23 retornos en cola.",
      "source": "WAREHOUSE-MAD-N",
      "related_return_id": "RET-2026-000123",
      "related_batch_id": null,
      "created_at": "2026-09-23T15:30:00Z",
      "acknowledged_at": null,
      "acknowledged_by": null,
      "resolved_at": null
    }
  ],
  "total": 15,
  "unacknowledged_count": 3
}
```

### KAM Approval Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/kam/pending-approvals` | Get batch returns awaiting KAM approval |
| POST | `/kam/approvals/{approval_id}` | Approve a pending batch |
| POST | `/kam/rejections/{approval_id}` | Reject a pending batch |
| GET | `/kam/approval-history` | Get KAM approval history |

**POST /kam/approvals/{approval_id}**
```json
// Request
{
  "comments": "Aprobado tras revisión de calidad",
  "conditions": ["Inspección obligatoria al recibir"]
}
// Response 200
{
  "approval_id": "APR-2026-000001",
  "return_id": "RET-2026-000456",
  "approved_by": "KAM-123",
  "approved_at": "2026-09-23T16:00:00Z",
  "comments": "Aprobado tras revisión de calidad",
  "conditions": ["Inspección obligatoria al recibir"]
}
```

### Export and Report Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/reports/generate` | Generate a report (PDF/HTML/CSV) |
| GET | `/reports/{report_id}` | Get report download URL |
| GET | `/reports` | List generated reports |

**POST /reports/generate**
```json
// Request
{
  "format": "PDF | HTML | CSV",
  "filters": {
    "date_from": "2026-09-01T00:00:00Z",
    "date_to": "2026-09-23T23:59:59Z",
    "channel": "B2B",
    "destination": null,
    "status": null,
    "customer_id": null,
    "alert_priority": null
  },
  "include_kpis": true,
  "include_alerts": true,
  "include_returns": true,
  "requested_by": "supervisor@company.com"
}
// Response 202
{
  "report_id": "RPT-2026-000001",
  "status": "GENERATING",
  "estimated_completion_seconds": 30
}
```

### Admin Configuration Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/admin/scoring-weights` | Get current scoring weights |
| PUT | `/admin/scoring-weights` | Update scoring weights |
| GET | `/admin/prompts` | List all prompt versions |
| POST | `/admin/prompts` | Create new prompt version |
| PUT | `/admin/prompts/{version}/activate` | Activate a prompt version |
| GET | `/admin/config` | Get system configuration |
| PUT | `/admin/config` | Update system configuration |

### Health and Observability Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check endpoint |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |
| GET | `/metrics` | Prometheus metrics endpoint |
| GET | `/version` | Get service version info |

**GET /health**
```json
// Response 200
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-09-23T16:00:00Z",
  "dependencies": {
    "database": "healthy",
    "cache": "healthy"
  }
}
```

**GET /metrics** (Prometheus format)
```
# HELP returns_total Total number of returns processed
# TYPE returns_total counter
returns_total{channel="B2C"} 1234
returns_total{channel="B2B"} 567

# HELP return_processing_seconds Time taken to process a return
# TYPE return_processing_seconds histogram
return_processing_seconds_bucket{le="0.1"} 100
return_processing_seconds_bucket{le="0.5"} 450
return_processing_seconds_sum 234.5
return_processing_seconds_count 890

# HELP kpi_return_rate_current Current return rate percentage
# TYPE kpi_return_rate_current gauge
kpi_return_rate_current 8.5
```

---

## 4. FILE STRUCTURE

```
sistema-logistica-inversa/
├── backend/
│   ├── main.py                           # FastAPI application entry point
│   ├── requirements.txt                  # Python dependencies
│   ├── config.py                        # Application configuration
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── models.py                     # All Pydantic models (see §2)
│   │   ├── database.py                   # Database connection and session
│   │   ├── redis.py                      # Redis client
│   │   ├── tracing.py                    # Distributed tracing utilities
│   │   ├── logging_config.py             # Structured logging setup
│   │   └── exceptions.py                 # Custom exceptions
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                       # API dependencies (auth, db session)
│   │   ├── router.py                     # Main API router
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   └── service.py
│   │   ├── returns/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── decision/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   ├── engine.py                  # Core decision engine
│   │   │   └── rules.py                   # Business rules
│   │   ├── batches/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   ├── service.py
│   │   │   └── parser.py                  # CSV parsing
│   │   ├── dropoff/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   └── service.py
│   │   ├── pickup/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   └── service.py
│   │   ├── control_tower/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   └── service.py
│   │   ├── kam/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   └── service.py
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   ├── generator.py               # PDF/HTML/CSV generation
│   │   │   └── templates/                  # Jinja2 templates
│   │   │       ├── report.html.j2
│   │   │       └── email_notification.html.j2
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints.py
│   │   │   └── service.py
│   │   └── observability/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── metrics.py                 # Prometheus metrics
│   │       └── health.py                  # Health check handlers
│   └── services/
│       ├── __init__.py
│       ├── qr_service.py                  # QR code generation
│       ├── notification_service.py        # Email notifications
│       └── kpi_service.py                 # KPI calculations
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.tsx                       # React entry point
│       ├── App.tsx                        # Root component with routing
│       ├── index.css                      # Global styles and Tailwind imports
│       ├── types/
│       │   └── models.ts                  # TypeScript interfaces (see §2)
│       ├── styles/
│       │   └── tokens.ts                  # Design tokens (see §9)
│       ├── api/
│       │   ├── client.ts                  # Axios HTTP client
│       │   ├── auth.ts                    # Auth API functions
│       │   ├── returns.ts                 # Returns API functions
│       │   ├── decision.ts                # Decision engine API
│       │   ├── batches.ts                 # Batch upload API
│       │   ├── dropoff.ts                 # Drop-off API
│       │   ├── pickup.ts                 # Pickup API
│       │   ├── controlTower.ts            # Control tower API
│       │   ├── kam.ts                     # KAM approval API
│       │   └── reports.ts                 # Reports API
│       ├── stores/
│       │   ├── authStore.ts               # Authentication state (Zustand)
│       │   ├── returnsStore.ts           # Returns state
│       │   ├── controlTowerStore.ts      # KPI and alerts state
│       │   └── uiStore.ts                # UI state (modals, sidebar)
│       ├── hooks/
│       │   ├── useReturns.ts              # Returns data hook
│       │   ├── useControlTower.ts        # Control tower data hook
│       │   ├── useDecision.ts             # Decision engine hook
│       │   ├── useBatches.ts              # Batch processing hook
│       │   ├── useDropOff.ts              # Drop-off points hook
│       │   └── useAlerts.ts               # Alerts hook
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppLayout.tsx         # Main layout wrapper
│       │   │   └── PageContainer.tsx     # Page content wrapper
│       │   └── ui/
│       │       ├── AppNavigationHeader.tsx
│       │       ├── KPIStatCard.tsx
│       │       ├── StatusBadge.tsx
│       │       ├── DecisionOutcomeCard.tsx
│       │       ├── DataDensityTable.tsx
│       │       ├── BatchUploadZone.tsx
│       │       └── PrimaryButtonCTA.tsx
│       ├── pages/
│       │   ├── PortalHibrido.tsx          # Portal Híbrido de Solicitud de Devolución
│       │   ├── ModuloLogistico.tsx        # Módulo Logístico de Entrega y Recogida
│       │   └── TorreControl.tsx            # Torre de Control de Retornos y Supervisión
│       └── utils/
│           ├── formatters.ts              # Number, date, currency formatters
│           ├── validators.ts              # Form validation utilities
│           └── constants.ts               # App constants
├── docker-compose.yml                     # Container orchestration
├── backend/Dockerfile                     # Backend container
├── frontend/Dockerfile                    # Frontend container
├── .env.example                           # Environment variables template
├── .gitignore
└── README.md
```

### PORT TABLE

| Service | Listening Port | Path |
|---|---|---|
| backend | 21001 | backend/ |
| frontend | 21002 | frontend/ |
| PostgreSQL | 25432 | Host: 25432, Container: 5432 |
| Redis | 26379 | Host: 26379, Container: 6379 |

### SHARED MODULES

| Shared path | Imported by services |
|---|---|
| backend/shared/ | All backend services |

**CRITICAL**: Each service Dockerfile MUST include:
```dockerfile
COPY shared/ ./shared/
```

---

## 5. ENVIRONMENT VARIABLES

### Backend Environment Variables

| Variable | Type | Description | Example |
|---|---|---|---|
| `ENVIRONMENT` | string | Deployment environment | `development`, `production` |
| `DEBUG` | boolean | Enable debug mode | `true`, `false` |
| `SECRET_KEY` | string | JWT signing secret (min 32 chars) | `your-secret-key-here-min-32-chars` |
| `DATABASE_URL` | string | PostgreSQL connection string | `postgresql://user:pass@localhost:25432/logistica` |
| `REDIS_URL` | string | Redis connection string | `redis://localhost:26379/0` |
| `DATABASE_POOL_SIZE` | integer | Connection pool size | `10` |
| `LOG_LEVEL` | string | Logging level | `INFO`, `DEBUG`, `WARNING` |
| `LOG_FORMAT` | string | Log format type | `json`, `text` |

### Third-Party API Keys

| Variable | Type | Description | Example |
|---|---|---|---|
| `SMTP_HOST` | string | Email SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | integer | Email SMTP port | `587` |
| `SMTP_USER` | string | SMTP authentication username | `notifications@company.com` |
| `SMTP_PASSWORD` | string | SMTP authentication password | `smtp-password` |
| `SMTP_FROM` | string | From email address | `no-reply@logistica-inversa.com` |
| `MAPS_API_KEY` | string | Google Maps / geocoding API key | `AIzaSy...` |

### Feature Flags

| Variable | Type | Description | Default |
|---|---|---|---|
| `ENABLE_KAM_APPROVALS` | boolean | Enable KAM approval workflow | `true` |
| `ENABLE_BATCH_UPLOAD` | boolean | Enable CSV batch upload | `true` |
| `ENABLE_QR_GENERATION` | boolean | Enable QR code generation | `true` |
| `ENABLE_REPORTS` | boolean | Enable report generation | `true` |
| `DECISION_ENGINE_V2` | boolean | Use enhanced decision engine | `false` |

### Application Settings

| Variable | Type | Description | Default |
|---|---|---|---|
| `MAX_BATCH_SIZE` | integer | Maximum CSV rows per batch | `1000` |
| `MAX_UPLOAD_SIZE_MB` | integer | Maximum file upload size | `10` |
| `CORS_ORIGINS` | string | Allowed CORS origins (comma-separated) | `http://localhost:21002` |
| `SESSION_TIMEOUT_MINUTES` | integer | Session timeout | `60` |
| `REFRESH_TOKEN_EXPIRY_DAYS` | integer | Refresh token expiry | `7` |
| `QR_CODE_EXPIRY_HOURS` | integer | QR code validity period | `72` |
| `KAM_APPROVAL_TIMEOUT_HOURS` | integer | Auto-escalate KAM pending | `24` |
| `INSPECTION_SATURATION_THRESHOLD` | float | Alert threshold (0-1) | `0.85` |
| `RETURN_RATE_SPIKE_THRESHOLD` | float | Alert threshold percentage | `10.0` |
| `CYCLE_TIME_ALERT_HOURS` | float | Alert threshold hours | `24.0` |

### Tracing and Observability

| Variable | Type | Description | Example |
|---|---|---|---|
| `OTEL_SERVICE_NAME` | string | OpenTelemetry service name | `logistica-backend` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | string | OTLP collector endpoint | `http://localhost:4317` |
| `OTEL_ENABLED` | boolean | Enable distributed tracing | `false` |
| `PROMETHEUS_ENABLED` | boolean | Enable Prometheus metrics | `true` |

### Frontend Environment Variables

| Variable | Type | Description | Default |
|---|---|---|---|
| `VITE_API_BASE_URL` | string | Backend API base URL | `http://localhost:21001/api/v1` |
| `VITE_APP_NAME` | string | Application name | `Sistema Logística Inversa` |
| `VITE_APP_VERSION` | string | Application version | `1.0.0` |
| `VITE_ENVIRONMENT` | string | Environment | `development` |
| `VITE_ENABLE_MOCK_API` | boolean | Use mock API responses | `false` |
| `VITE_MAPBOX_TOKEN` | string | Mapbox token for drop-off map | `pk.ey...` |
| `VITE_REALM` | string | Keycloak realm | `logistica` |
| `VITE_CLIENT_ID` | string | Keycloak client ID | `logistica-frontend` |

---

## 6. IMPORT CONTRACTS

### Backend Shared Module

```python
# backend/shared/models.py exports
from shared.models import (
    # Enums
    ReturnChannel,
    ReturnDestination,
    ReturnStatus,
    ReturnMethod,
    AlertPriority,
    AlertType,
    # Core Models
    ReturnItem,
    ReturnRequestCreate,
    ReturnRequest,
    # Decision Models
    DecisionInput,
    DecisionResult,
    ScoringDimensions,
    # Batch Models
    BatchUploadRecord,
    BatchUploadResponse,
    BatchApprovalAction,
    # KPI Models
    KPIMetrics,
    DestinationDistribution,
    # Alert Models
    Alert,
    AlertAcknowledgement,
    # Tracking Models
    TrackingEvent,
    TrackingTimeline,
    # Drop-off Models
    DropOffPoint,
    NearestDropOffPointsRequest,
    # Report Models
    ReportFilters,
    ReportRequest,
    # Admin Models
    ScoringWeights,
    PromptConfig,
    # Utilities
    uuid4,
    datetime,
    Decimal,
    BaseModel,
    Field,
)

# backend/shared/database.py exports
from shared.database import (
    get_db,
    get_db_session,
    init_db,
    engine,
    Base,
    DatabaseSession,
)

# backend/shared/redis.py exports
from shared.redis import (
    get_redis,
    cache_get,
    cache_set,
    cache_delete,
    rate_limit,
)

# backend/shared/tracing.py exports
from shared.tracing import (
    setup_tracing,
    create_span,
    inject_trace_context,
    extract_trace_context,
    TraceContext,
)

# backend/shared/exceptions.py exports
from shared.exceptions import (
    LogisticaException,
    NotFoundException,
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
    RateLimitException,
    ExternalServiceException,
)
```

### Backend API Dependencies

```python
# backend/api/deps.py exports
from api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_supervisor,
    get_current_kam,
    get_current_admin,
    get_db,
    get_redis,
    rate_limit_dependency,
)
```

### Backend Services

```python
# backend/services/qr_service.py exports
from services.qr_service import (
    generate_qr_code,
    generate_return_label,
    QRService,
)

# backend/services/notification_service.py exports
from services.notification_service import (
    NotificationService,
    send_return_confirmation,
    send_kam_approval_request,
    send_pickup_confirmation,
    send_alert_notification,
)

# backend/services/kpi_service.py exports
from services.kpi_service import (
    KPIService,
    calculate_kpis,
    calculate_destination_distribution,
)
```

### Frontend API Client

```typescript
// frontend/src/api/client.ts exports
export { apiClient, createApiClient } from './client';
export type { ApiClient } from './client';
```

### Frontend Store Exports

```typescript
// frontend/src/stores/authStore.ts exports
export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: false,
  login: async (credentials) => {...},
  logout: () => {...},
  refreshToken: async () => {...},
  setUser: (user) => {...},
}));
export type { AuthState, User };

// frontend/src/stores/returnsStore.ts exports
export const useReturnsStore = create<ReturnsState>((set, get) => ({
  returns: [],
  currentReturn: null,
  isLoading: false,
  error: null,
  pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 },
  fetchReturns: async (filters) => {...},
  fetchReturnById: async (returnId) => {...},
  createReturn: async (data) => {...},
  updateReturn: async (returnId, data) => {...},
  setCurrentReturn: (ret) => {...},
}));
export type { ReturnsState };

// frontend/src/stores/controlTowerStore.ts exports
export const useControlTowerStore = create<ControlTowerState>((set, get) => ({
  kpis: null,
  distribution: null,
  alerts: [],
  unreadAlertCount: 0,
  isLoading: false,
  lastUpdated: null,
  fetchKPIs: async () => {...},
  fetchDistribution: async () => {...},
  fetchAlerts: async (filters) => {...},
  acknowledgeAlert: async (alertId) => {...},
  subscribeToRealtime: () => {...},
}));
export type { ControlTowerState };

// frontend/src/stores/uiStore.ts exports
export const useUIStore = create<UIState>((set, get) => ({
  sidebarOpen: true,
  activeModal: null,
  notifications: [],
  theme: 'light',
  setSidebarOpen: (open) => {...},
  openModal: (modalId, data) => {...},
  closeModal: () => {...},
  addNotification: (notification) => {...},
  markNotificationRead: (id) => {...},
  setTheme: (theme) => {...},
}));
export type { UIState };
```

### Frontend Hook Exports

```typescript
// All hooks return exact property names as specified
export function useReturns(): {
  returns: ReturnRequest[];
  loading: boolean;
  error: string | null;
  pagination: { page: number; pageSize: number; total: number; totalPages: number };
  createReturn: (data: ReturnRequestCreate) => Promise<ReturnRequest>;
  fetchReturn: (returnId: string) => Promise<ReturnRequest>;
  updateReturn: (returnId: string, data: Partial<ReturnRequest>) => Promise<ReturnRequest>;
};

export function useControlTower(): {
  kpis: KPIMetrics | null;
  distribution: DestinationDistribution | null;
  loading: boolean;
  refreshKPIs: () => Promise<void>;
  refreshDistribution: () => Promise<void>;
};

export function useDecision(): {
  evaluate: (input: DecisionInput) => Promise<DecisionResult>;
  explanation: string | null;
  loading: boolean;
};

export function useBatches(): {
  uploadBatch: (file: File, customerId: string, reason: string) => Promise<BatchUploadResponse>;
  batch: BatchUploadResponse | null;
  validationErrors: BatchUploadRecord[];
  loading: boolean;
  reset: () => void;
};

export function useDropOff(): {
  points: DropOffPoint[];
  nearestPoint: DropOffPoint | null;
  fetchNearest: (lat: number, lng: number) => Promise<void>;
  loading: boolean;
};

export function useAlerts(): {
  alerts: Alert[];
  unreadCount: number;
  acknowledge: (alertId: string) => Promise<void>;
  fetchAlerts: (filters?: AlertFilters) => Promise<void>;
  loading: boolean;
};
```

---

## 7. FRONTEND STATE & COMPONENT CONTRACTS

### React Hooks (Zustand Stores)

**useAuthStore() →**
```typescript
{
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User) => void;
}
```

**useReturnsStore() →**
```typescript
{
  returns: ReturnRequest[];
  currentReturn: ReturnRequest | null;
  isLoading: boolean;
  error: string | null;
  pagination: { page: number; pageSize: number; total: number; totalPages: number };
  fetchReturns: (filters?: ReturnsFilters) => Promise<void>;
  fetchReturnById: (returnId: string) => Promise<ReturnRequest>;
  createReturn: (data: ReturnRequestCreate) => Promise<ReturnRequest>;
  updateReturn: (returnId: string, data: Partial<ReturnRequest>) => Promise<ReturnRequest>;
  setCurrentReturn: (ret: ReturnRequest | null) => void;
}
```

**useControlTowerStore() →**
```typescript
{
  kpis: KPIMetrics | null;
  distribution: DestinationDistribution | null;
  alerts: Alert[];
  unreadAlertCount: number;
  isLoading: boolean;
  lastUpdated: string | null;
  fetchKPIs: () => Promise<void>;
  fetchDistribution: () => Promise<void>;
  fetchAlerts: (filters?: AlertFilters) => Promise<void>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  subscribeToRealtime: () => void;
}
```

**useUIStore() →**
```typescript
{
  sidebarOpen: boolean;
  activeModal: string | null;
  modalData: unknown;
  notifications: NotificationItem[];
  theme: 'light' | 'dark';
  setSidebarOpen: (open: boolean) => void;
  openModal: (modalId: string, data?: unknown) => void;
  closeModal: () => void;
  addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp'>) => void;
  markNotificationRead: (id: string) => void;
  setTheme: (theme: 'light' | 'dark') => void;
}
```

### React Hooks (Custom)

**useReturns() →**
```typescript
{
  returns: ReturnRequest[];
  loading: boolean;
  error: string | null;
  pagination: { page: number; pageSize: number; total: number; totalPages: number };
  createReturn: (data: ReturnRequestCreate) => Promise<ReturnRequest>;
  fetchReturn: (returnId: string) => Promise<ReturnRequest>;
  updateReturn: (returnId: string, data: Partial<ReturnRequest>) => Promise<ReturnRequest>;
}
```

**useControlTower() →**
```typescript
{
  kpis: KPIMetrics | null;
  distribution: DestinationDistribution | null;
  loading: boolean;
  refreshKPIs: () => Promise<void>;
  refreshDistribution: () => Promise<void>;
}
```

**useDecision() →**
```typescript
{
  evaluate: (input: DecisionInput) => Promise<DecisionResult>;
  explanation: string | null;
  loading: boolean;
  result: DecisionResult | null;
}
```

**useBatches() →**
```typescript
{
  uploadBatch: (file: File, customerId: string, reason: string) => Promise<BatchUploadResponse>;
  batch: BatchUploadResponse | null;
  validationErrors: BatchUploadRecord[];
  loading: boolean;
  progress: number;
  reset: () => void;
}
```

**useDropOff() →**
```typescript
{
  points: DropOffPoint[];
  nearestPoint: DropOffPoint | null;
  fetchNearest: (lat: number, lng: number, maxWeight?: number, maxVolume?: number) => Promise<void>;
  loading: boolean;
  error: string | null;
}
```

**useAlerts() →**
```typescript
{
  alerts: Alert[];
  unreadCount: number;
  acknowledge: (alertId: string) => Promise<void>;
  fetchAlerts: (filters?: { priority?: AlertPriority; acknowledged?: boolean }) => Promise<void>;
  loading: boolean;
}
```

### Base Component Props Interfaces

**AppNavigationHeader props/inputs:**
```typescript
interface AppNavigationHeaderProps {
  brand: string;
  activePage: 'portal' | 'logistico' | 'torre';
  notificationCount: number;
  userRole: 'B2C_USER' | 'B2B_USER' | 'SUPERVISOR' | 'KAM' | 'ADMIN';
  onNavigate: (page: 'portal' | 'logistico' | 'torre') => void;
  onNotificationsClick: () => void;
}
```

**KPIStatCard props/inputs:**
```typescript
interface KPIStatCardProps {
  title: string;
  value: number | string;
  unit?: string;
  delta?: number;
  deltaLabel?: string;
  sparklineData?: number[];
  sparklineColor?: 'positive' | 'negative' | 'neutral';
  loading?: boolean;
}
```

**StatusBadge props/inputs:**
```typescript
interface StatusBadgeProps {
  status: ReturnStatus | ReturnDestination | AlertPriority;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}
```

**DecisionOutcomeCard props/inputs:**
```typescript
interface DecisionOutcomeCardProps {
  destination: ReturnDestination;
  returnMethod: ReturnMethod;
  score: number;
  explanation: string;
  estimatedRefund?: number;
  creditNoteValue?: number;
  requiresKamApproval?: boolean;
  onViewDetails?: () => void;
  onSchedulePickup?: () => void;
}
```

**DataDensityTable props/inputs:**
```typescript
interface DataDensityTableProps {
  columns: Array<{
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
    align?: 'left' | 'center' | 'right';
  }>;
  data: ReturnRequest[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
  };
  filters?: {
    status?: ReturnStatus[];
    destination?: ReturnDestination[];
    channel?: ReturnChannel[];
    onFilterChange: (filters: Record<string, string[]>) => void;
  };
  onRowClick?: (row: ReturnRequest) => void;
  onBulkAction?: (ids: string[], action: string) => void;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
}
```

**BatchUploadZone props/inputs:**
```typescript
interface BatchUploadZoneProps {
  customerId: string;
  returnReason: string;
  onUploadComplete: (response: BatchUploadResponse) => void;
  onUploadError: (error: string) => void;
  maxFileSizeMB?: number;
  acceptedFormats?: string[];
  loading?: boolean;
}
```

**PrimaryButtonCTA props/inputs:**
```typescript
interface PrimaryButtonCTAProps {
  variant: 'solid' | 'outline' | 'danger' | 'subtle';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
  onClick: () => void;
  children: ReactNode;
}
```

---

## 8. FILE EXTENSION CONVENTION

**TypeScript Project** — All frontend files use `.tsx` (React) or `.ts` extension.

| File Type | Extension | Location |
|---|---|---|
| React entry | `.tsx` | `frontend/src/main.tsx` |
| App root | `.tsx` | `frontend/src/App.tsx` |
| Page components | `.tsx` | `frontend/src/pages/*.tsx` |
| UI components | `.tsx` | `frontend/src/components/ui/*.tsx` |
| Layout components | `.tsx` | `frontend/src/components/layout/*.tsx` |
| Hooks | `.ts` | `frontend/src/hooks/*.ts` |
| Stores | `.ts` | `frontend/src/stores/*.ts` |
| API clients | `.ts` | `frontend/src/api/*.ts` |
| Types/Interfaces | `.ts` | `frontend/src/types/*.ts` |
| Utilities | `.ts` | `frontend/src/utils/*.ts` |
| Styles | `.ts` | `frontend/src/styles/*.ts` |
| Config | `.ts` | `frontend/vite.config.ts`, `tsconfig.json` |
| CSS | `.css` | `frontend/src/index.css` |

**Entry point path**: `/src/main.tsx` (referenced in `index.html` as `<script type="module" src="/src/main.tsx"></script>`)

---

## 9. DESIGN TOKENS

```typescript
// frontend/src/styles/tokens.ts

export const tokens = {
  colors: {
    // Primary palette - Professional neutral
    primary: '#1E40AF',           // Deep blue - primary actions
    primaryLight: '#3B82F6',       // Lighter blue - hover states
    primaryDark: '#1E3A8A',        // Darker blue - active states
    
    // Semantic status colors
    success: '#059669',           // Emerald green - éxito
    successLight: '#10B981',       // Lighter emerald
    successDark: '#047857',        // Darker emerald
    
    warning: '#D97706',            // Amber - alertas
    warningLight: '#F59E0B',        // Lighter amber
    warningDark: '#B45309',         // Darker amber
    
    danger: '#DC2626',             // Carmine - crítico
    dangerLight: '#EF4444',        // Lighter carmine
    dangerDark: '#B91C1C',         // Darker carmine
    
    // Neutral palette
    gray50: '#F9FAFB',             // Page background light
    gray100: '#F3F4F6',            // Card backgrounds
    gray200: '#E5E7EB',            // Borders light
    gray300: '#D1D5DB',            // Borders medium
    gray400: '#9CA3AF',            // Disabled text
    gray500: '#6B7280',            // Secondary text
    gray600: '#4B5563',            // Body text
    gray700: '#374151',            // Headings dark
    gray800: '#1F2937',            // Dark backgrounds
    gray900: '#111827',            // Darkest backgrounds
    
    // Dark theme backgrounds (from Figma specs)
    darkNavy: '#0E1729',           // Navigation dark variant
    darkNavyAlt: '#0E1829',        // Alternative dark
    darkBlue: '#102A43',           // Deep blue dark
    charcoal: '#17212E',           // Header backgrounds
    
    // Page backgrounds (from Figma specs)
    pageBackground: '#F5F7FA',     // Default page
    pageBackgroundAlt: '#F6F8FA',  // Alternative page
    pageBackgroundDark: '#F2F6FA', // Control tower
    
    // White
    white: '#FFFFFF',
    
    // Black
    black: '#000000',
  },
  
  typography: {
    // Font families
    fontFamily: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      mono: "'JetBrains Mono', 'Fira Code', 'SF Mono', Monaco, monospace",
    },
    
    // Font sizes
    fontSize: {
      xs: '0.6875rem',            // 11px - Meta
      sm: '0.75rem',              // 12px
      base: '0.875rem',           // 14px - Body
      lg: '1rem',                 // 16px
      xl: '1.125rem',             // 18px
      '2xl': '1.25rem',           // 20px - Heading
      '3xl': '1.5rem',            // 24px
      '4xl': '1.875rem',          // 30px - Display
      '5xl': '2.25rem',           // 36px
      '6xl': '3rem',              // 48px
    },
    
    // Font weights
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    
    // Line heights
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
    
    // Letter spacing
    letterSpacing: {
      tight: '-0.025em',
      normal: '0',
      wide: '0.025em',
      wider: '0.05em',
    },
  },
  
  spacing: {
    // Base unit: 4px
    0: '0',
    0.5: '0.125rem',              // 2px
    1: '0.25rem',                 // 4px
    1.5: '0.375rem',              // 6px
    2: '0.5rem',                  // 8px
    2.5: '0.625rem',              // 10px
    3: '0.75rem',                 // 12px
    3.5: '0.875rem',              // 14px
    4: '1rem',                    // 16px
    5: '1.25rem',                 // 20px
    6: '1.5rem',                  // 24px
    7: '1.75rem',                 // 28px
    8: '2rem',                    // 32px
    9: '2.25rem',                 // 36px
    10: '2.5rem',                 // 40px
    11: '2.75rem',                // 44px
    12: '3rem',                   // 48px
    14: '3.5rem',                 // 56px
    16: '4rem',                   // 64px
    20: '5rem',                   // 80px
    24: '6rem',                   // 96px
    28: '7rem',                   // 112px
    32: '8rem',                   // 128px
    
    // Semantic spacing
    sectionPadding: '1.5rem',     // 24px
    cardPadding: '1rem',          // 16px
    inputPadding: '0.625rem',     // 10px
  },
  
  borderRadius: {
    none: '0',
    sm: '0.125rem',               // 2px - sharp containers
    DEFAULT: '0.25rem',           // 4px
    md: '0.375rem',               // 6px
    lg: '0.5rem',                 // 8px
    xl: '0.75rem',                // 12px
    '2xl': '1rem',                // 16px
    '3xl': '1.5rem',              // 24px
    full: '9999px',              // Pill buttons
  },
  
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: 'none',
    
    // Semantic shadows
    card: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    cardHover: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    modal: '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  },
  
  transitions: {
    duration: {
      fast: '150ms',
      DEFAULT: '200ms',
      slow: '300ms',
      slower: '500ms',
    },
    easing: {
      DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },
  
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
    toast: 1080,
  },
  
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1440px',
    '3xl': '1536px',
  },
};

// Semantic token aliases for common use cases
export const semanticTokens = {
  // Page background
  pageBg: tokens.colors.pageBackground,
  pageBgAlt: tokens.colors.pageBackgroundAlt,
  pageBgDark: tokens.colors.pageBackgroundDark,
  
  // Card styles
  cardBg: tokens.colors.white,
  cardBorder: tokens.colors.gray200,
  cardShadow: tokens.shadows.card,
  
  // Navigation
  navBg: tokens.colors.darkNavy,
  navBgAlt: tokens.colors.charcoal,
  navText: tokens.colors.white,
  navTextMuted: tokens.colors.gray400,
  
  // Text colors
  textPrimary: tokens.colors.gray900,
  textSecondary: tokens.colors.gray600,
  textMuted: tokens.colors.gray500,
  textDisabled: tokens.colors.gray400,
  textInverse: tokens.colors.white,
  
  // Border colors
  borderDefault: tokens.colors.gray200,
  borderStrong: tokens.colors.gray300,
  borderFocus: tokens.colors.primary,
  
  // Status colors (traffic light)
  statusGreen: tokens.colors.success,    // >= 80 score
  statusYellow: tokens.colors.warning,  // 50-79 score
  statusRed: tokens.colors.danger,      // < 50 score
  
  // Destination colors
  destinationCarrilRapido: '#2563EB',    // Blue
  destinationOutlet: '#7C3AED',         // Purple
  destinationReciclaje: '#059669',      // Green
  destinationKeepIt: '#0D9488',         // Teal
  destinationInspeccion: '#D97706',     // Amber
};

export default tokens;
```

---

## 10. FUNCTIONAL REQUIREMENTS COVERAGE

| Requirement | Implementation | Files |
|---|---|---|
| **Portal Híbrido B2C/B2B** | React page with profile selector, return form, batch upload zone, decision display, and financial summary | `frontend/src/pages/PortalHibrido.tsx` |
| **B2C Individual Return Request** | Form with customer ID, order reference, items, return reason, contact info; POST to `/returns` | `frontend/src/pages/PortalHibrido.tsx`, `backend/api/returns/endpoints.py` |
| **B2B Batch CSV Upload** | Drag-and-drop CSV upload zone with validation; POST to `/batches/upload` | `frontend/src/components/ui/BatchUploadZone.tsx`, `backend/api/batches/endpoints.py` |
| **Profile Selector (B2C/B2B)** | UI toggle between consumer and wholesale flows; channel enum passed in API requests | `frontend/src/pages/PortalHibrido.tsx` |
| **Decision Engine (4 Rules)** | Sequential rule evaluation: value threshold → condition → reason → KAM approval | `backend/api/decision/engine.py`, `backend/api/decision/rules.py` |
| **Decision Score 0-100** | relevance+urgency+impact each 0-33, sum = overall_score 0-100 | `backend/shared/models.py` (ScoringDimensions), `backend/api/decision/engine.py` |
| **Traffic Light Semaphore** | score>=80→green, 50-79→yellow, <50→red CSS classes from tokens | `frontend/src/components/ui/StatusBadge.tsx`, `frontend/src/styles/tokens.ts` |
| **Destination: Carril Rápido** | Fast lane to immediate restocking; business rule: high value, new condition | `backend/api/decision/rules.py` |
| **Destination: Outlet** | Resale at reduced price; business rule: good condition, medium value | `backend/api/decision/rules.py` |
| **Destination: Reciclaje** | Textile recycling; business rule: damaged, low value | `backend/api/decision/rules.py` |
| **Destination: Keep It** | Keep at customer; business rule: very low value, convenience return | `backend/api/decision/rules.py` |
| **Destination: Inspección B2B** | Incident inspection for B2B; business rule: B2B channel, requires KAM | `backend/api/decision/rules.py` |
| **Return Method: Drop-off QR** | Generate QR code for convenience drop-off points; GET `/dropoff/qr/{return_id}` | `frontend/src/pages/ModuloLogistico.tsx`, `backend/services/qr_service.py` |
| **Return Method: Pickup** | Schedule dedicated B2B transport; POST `/pickup/schedule` | `frontend/src/pages/ModuloLogistico.tsx`, `backend/api/pickup/endpoints.py` |
| **Drop-off Point Map** | Show nearest authorized points with distance; GET `/dropoff/points` | `frontend/src/pages/ModuloLogistico.tsx`, `backend/api/dropoff/endpoints.py` |
| **QR Code Generation** | Base64-encoded QR with return reference; python-qrcode + Pillow | `backend/services/qr_service.py` |
| **Packaging Guidelines** | Instructions for item preparation; GET `/dropoff/instructions/{return_id}` | `backend/api/dropoff/endpoints.py` |
| **Tracking Timeline** | Visual timeline of return status events; GET `/returns/{id}/tracking` | `frontend/src/pages/ModuloLogistico.tsx`, `backend/api/returns/endpoints.py` |
| **Torre de Control Dashboard** | React page with KPIs, distribution, alerts, KAM module, data table | `frontend/src/pages/TorreControl.tsx` |
| **KPI: Return Rate** | Percentage of returns vs orders; GET `/control-tower/kpis` | `backend/services/kpi_service.py` |
| **KPI: Cycle Time** | Average hours from request to processed; GET `/control-tower/kpis` | `backend/services/kpi_service.py` |
| **KPI: Average Recovery Cost** | Mean cost per return; GET `/control-tower/kpis` | `backend/services/kpi_service.py` |
| **KPI: Value Recovery Rate** | Percentage of value recovered; GET `/control-tower/kpis` | `backend/services/kpi_service.py` |
| **KPI Sparklines** | 7-day historical data in KPI cards; embedded in KPIMetrics response | `frontend/src/components/ui/KPIStatCard.tsx`, `backend/services/kpi_service.py` |
| **KPI Delta Indicators** | Trend arrows and percentage change; in KPIStatCard component | `frontend/src/components/ui/KPIStatCard.tsx` |
| **Destination Distribution Chart** | Horizontal bar chart showing % per destination; GET `/control-tower/distribution` | `frontend/src/pages/TorreControl.tsx`, `backend/api/control_tower/endpoints.py` |
| **Operational Alerts** | Priority-sorted alert list; GET `/control-tower/alerts` | `frontend/src/pages/TorreControl.tsx`, `backend/api/control_tower/endpoints.py` |
| **Alert Priority Levels** | LOW, MEDIUM, HIGH, CRITICAL with color coding | `backend/shared/models.py` (AlertPriority), `frontend/src/components/ui/StatusBadge.tsx` |
| **Alert Types** | INSPECTION_SATURATION, B2B_APPROVAL_PENDING, RETURN_RATE_SPIKE, etc. | `backend/shared/models.py` (AlertType) |
| **KAM Batch Approval Module** | Approve/reject pending B2B batches; GET `/kam/pending-approvals` | `frontend/src/pages/TorreControl.tsx`, `backend/api/kam/endpoints.py` |
| **DataDensityTable** | Paginated table with filters, sorting, bulk actions; GET `/control-tower/returns` | `frontend/src/components/ui/DataDensityTable.tsx`, `backend/api/control_tower/endpoints.py` |
| **Table Filters** | Filter by status, destination, channel, date range | `frontend/src/components/ui/DataDensityTable.tsx` |
| **Table Sorting** | Sort by any column (created_at, status, destination, total_value) | `frontend/src/components/ui/DataDensityTable.tsx` |
| **Bulk Actions** | Select multiple rows for bulk approve/reject; POST `/kam/approvals` | `frontend/src/components/ui/DataDensityTable.tsx` |
| **Financial Summary** | Estimated refund and credit note value display | `frontend/src/pages/PortalHibrido.tsx` |
| **Pre-approval Status** | Show if return is pre-approved or pending KAM review | `frontend/src/pages/PortalHibrido.tsx`, `backend/api/returns/endpoints.py` |
| **DecisionOutcomeCard** | Prominent card showing destination, method, score, instructions | `frontend/src/components/ui/DecisionOutcomeCard.tsx` |
| **Trace ID Generation** | UUID generated at ingestion, stored in ReturnRequest | `backend/shared/models.py` (trace_id field) |
| **Trace ID Propagation** | Distributed tracing via OpenTelemetry headers | `backend/shared/tracing.py` |
| **Prompt Version** | Audit field tracking which decision prompt was used | `backend/shared/models.py` (prompt_version field) |
| **Model Version** | Audit field tracking decision engine version | `backend/shared/models.py` (model_version field) |
| **Processing Time Audit** | Track decision engine processing time in ms | `backend/shared/models.py` (processing_time_ms field) |
| **Prometheus Metrics** | `/metrics` endpoint with Counter/Histogram/Gauge | `backend/api/observability/metrics.py` |
| **Health Checks** | `/health`, `/health/ready`, `/health/live` endpoints | `backend/api/observability/health.py` |
| **PDF Report Generation** | Generate PDF via WeasyPrint; POST `/reports/generate` | `backend/api/reports/generator.py` |
| **HTML Report Export** | Generate HTML via Jinja2; POST `/reports/generate` | `backend/api/reports/generator.py` |
| **CSV Report Export** | Generate CSV via pandas; POST `/reports/generate` | `backend/api/reports/generator.py` |
| **Admin: Scoring Weights** | GET/PUT `/admin/scoring-weights` | `backend/api/admin/endpoints.py` |
| **Admin: Prompt Management** | List, create, activate prompts; GET/POST `/admin/prompts` | `backend/api/admin/endpoints.py` |
| **JWT Authentication** | POST `/auth/login`, token-based auth for all protected endpoints | `backend/api/auth/endpoints.py` |
| **Role-based Access Control** | Roles: B2C_USER, B2B_USER, SUPERVISOR, KAM, ADMIN | `backend/api/deps.py` |
| **CORS Configuration** | Configurable origins via CORS_ORIGINS env var | `backend/main.py` |
| **Rate Limiting** | Redis-based rate limiting; configurable limits | `backend/shared/redis.py` |
| **Structured Logging** | JSON logs with structlog; trace_id in all logs | `backend/shared/logging_config.py` |
| **Notification Emails** | SMTP notifications for return confirmations, KAM requests | `backend/services/notification_service.py` |
| **Pickup Scheduling** | Time slot selection, address validation; GET `/pickup/slots` | `backend/api/pickup/endpoints.py` |
| **StatusBadge Component** | Semantic badge with color coding for all status/destination/priority | `frontend/src/components/ui/StatusBadge.tsx` |
| **KPIStatCard Component** | Metric display with sparkline, delta, loading state | `frontend/src/components/ui/KPIStatCard.tsx` |
| **AppNavigationHeader Component** | Navigation bar with role context, page links, notifications | `frontend/src/components/ui/AppNavigationHeader.tsx` |
| **PrimaryButtonCTA Component** | Action button with variants (solid, outline, danger, subtle) | `frontend/src/components/ui/PrimaryButtonCTA.tsx` |
| **Design Tokens** | Centralized token exports for all colors, typography, spacing | `frontend/src/styles/tokens.ts` |
| **12-Column Grid** | CSS grid layout for desktop, 4-column for mobile per responsive notes | `frontend/src/pages/*.tsx` |
| **CSV Validation** | Real-time validation of SKU, quantity, weight, volume, reason codes | `backend/api/batches/parser.py` |
| **Weight/Volume Limits** | Check against drop-off point capacity | `backend/api/dropoff/service.py` |
| **Batch Auto-escalation** | Auto-escalate KAM pending after configurable timeout | `backend/api/kam/service.py` |
| **Inspection Saturation Alert** | Trigger alert when inspection queue reaches threshold | `backend/services/kpi_service.py` |
| **Return Rate Spike Alert** | Trigger alert when return rate exceeds threshold | `backend/services/kpi_service.py` |
| **Cycle Time Exceeded Alert** | Trigger alert when average cycle time exceeds threshold | `backend/services/kpi_service.py` |

---

## 11. NON-FUNCTIONAL REQUIREMENTS

### Performance
- Return decision response time: < 500ms p95
- Page load time: < 2s initial load
- API response time: < 200ms p95 for cached endpoints
- Batch processing: 1000 records in < 30s
- QR code generation: < 100ms per code

### Scalability
- Support 100 concurrent users
- Handle 10,000 returns per day
- Database connection pool: 10 connections

### Security
- JWT tokens with 1-hour expiry
- Refresh tokens with 7-day expiry
- Password hashing: bcrypt with cost factor 12
- HTTPS required in production
- Input validation on all endpoints
- SQL injection prevention via ORM
- XSS prevention via React escaping

### Availability
- Health check endpoints for container orchestration
- Graceful shutdown handling
- Database connection retry logic
- Redis connection retry with backoff

### Compatibility
- Browser support: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Responsive breakpoints: 640px, 768px, 1024px, 1280px, 1440px

---

## 12. ASSUMPTIONS AND CONSTRAINTS

### Confirmed Assumptions
1. No ERP or WMS integrations in MVP scope
2. Business rules are predefined and fixed (no dynamic admin configuration)
3. Single PostgreSQL database instance
4. Single Redis instance for caching and rate limiting
5. Email notifications via SMTP (no third-party email service)

### Constraints
1. No mobile app; web-only platform
2. No offline support
3. No real-time WebSocket for MVP (polling-based updates)
4. PDF generation server-side only
5. Map integration uses Mapbox (Google Maps optional)

---

*Specification Version: 1.0.0*  
*Generated for: Sistema Inteligente de Logística Inversa*  
*Project ID: a1f531ec-0bee-42c5-b6c2-0eae037a17ec*