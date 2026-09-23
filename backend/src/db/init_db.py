# backend/src/db/init_db.py

import asyncio
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.db.database import engine, Base, SessionLocal
from config import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE return_channel AS ENUM ('B2C', 'B2B');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE return_destination AS ENUM ('CARRIL_RAPIDO', 'OUTLET', 'RECICLAJE', 'KEEP_IT', 'INSPECCION_B2B');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE return_status AS ENUM ('PENDIENTE', 'APROBADO', 'PRE_APROBADO', 'RECHAZADO', 'EN_TRANSITO', 'ENTREGADO', 'INSPECCION', 'PROCESADO', 'EXCEPTION');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE return_method AS ENUM ('DROP_OFF', 'PICKUP', 'KEEP_IT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_type AS ENUM ('INSPECTION_SATURATION', 'B2B_APPROVAL_PENDING', 'RETURN_RATE_SPIKE', 'CYCLE_TIME_EXCEEDED', 'COST_THRESHOLD_BREACH');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('B2C_USER', 'B2B_USER', 'SUPERVISOR', 'KAM', 'ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Users table
CREATE TABLE IF NOT EXISTS users (
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

-- Returns table
CREATE TABLE IF NOT EXISTS returns (
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
    total_value DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_weight_kg DECIMAL(8, 3) NOT NULL DEFAULT 0.000,
    total_volume_m3 DECIMAL(8, 4) NOT NULL DEFAULT 0.0000,

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
    decision_score INTEGER CHECK (decision_score >= 0 AND decision_score <= 100),
    decision_explanation TEXT,

    estimated_reimbursement DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    credit_note_value DECIMAL(10, 2),
    pre_approval_status VARCHAR(20),

    qr_code TEXT,
    qr_code_expires_at TIMESTAMP WITH TIME ZONE,
    drop_off_point_id VARCHAR(50),

    scheduled_pickup_at TIMESTAMP WITH TIME ZONE,
    pickup_address_json JSONB,
    pickup_carrier VARCHAR(100),
    tracking_number VARCHAR(100),

    kam_approval_reference VARCHAR(100),
    kam_approver_id VARCHAR(100),
    kam_approval_at TIMESTAMP WITH TIME ZONE,
    kam_comments TEXT,

    requires_kam_approval BOOLEAN NOT NULL DEFAULT FALSE,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    rejection_reason VARCHAR(500),

    metadata JSONB,
    batch_id VARCHAR(50),

    created_by VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(20) DEFAULT 'v1.0.0',
    model_version VARCHAR(50) DEFAULT 'decision-engine-v1',
    processing_time_ms INTEGER,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Batch uploads table
CREATE TABLE IF NOT EXISTS batch_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,

    total_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    invalid_records INTEGER NOT NULL DEFAULT 0,

    records JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_value DECIMAL(12, 2) NOT NULL DEFAULT 0.00,

    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processing_time_ms INTEGER NOT NULL DEFAULT 0,

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    return_request_id UUID REFERENCES returns(id) ON DELETE SET NULL
);

-- KPI snapshots table
CREATE TABLE IF NOT EXISTS kpi_snapshots (
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

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
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

-- Drop-off points table
CREATE TABLE IF NOT EXISTS drop_off_points (
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

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_customer_id ON users(customer_id);

CREATE INDEX IF NOT EXISTS idx_returns_customer_id ON returns(customer_id);
CREATE INDEX IF NOT EXISTS idx_returns_status ON returns(status);
CREATE INDEX IF NOT EXISTS idx_returns_channel ON returns(channel);
CREATE INDEX IF NOT EXISTS idx_returns_created_at ON returns(created_at);
CREATE INDEX IF NOT EXISTS idx_returns_destination ON returns(destination);
CREATE INDEX IF NOT EXISTS idx_returns_return_id ON returns(return_id);
CREATE INDEX IF NOT EXISTS idx_returns_trace_id ON returns(trace_id);
CREATE INDEX IF NOT EXISTS idx_returns_batch_id ON returns(batch_id);

CREATE INDEX IF NOT EXISTS idx_batch_customer_id ON batch_uploads(customer_id);
CREATE INDEX IF NOT EXISTS idx_batch_batch_id ON batch_uploads(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_uploaded_at ON batch_uploads(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_batch_status ON batch_uploads(status);

CREATE INDEX IF NOT EXISTS idx_kpi_snapshot_created_at ON kpi_snapshots(created_at);

CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_drop_off_point_available ON drop_off_points(available);
CREATE INDEX IF NOT EXISTS idx_drop_off_point_location ON drop_off_points(latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_returns_updated_at ON returns;
CREATE TRIGGER update_returns_updated_at
    BEFORE UPDATE ON returns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_drop_off_point_updated_at ON drop_off_points;
CREATE TRIGGER update_drop_off_point_updated_at
    BEFORE UPDATE ON drop_off_points
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

SEED_USERS_SQL = """
INSERT INTO users (username, email, full_name, role, hashed_password, customer_id)
VALUES
    ('admin', 'admin@logistica.com', 'Administrador Sistema', 'ADMIN', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiiGTMwFYjGq', 'CUST-001'),
    ('supervisor1', 'supervisor@logistica.com', 'Juan Supervisor', 'SUPERVISOR', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiiGTMwFYjGq', 'CUST-001'),
    ('kam1', 'kam@logistica.com', 'Maria KAM', 'KAM', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiiGTMwFYjGq', 'CUST-002'),
    ('b2c_user1', 'cliente@ejemplo.com', 'Carlos Consumidor', 'B2C_USER', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiiGTMwFYjGq', 'CUST-003'),
    ('b2b_user1', 'compras@empresa.com', 'Empresa SL', 'B2B_USER', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiiGTMwFYjGq', 'CUST-004')
ON CONFLICT (username) DO NOTHING;
"""

SEED_DROP_OFF_POINTS_SQL = """
INSERT INTO drop_off_points (point_id, name, address, latitude, longitude, max_weight_kg, max_volume_m3, opening_hours, available)
VALUES
    ('DROP-001', 'Punto Drop-off Centro Comercial Madrid', '{"street": "Calle Gran Via 1", "city": "Madrid", "postal_code": "28013", "country": "ES"}', 40.417500, -3.702500, 20.000, 0.1000, 'L-V 09:00-21:00, S 10:00-14:00', true),
    ('DROP-002', 'Punto Drop-off Estacion Atocha', '{"street": "Plaza del Emperador Carlos V", "city": "Madrid", "postal_code": "28045", "country": "ES"}', 40.407186, -3.690806, 25.000, 0.1500, 'L-D 06:00-23:00', true),
    ('DROP-003', 'Punto Drop-off Barcelona Centro', '{"street": "Passeig de Gracia 100", "city": "Barcelona", "postal_code": "08008", "country": "ES"}', 41.392500, 2.164722, 20.000, 0.1000, 'L-S 09:00-21:00', true)
ON CONFLICT (point_id) DO NOTHING;
"""


def run_schema() -> None:
    with engine.connect() as conn:
        for statement in SCHEMA_SQL.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    logger.warning(f"Schema statement failed (may already exist): {e}")
        conn.commit()


def seed_data() -> None:
    with engine.connect() as conn:
        try:
            conn.execute(text(SEED_USERS_SQL))
            conn.commit()
            logger.info("Seed users created successfully")
        except Exception as e:
            logger.warning(f"Seed users failed: {e}")

        try:
            conn.execute(text(SEED_DROP_OFF_POINTS_SQL))
            conn.commit()
            logger.info("Seed drop-off points created successfully")
        except Exception as e:
            logger.warning(f"Seed drop-off points failed: {e}")


async def initialize_database() -> None:
    logger.info("Initializing database...")
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, run_schema)
        await loop.run_in_executor(_executor, seed_data)
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_database())
