export enum ReturnChannel {
  B2C = 'B2C',
  B2B = 'B2B',
}

export enum ReturnDestination {
  CARRIL_RAPIDO = 'CARRIL_RAPIDO',
  OUTLET = 'OUTLET',
  RECICLAJE = 'RECICLAJE',
  KEEP_IT = 'KEEP_IT',
  INSPECCION_B2B = 'INSPECCION_B2B',
}

export enum ReturnStatus {
  PENDIENTE = 'PENDIENTE',
  APROBADO = 'APROBADO',
  PRE_APROBADO = 'PRE_APROBADO',
  RECHAZADO = 'RECHAZADO',
  EN_TRANSITO = 'EN_TRANSITO',
  ENTREGADO = 'ENTREGADO',
  INSPECCION = 'INSPECCION',
  PROCESADO = 'PROCESADO',
  EXCEPTION = 'EXCEPTION',
}

export enum ReturnMethod {
  DROP_OFF = 'DROP_OFF',
  PICKUP = 'PICKUP',
  KEEP_IT = 'KEEP_IT',
}

export enum AlertPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export enum AlertType {
  INSPECTION_SATURATION = 'INSPECTION_SATURATION',
  B2B_APPROVAL_PENDING = 'B2B_APPROVAL_PENDING',
  RETURN_RATE_SPIKE = 'RETURN_RATE_SPIKE',
  CYCLE_TIME_EXCEEDED = 'CYCLE_TIME_EXCEEDED',
  COST_THRESHOLD_BREACH = 'COST_THRESHOLD_BREACH',
}

export enum UserRole {
  B2C_USER = 'B2C_USER',
  B2B_USER = 'B2B_USER',
  SUPERVISOR = 'SUPERVISOR',
  KAM = 'KAM',
  ADMIN = 'ADMIN',
}

export interface Address {
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
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
  is_customized: boolean;
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
  return_reason: string;
  return_reason_description?: string;
  pickup_address?: Address;
  preferred_drop_off_id?: string;
  preferred_time_slot?: string;
  contact_email: string;
  contact_phone?: string;
  status: ReturnStatus;
  destination?: ReturnDestination;
  method?: ReturnMethod;
  estimated_reimbursement: number;
  qr_code?: string;
  qr_code_expires_at?: string;
  pickup_scheduled_at?: string;
  pickup_carrier?: string;
  kam_approval_reference?: string;
  kam_approved_by?: string;
  kam_approved_at?: string;
  is_approved?: boolean;
  rejection_reason?: string;
  metadata?: Record<string, unknown>;
  batch_id?: string;
}

export interface DecisionInput {
  channel: ReturnChannel;
  customer_type: string;
  items: ReturnItem[];
  total_items: number;
  total_weight_kg?: number;
  total_volume_m3?: number;
  return_reason: string;
  is_batch: boolean;
  batch_id?: string;
}

export interface DecisionResult {
  destination: ReturnDestination;
  method: ReturnMethod;
  status: ReturnStatus;
  estimated_reimbursement: number;
  rule_applied: string;
  explanation: string;
  keep_it_reason?: string;
  inspection_required?: boolean;
  kam_approval_required?: boolean;
}

export interface KPIMetrics {
  return_rate: number;
  return_rate_delta: number;
  avg_cycle_time_hours: number;
  avg_cycle_time_delta: number;
  avg_recovery_cost: number;
  avg_recovery_cost_delta: number;
  value_recovery_rate: number;
  value_recovery_rate_delta: number;
  total_returns_today: number;
  total_returns_today_delta: number;
  inspection_queue_size: number;
  pickup_pending_count: number;
  kam_pending_count: number;
}

export interface DestinationDistribution {
  CARRIL_RAPIDO: number;
  OUTLET: number;
  RECICLAJE: number;
  KEEP_IT: number;
  INSPECCION_B2B: number;
}

export interface Alert {
  id: string;
  alert_id: string;
  type: AlertType;
  priority: AlertPriority;
  message: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  customer_id?: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthPayload {
  sub: string;
  user_id: string;
  username: string;
  role: UserRole;
  customer_id?: string;
  exp: number;
  iat: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface BatchUploadRecord {
  row_number: number;
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
  is_valid: boolean;
  validation_errors: string[];
}

export interface BatchUploadResponse {
  batch_id: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  records: BatchUploadRecord[];
  processing_time_ms: number;
  status: string;
}

export interface DropOffPoint {
  id: string;
  point_id: string;
  name: string;
  address: Address;
  latitude: number;
  longitude: number;
  max_weight_kg: number;
  max_volume_m3: number;
  opening_hours: string;
  available: boolean;
}

export interface TimeSlot {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
  available: boolean;
}

export interface PickupSchedulingRequest {
  return_id: string;
  selected_slot_id: string;
  pickup_address: Address;
  special_instructions?: string;
}

export interface NotificationItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  read: boolean;
  timestamp: string;
}

export interface ReturnsFilters {
  channel?: ReturnChannel;
  status?: ReturnStatus;
  destination?: ReturnDestination;
  customer_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface AlertFilters {
  priority?: AlertPriority;
  type?: AlertType;
  acknowledged?: boolean;
  date_from?: string;
  date_to?: string;
}
