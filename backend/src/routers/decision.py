# backend/src/routers/decision.py

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.schemas import (
    UserSchema,
    DecisionInputSchema,
    DecisionResultSchema,
)
from src.routers.auth import get_current_active_user
from src.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/evaluate", response_model=DecisionResultSchema)
async def evaluate_decision(
    decision_input: DecisionInputSchema,
    current_user: UserSchema = Depends(get_current_active_user),
):
    start_time = time.time()

    items_data = []
    for item in decision_input.items:
        if hasattr(item, "model_dump"):
            items_data.append(item.model_dump())
        else:
            items_data.append({
                "sku": item.sku,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "weight_kg": float(item.weight_kg) if item.weight_kg else None,
                "volume_m3": float(item.volume_m3) if item.volume_m3 else None,
                "reason_code": item.reason_code,
                "reason_description": item.reason_description,
                "condition": item.condition,
                "batch_id": item.batch_id,
                "is_customized": getattr(item, "is_customized", False),
            })

    decision = decision_engine.evaluate(
        channel=decision_input.channel,
        customer_type=decision_input.customer_type,
        items=items_data,
        total_items=decision_input.item_count,
        total_value=decision_input.total_value,
        total_weight_kg=decision_input.total_weight_kg,
        total_volume_m3=decision_input.total_volume_m3,
        return_reason=decision_input.return_reason,
        has_kam_approval=decision_input.has_kam_approval,
    )

    processing_time = int((time.time() - start_time) * 1000)

    return DecisionResultSchema(
        destination=decision.destination,
        return_method=decision.return_method,
        score=decision.score,
        confidence=decision.confidence,
        explanation=decision.explanation,
        factors=decision.factors,
        business_rule_applied=decision.business_rule_applied,
        requires_kam_approval=decision.requires_kam_approval,
        processing_time_ms=processing_time,
    )


@router.get("/explain/{return_id}")
async def explain_decision(
    return_id: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    from src.db.database import SessionLocal
    db = SessionLocal()
    try:
        query = text("""
            SELECT return_id, trace_id, channel, customer_id, customer_type,
                   items, total_items, total_value, total_weight_kg,
                   total_volume_m3, return_reason, status, destination,
                   method, decision_score, decision_explanation,
                   requires_kam_approval, business_rule_applied,
                   processing_time_ms, created_at
            FROM returns
            WHERE return_id = :return_id
        """)

        result = db.execute(query, {"return_id": return_id}).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devolucion {return_id} no encontrada"
            )

        items_data = result[5] if isinstance(result[5], list) else []

        explanation = {
            "return_id": result[0],
            "trace_id": str(result[1]),
            "channel": result[2],
            "customer_type": result[4],
            "total_items": result[6],
            "total_value": float(result[7]) if result[7] else 0,
            "total_weight_kg": float(result[8]) if result[8] else 0,
            "return_reason": result[10],
            "status": result[11],
            "destination": result[12],
            "method": result[13],
            "decision_score": result[14],
            "decision_explanation": result[15],
            "requires_kam_approval": result[16],
            "business_rule_applied": result[17],
            "processing_time_ms": result[18],
            "created_at": result[19].isoformat() if result[19] else None,
            "rule_evaluation": [],
        }

        rules = decision_engine.get_available_rules()
        for rule in rules.get("rules", []):
            rule_evaluation = {
                "rule_id": rule["id"],
                "rule_description": rule["description"],
                "conditions": rule["conditions"],
                "applicable": False,
                "reason": "",
            }

            if rule["id"] == "B2C_STANDARD_DROP_OFF":
                if (result[2] == "B2C" and
                    result[6] <= 5 and
                    float(result[8] or 0) <= 15.0):
                    rule_evaluation["applicable"] = True
                    rule_evaluation["reason"] = " Cumple condiciones: B2C, <=5 articulos, <=15kg"
            elif rule["id"] == "B2C_EXCEEDS_DROP_OFF_LIMITS":
                if (result[2] == "B2C" and
                    (result[6] > 5 or float(result[8] or 0) > 15.0)):
                    rule_evaluation["applicable"] = True
                    rule_evaluation["reason"] = " Excede limites: >5 articulos o >15kg"
            elif rule["id"] == "KEEP_IT_COST_EXCEEDS_VALUE":
                if result[12] == "KEEP_IT":
                    rule_evaluation["applicable"] = True
                    rule_evaluation["reason"] = "Coste logistico supera el valor del producto"
            elif rule["id"] == "B2B_REQUIRES_KAM":
                if result[2] == "B2B" and not result[16]:
                    rule_evaluation["applicable"] = True
                    rule_evaluation["reason"] = "B2B sin aprobacion KAM"

            explanation["rule_evaluation"].append(rule_evaluation)

        return explanation
    finally:
        db.close()


@router.get("/rules")
async def get_decision_rules(
    current_user: UserSchema = Depends(get_current_active_user),
):
    rules = decision_engine.get_available_rules()
    return rules


@router.get("/scoring")
async def get_decision_scoring(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["SUPERVISOR", "KAM", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver la configuracion de scoring"
        )

    return {
        "scoring_dimensions": [
            {
                "name": "relevance",
                "description": "Relevancia del retorno para el negocio",
                "min_value": 0,
                "max_value": 33,
                "weight": 0.33,
            },
            {
                "name": "urgency",
                "description": "Urgencia del procesamiento",
                "min_value": 0,
                "max_value": 33,
                "weight": 0.33,
            },
            {
                "name": "impact",
                "description": "Impacto en inventario y costos",
                "min_value": 0,
                "max_value": 34,
                "weight": 0.34,
            },
        ],
        "total_score_range": {
            "min": 0,
            "max": 100,
        },
        "score_interpretation": {
            "0-30": "Prioridad baja - Procesamiento standard",
            "31-60": "Prioridad media - Procesamiento acelerado",
            "61-80": "Prioridad alta - Requiere atencion",
            "81-100": "Prioridad critica - Accion inmediata",
        },
        "current_weights": {
            "distance_weight": 0.2,
            "weight_weight": 0.3,
            "value_weight": 0.25,
            "condition_weight": 0.15,
            "customization_weight": 0.1,
        },
    }
