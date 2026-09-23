# backend/src/services/decision_engine.py

import time
import logging
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class DecisionOutput:
    destination: str
    return_method: str
    score: int
    confidence: float
    explanation: str
    factors: dict
    business_rule_applied: str
    requires_kam_approval: bool
    processing_time_ms: int
    status: str
    estimated_refund: Decimal
    keep_it_reason: Optional[str] = None


class DecisionEngine:
    def __init__(self):
        self.b2c_max_items_drop_off = settings.business_rules.B2C_MAX_ITEMS_DROP_OFF
        self.b2c_max_weight_kg = settings.business_rules.B2C_MAX_WEIGHT_DROP_OFF_KG
        self.b2b_lot_size_threshold = settings.business_rules.B2B_LOT_SIZE_THRESHOLD
        self.b2b_weight_threshold_kg = settings.business_rules.B2B_WEIGHT_THRESHOLD_KG
        self.keep_it_cost_ratio = settings.business_rules.KEEP_IT_COST_THRESHOLD_RATIO

    def evaluate(
        self,
        channel: str,
        customer_type: str,
        items: list,
        total_items: int,
        total_value: Decimal,
        total_weight_kg: Decimal,
        total_volume_m3: Decimal,
        return_reason: str,
        has_kam_approval: bool = False,
        is_batch: bool = False,
        batch_id: Optional[str] = None,
    ) -> DecisionOutput:
        start_time = time.time()

        item_count = total_items
        has_customized_items = any(
            item.get("is_customized", False) for item in items
        )
        has_defective_items = any(
            item.get("condition", "").upper() in ["DEFECTIVE", "DAMAGED"]
            for item in items
        )

        if channel == "B2B":
            return self._evaluate_b2b(
                items=items,
                total_items=total_items,
                total_value=total_value,
                total_weight_kg=total_weight_kg,
                return_reason=return_reason,
                has_kam_approval=has_kam_approval,
                has_customized_items=has_customized_items,
                is_batch=is_batch,
                start_time=start_time,
            )
        else:
            return self._evaluate_b2c(
                items=items,
                total_items=total_items,
                total_value=total_value,
                total_weight_kg=total_weight_kg,
                return_reason=return_reason,
                has_customized_items=has_customized_items,
                has_defective_items=has_defective_items,
                start_time=start_time,
            )

    def _evaluate_b2c(
        self,
        items: list,
        total_items: int,
        total_value: Decimal,
        total_weight_kg: Decimal,
        return_reason: str,
        has_customized_items: bool,
        has_defective_items: bool,
        start_time: float,
    ) -> DecisionOutput:
        if has_customized_items and has_defective_items:
            return DecisionOutput(
                destination="RECICLAJE",
                return_method="PICKUP",
                score=85,
                confidence=0.92,
                explanation="Articulo hipercustomizado con defecto. No apta para re-stock. Reciclaje textil obligatorio.",
                factors={
                    "customized_factor": 1.0,
                    "defect_factor": 0.8,
                    "value_factor": 0.3,
                },
                business_rule_applied="HYPERCUSTOMIZED_DEFECT_B2C",
                requires_kam_approval=False,
                status="PRE_APROBADO",
                estimated_refund=Decimal("0.00"),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        keep_it_decision = self._evaluate_keep_it(
            total_value=total_value,
            total_weight_kg=total_weight_kg,
            channel="B2C",
        )
        if keep_it_decision:
            return keep_it_decision

        if total_items > 5 or float(total_weight_kg) > 15.0:
            return DecisionOutput(
                destination="KEEP_IT",
                return_method="KEEP_IT",
                score=70,
                confidence=0.88,
                explanation="Volumen o peso exceden limites Drop-off. Cliente puede quedarse con el producto y recibir reembolso parcial.",
                factors={
                    "volume_factor": 0.9 if total_items > 5 else 0.5,
                    "weight_factor": 0.9 if float(total_weight_kg) > 15.0 else 0.5,
                },
                business_rule_applied="B2C_EXCEEDS_DROP_OFF_LIMITS",
                requires_kam_approval=False,
                status="PRE_APROBADO",
                estimated_refund=total_value,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        if total_items <= 5 and float(total_weight_kg) <= 15.0:
            return DecisionOutput(
                destination="CARRIL_RAPIDO",
                return_method="DROP_OFF",
                score=80,
                confidence=0.95,
                explanation="Devolucion B2C dentro de parametros. Asignada a Carril Rapido para re-stock inmediato.",
                factors={
                    "volume_factor": 0.4,
                    "weight_factor": 0.3,
                    "condition_factor": 0.9,
                },
                business_rule_applied="B2C_STANDARD_DROP_OFF",
                requires_kam_approval=False,
                status="PRE_APROBADO",
                estimated_refund=total_value,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        return DecisionOutput(
            destination="OUTLET",
            return_method="PICKUP",
            score=60,
            confidence=0.75,
            explanation="Devolucion B2C asignada a Outlet por temporada o condicion.",
            factors={
                "season_factor": 0.6,
                "condition_factor": 0.5,
            },
            business_rule_applied="B2C_DEFAULT_OUTLET",
            requires_kam_approval=False,
            status="PENDIENTE",
            estimated_refund=total_value * Decimal("0.7"),
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

    def _evaluate_b2b(
        self,
        items: list,
        total_items: int,
        total_value: Decimal,
        total_weight_kg: Decimal,
        return_reason: str,
        has_kam_approval: bool,
        has_customized_items: bool,
        is_batch: bool,
        start_time: float,
    ) -> DecisionOutput:
        if has_customized_items:
            return DecisionOutput(
                destination="INSPECCION_B2B",
                return_method="PICKUP",
                score=90,
                confidence=0.95,
                explanation="Articulo hipercustomizado B2B requiere inspeccion obligatoria. No re-stock directo.",
                factors={
                    "customized_factor": 1.0,
                    "inspection_factor": 0.9,
                },
                business_rule_applied="HYPERCUSTOMIZED_B2B_INSPECTION",
                requires_kam_approval=True,
                status="EXCEPTION",
                estimated_refund=Decimal("0.00"),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        if has_kam_approval:
            return DecisionOutput(
                destination="CARRIL_RAPIDO",
                return_method="PICKUP",
                score=85,
                confidence=0.93,
                explanation="Lote B2B aprobado por KAM. Pickup programado para recogida.",
                factors={
                    "kam_approval_factor": 1.0,
                    "value_factor": 0.7,
                },
                business_rule_applied="KAM_APPROVED_B2B",
                requires_kam_approval=False,
                status="APROBADO",
                estimated_refund=total_value,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        return DecisionOutput(
            destination="INSPECCION_B2B",
            return_method="PICKUP",
            score=75,
            confidence=0.85,
            explanation="Lote B2B requiere autorizacion KAM antes de programacion de recogida.",
            factors={
                "batch_factor": 0.8,
                "volume_factor": 0.6,
            },
            business_rule_applied="B2B_REQUIRES_KAM",
            requires_kam_approval=True,
            status="EXCEPTION",
            estimated_refund=total_value,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

    def _evaluate_keep_it(
        self,
        total_value: Decimal,
        total_weight_kg: Decimal,
        channel: str,
    ) -> Optional[DecisionOutput]:
        estimated_logistics_cost = self._estimate_logistics_cost(
            total_weight_kg=total_weight_kg,
            channel=channel,
        )

        if estimated_logistics_cost > total_value * Decimal(str(self.keep_it_cost_ratio)):
            return DecisionOutput(
                destination="KEEP_IT",
                return_method="KEEP_IT",
                score=95,
                confidence=0.98,
                explanation=f"Coste logistico ({estimated_logistics_cost}) supera el valor del producto ({total_value}). Reembolso autorizado sin retorno fisico.",
                factors={
                    "cost_factor": 1.0,
                    "value_factor": 0.2,
                    "logistics_factor": 0.9,
                },
                business_rule_applied="KEEP_IT_COST_EXCEEDS_VALUE",
                requires_kam_approval=False,
                status="APROBADO",
                estimated_refund=total_value,
                keep_it_reason="Coste logistico superior al valor del producto",
                processing_time_ms=0,
            )

        return None

    def _estimate_logistics_cost(
        self,
        total_weight_kg: Decimal,
        channel: str,
    ) -> Decimal:
        base_cost = Decimal("5.00")
        weight_cost = total_weight_kg * Decimal("1.50")

        if channel == "B2B":
            return base_cost + weight_cost + Decimal("10.00")
        else:
            return base_cost + weight_cost

    def get_available_rules(self) -> dict:
        return {
            "rules": [
                {
                    "id": "B2C_STANDARD_DROP_OFF",
                    "description": "B2C con 1-5 articulos y peso <= 15kg -> Drop-off con QR",
                    "conditions": ["channel == B2C", "total_items <= 5", "total_weight_kg <= 15"],
                    "destination": "CARRIL_RAPIDO",
                    "method": "DROP_OFF",
                },
                {
                    "id": "B2C_EXCEEDS_DROP_OFF_LIMITS",
                    "description": "B2C con > 5 articulos o peso > 15kg -> Keep-it con reembolso",
                    "conditions": ["channel == B2C", "total_items > 5 OR total_weight_kg > 15"],
                    "destination": "KEEP_IT",
                    "method": "KEEP_IT",
                },
                {
                    "id": "KEEP_IT_COST_EXCEEDS_VALUE",
                    "description": "Coste logistico > valor producto -> Keep-it sin retorno",
                    "conditions": ["logistics_cost > product_value"],
                    "destination": "KEEP_IT",
                    "method": "KEEP_IT",
                },
                {
                    "id": "HYPERCUSTOMIZED_DEFECT_B2C",
                    "description": "Articulo hipercustomizado B2C con defecto -> Reciclaje",
                    "conditions": ["is_customized == true", "condition == DEFECTIVE", "channel == B2C"],
                    "destination": "RECICLAJE",
                    "method": "PICKUP",
                },
                {
                    "id": "B2B_REQUIRES_KAM",
                    "description": "B2B sin aprobacion KAM -> Pickup pendiente de autorizacion",
                    "conditions": ["channel == B2B", "has_kam_approval == false"],
                    "destination": "INSPECCION_B2B",
                    "method": "PICKUP",
                    "requires_kam_approval": True,
                },
                {
                    "id": "KAM_APPROVED_B2B",
                    "description": "B2B con aprobacion KAM -> Pickup programado",
                    "conditions": ["channel == B2B", "has_kam_approval == true"],
                    "destination": "CARRIL_RAPIDO",
                    "method": "PICKUP",
                },
                {
                    "id": "HYPERCUSTOMIZED_B2B_INSPECTION",
                    "description": "Articulo hipercustomizado B2B -> Inspeccion B2B obligatoria",
                    "conditions": ["is_customized == true", "channel == B2B"],
                    "destination": "INSPECCION_B2B",
                    "method": "PICKUP",
                    "requires_kam_approval": True,
                },
            ],
            "thresholds": {
                "B2C_MAX_ITEMS_DROP_OFF": 5,
                "B2C_MAX_WEIGHT_DROP_OFF_KG": 15.0,
                "B2B_LOT_SIZE_THRESHOLD": 50,
                "B2B_WEIGHT_THRESHOLD_KG": 15.0,
                "KEEP_IT_COST_THRESHOLD_RATIO": 1.0,
            },
        }


decision_engine = DecisionEngine()
