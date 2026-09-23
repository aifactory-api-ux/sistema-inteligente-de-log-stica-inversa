# backend/migrations/seed_data.py

"""
Seed data module for database initialization
"""

from datetime import datetime
from decimal import Decimal
import uuid


def get_seed_drop_off_points():
    """Return seed data for drop-off points"""
    return [
        {
            "point_id": "DROP-001",
            "name": "Punto Drop-off Centro Comercial Gran Vía",
            "address": "Calle Gran Vía 1, 28013 Madrid",
            "latitude": Decimal("40.4175000"),
            "longitude": Decimal("-3.7025000"),
            "max_weight_kg": Decimal("20.000"),
            "max_volume_m3": Decimal("0.1000"),
            "available": True,
            "operating_hours": "L-V 09:00-21:00, S 10:00-14:00",
            "distance_km": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "point_id": "DROP-002",
            "name": "Punto Drop-off CC Sol",
            "address": "Calle del Arenal 9, 28013 Madrid",
            "latitude": Decimal("40.4150000"),
            "longitude": Decimal("-3.7038000"),
            "max_weight_kg": Decimal("15.000"),
            "max_volume_m3": Decimal("0.0800"),
            "available": True,
            "operating_hours": "L-V 09:30-20:00, S 10:00-14:00",
            "distance_km": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "point_id": "DROP-003",
            "name": "Punto Drop-off Tiendacallao",
            "address": "Plaza del Callao 3, 28013 Madrid",
            "latitude": Decimal("40.4198000"),
            "longitude": Decimal("-3.7058000"),
            "max_weight_kg": Decimal("25.000"),
            "max_volume_m3": Decimal("0.1200"),
            "available": True,
            "operating_hours": "L-S 10:00-22:00",
            "distance_km": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "point_id": "DROP-004",
            "name": "Punto Drop-off CC ABC Serrano",
            "address": "Calle Serrano 61, 28006 Madrid",
            "latitude": Decimal("40.4298000"),
            "longitude": Decimal("-3.6878000"),
            "max_weight_kg": Decimal("18.000"),
            "max_volume_m3": Decimal("0.0900"),
            "available": True,
            "operating_hours": "L-V 10:00-20:00, S 11:00-14:00",
            "distance_km": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "point_id": "DROP-005",
            "name": "Punto Drop-off punto pack",
            "address": "Calle Fuencarral 100, 28010 Madrid",
            "latitude": Decimal("40.4308000"),
            "longitude": Decimal("-3.6978000"),
            "max_weight_kg": Decimal("10.000"),
            "max_volume_m3": Decimal("0.0500"),
            "available": True,
            "operating_hours": "L-V 09:00-19:00",
            "distance_km": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    ]


def get_seed_users():
    """Return seed data for users with bcrypt hashed passwords"""
    import bcrypt

    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    return [
        {
            "user_id": "USR-001",
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": "ADMIN",
            "permissions": ["read", "write", "delete", "admin"],
            "email": "admin@logistica-inversa.com",
            "full_name": "Administrador Sistema",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login_at": None,
        },
        {
            "user_id": "USR-002",
            "username": "supervisor",
            "password_hash": hash_password("supervisor123"),
            "role": "SUPERVISOR",
            "permissions": ["read", "write", "approve"],
            "email": "supervisor@logistica-inversa.com",
            "full_name": "Supervisor de Operaciones",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login_at": None,
        },
        {
            "user_id": "USR-003",
            "username": "kam_madrid",
            "password_hash": hash_password("kam123"),
            "role": "KAM",
            "permissions": ["read", "write", "approve_b2b"],
            "email": "kam.madrid@logistica-inversa.com",
            "full_name": "Key Account Manager Madrid",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login_at": None,
        },
        {
            "user_id": "USR-004",
            "username": "b2c_user",
            "password_hash": hash_password("b2c123"),
            "role": "B2C_USER",
            "permissions": ["read", "write_own"],
            "email": "cliente.b2c@ejemplo.com",
            "full_name": "Cliente B2C Prueba",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login_at": None,
        },
        {
            "user_id": "USR-005",
            "username": "b2b_user",
            "password_hash": hash_password("b2b123"),
            "role": "B2B_USER",
            "permissions": ["read", "write_own", "batch_upload"],
            "email": "cliente.b2b@empresa.com",
            "full_name": "Empresa B2B Prueba",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login_at": None,
        },
    ]


def get_seed_scoring_weights():
    """Return default scoring weights"""
    return {
        "relevance": Decimal("1.0"),
        "urgency": Decimal("1.0"),
        "impact": Decimal("1.0"),
        "value_threshold": Decimal("50.00"),
        "weight_threshold_kg": Decimal("5.0"),
        "volume_threshold_m3": Decimal("0.05"),
        "updated_at": datetime.utcnow(),
        "updated_by": "system",
    }


def get_seed_prompt_config():
    """Return default prompt configuration"""
    return {
        "version": "v1.0.0",
        "prompt_text": """Eres el motor de decisión del Sistema Inteligente de Logística Inversa.
Tu objetivo es evaluar cada solicitud de devolución y asignar el destino óptimo.
Considera los siguientes factores:
1. Canal del cliente (B2C o B2B)
2. Valor total de la devolución
3. Peso y volumen
4. Estado del producto
5. Motivo de la devolución
6. Disponibilidad de aprobación KAM para B2B

Destinos posibles:
- CARRIL_RAPIDO: Para productos de alta valorización y condición óptima
- OUTLET: Para productos en buena condición pero menor valor
- RECICLAJE: Para productos dañados sin valor recuperable
- KEEP_IT: Para devoluciones de muy bajo valor donde el costo logístico supera el valor
- INSPECCION_B2B: Para productos B2B que requieren revisión de KAM""",
        "active": True,
        "created_at": datetime.utcnow(),
        "created_by": "system",
    }
