-- backend/src/db/schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE return_channel AS ENUM ('B2C', 'B2B');
CREATE TYPE return_destination AS ENUM ('CARRIL_RAPIDO', 'OUTLET', 'RECICLAJE', 'KEEP_IT', 'INSPECCION_B2B');
CREATE TYPE return_status AS ENUM ('PENDIENTE', 'APROBADO', 'PRE_APROBADO', 'RECHAZADO', 'EN_TRANSITO', 'ENTREGADO', 'INSPECCION', 'PROCESADO', 'EXCEPTION');
CREATE TYPE return_method AS ENUM ('DROP_OFF', 'PICKUP', 'KEEP_IT');
CREATE TYPE alert_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE alert_type AS ENUM ('INSPECTION_SATURATION', 'B2B_APPROVAL_PENDING', 'RETURN_RATE_SPIKE', 'CYCLE_TIME_EXCEEDED', 'COST_THRESHOLD_BREACH');
CREATE TYPE user_role AS ENUM ('B2C_USER', 'B2B_USER', 'SUPERVISOR', 'KAM', 'ADMIN');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'B2C_USER',
    customer_id VARCHAR(50),
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_customer_id ON users(customer_id);

-- Returns table
CREATE TABLE returns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    return_id VARCHAR(50) UNIQUE NOT NULL,
    trace_id UUID NOT NULL DEFAULT uuid_generate_v4(),

    channel return_channel NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    customer_type VARCHAR(50) NOT NULL,
    order_reference VARCHAR(100) NOT NULL,
    invoice_reference VARCHAR(100),

    items JSONB NOT NULL,
    total_items INTEGER NOT NULL CHECK (total_items >= 1),

    return_reason VARCHAR(20) NOT NULL,
    return_reason_description VARCHAR(500),

    pickup_address JSONB,
    preferred_drop_off_id VARCHAR(50),
    preferred_time_slot VARCHAR(50),

    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20),

    status return_status NOT NULL DEFAULT 'PENDIENTE',
    destination return_destination,
    method return_method,

    estimated_reimbursement DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    qr_code TEXT,
    qr_code_expires_at TIMESTAMP WITH TIME ZONE,

    pickup_scheduled_at TIMESTAMP WITH TIME ZONE,
    pickup_carrier VARCHAR(100),

    kam_approval_reference VARCHAR(100),
    kam_approved_by VARCHAR(100),
    kam_approved_at TIMESTAMP WITH TIME ZONE,

    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    rejection_reason VARCHAR(500),
    metadata JSONB,

    batch_id VARCHAR(50),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_returns_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_returns_customer_id ON returns(customer_id);
CREATE INDEX idx_returns_status ON returns(status);
CREATE INDEX idx_returns_channel ON returns(channel);
CREATE INDEX idx_returns_created_at ON returns(created_at);
CREATE INDEX idx_returns_destination ON returns(destination);
CREATE INDEX idx_returns_return_id ON returns(return_id);
CREATE INDEX idx_returns_trace_id ON returns(trace_id);
CREATE INDEX idx_returns_batch_id ON returns(batch_id);

-- Batch uploads table
CREATE TABLE batch_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,

    total_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    invalid_records INTEGER NOT NULL DEFAULT 0,

    records JSONB NOT NULL DEFAULT '[]'::jsonb,

    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processing_time_ms INTEGER NOT NULL DEFAULT 0,

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    return_request_id UUID REFERENCES returns(id) ON DELETE SET NULL,

    CONSTRAINT fk_batch_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_batch_customer_id ON batch_uploads(customer_id);
CREATE INDEX idx_batch_batch_id ON batch_uploads(batch_id);
CREATE INDEX idx_batch_uploaded_at ON batch_uploads(uploaded_at);
CREATE INDEX idx_batch_status ON batch_uploads(status);

-- KPI snapshots table
CREATE TABLE kpi_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id VARCHAR(50) UNIQUE NOT NULL,

    return_rate DECIMAL(5, 4) NOT NULL,
    return_rate_delta DECIMAL(5, 4) NOT NULL DEFAULT 0,

    avg_cycle_time_hours DECIMAL(10, 2) NOT NULL,
    avg_cycle_time_delta DECIMAL(10, 2) NOT NULL DEFAULT 0,

    avg_recovery_cost DECIMAL(10, 2) NOT NULL,
    avg_recovery_cost_delta DECIMAL(10, 2) NOT NULL DEFAULT 0,

    value_recovery_rate DECIMAL(5, 4) NOT NULL,
    value_recovery_rate_delta DECIMAL(5, 4) NOT NULL DEFAULT 0,

    total_returns_today INTEGER NOT NULL DEFAULT 0,
    total_returns_today_delta INTEGER NOT NULL DEFAULT 0,

    inspection_queue_size INTEGER NOT NULL DEFAULT 0,
    pickup_pending_count INTEGER NOT NULL DEFAULT 0,
    kam_pending_count INTEGER NOT NULL DEFAULT 0,

    destination_distribution JSONB NOT NULL DEFAULT '{"CARRIL_RAPIDO": 0, "OUTLET": 0, "RECICLAJE": 0, "KEEP_IT": 0, "INSPECCION_B2B": 0}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kpi_snapshot_created_at ON kpi_snapshots(created_at);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id VARCHAR(50) UNIQUE NOT NULL,

    type alert_type NOT NULL,
    priority alert_priority NOT NULL,
    message VARCHAR(500) NOT NULL,

    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,

    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_priority ON alerts(priority);
CREATE INDEX idx_alerts_type ON alerts(type);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);

-- Drop-off points table
CREATE TABLE drop_off_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    point_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,

    address JSONB NOT NULL,

    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,

    max_weight_kg DECIMAL(8, 3) NOT NULL,
    max_volume_m3 DECIMAL(8, 4) NOT NULL,

    opening_hours VARCHAR(100) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drop_off_point_available ON drop_off_points(available);
CREATE INDEX idx_drop_off_point_location ON drop_off_points(latitude, longitude);

-- Audit log table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(50) UNIQUE NOT NULL,

    event_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(50),
    actor_role user_role,

    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(50) NOT NULL,

    details JSONB,

    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_returns_updated_at
    BEFORE UPDATE ON returns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drop_off_point_updated_at
    BEFORE UPDATE ON drop_off_points
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Return tracking table
CREATE TABLE return_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracking_id VARCHAR(50) UNIQUE NOT NULL,
    return_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    location VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_return_tracking_return_id ON return_tracking(return_id);
CREATE INDEX idx_return_tracking_status ON return_tracking(status);
CREATE INDEX idx_return_tracking_created_at ON return_tracking(created_at);

-- Reports table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id VARCHAR(50) UNIQUE NOT NULL,
    format VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    file_path VARCHAR(500),
    filters JSONB,
    include_kpis BOOLEAN NOT NULL DEFAULT TRUE,
    include_alerts BOOLEAN NOT NULL DEFAULT FALSE,
    include_returns BOOLEAN NOT NULL DEFAULT TRUE,
    requested_by VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_reports_report_id ON reports(report_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_requested_by ON reports(requested_by);
CREATE INDEX idx_reports_created_at ON reports(created_at);
