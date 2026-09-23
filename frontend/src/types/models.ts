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

export interface DecisionInput {
  channel: ReturnChannel;
  customer_type: string;
  total_value: number;
  total_weight_kg: number;
  total_volume_m3: number;
  item_count: number;
  return_reason: string;
  has_kam_approval?: boolean;
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

export interface AlertAcknowledgement {
  alert_id: string;
  acknowledged_by: string;
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

export interface NearestDropOffPointsRequest {
  latitude: number;
  longitude: number;
  max_results?: number;
  max_weight_kg?: number;
  max_volume_m3?: number;
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

export interface User {
  user_id: string;
  username: string;
  role: "B2C_USER" | "B2B_USER" | "SUPERVISOR" | "KAM" | "ADMIN";
  permissions: string[];
  email?: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse extends TokenResponse {
  user: User;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReturnsFilters {
  page?: number;
  page_size?: number;
  channel?: ReturnChannel;
  status?: ReturnStatus;
  destination?: ReturnDestination;
  customer_id?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: "created_at" | "status" | "destination" | "total_value";
  sort_order?: "asc" | "desc";
}

export interface AlertFilters {
  priority?: AlertPriority;
  acknowledged?: boolean;
  limit?: number;
}

export interface PickupSlot {
  slot_id: string;
  date: string;
  time_slot: string;
  available: boolean;
}

export interface PickupScheduleRequest {
  return_id: string;
  pickup_address: Address;
  preferred_date: string;
  preferred_time_slot: string;
  contact_phone?: string;
  special_instructions?: string;
}

export interface PickupScheduleResponse {
  pickup_id: string;
  return_id: string;
  scheduled_at: string;
  pickup_address: Address;
  contact_phone?: string;
  tracking_number: string;
  estimated_duration_minutes: number;
  status: string;
}

export interface ScoringWeights {
  relevance: number;
  urgency: number;
  impact: number;
  value_threshold: number;
  weight_threshold_kg: number;
  volume_threshold_m3: number;
}

export interface KAMApprovalRequest {
  comments?: string;
  conditions?: string[];
}

export interface KAMApprovalResponse {
  approval_id: string;
  return_id: string;
  approved_by: string;
  approved_at: string;
  comments?: string;
  conditions?: string[];
}
