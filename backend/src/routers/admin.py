# backend/src/routers/admin.py

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.schemas import UserSchema
from src.routers.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminConfigSchema(BaseModel):
    max_drop_off_weight_kg: float = Field(default=15.0, ge=0)
    max_drop_off_items: int = Field(default=5, ge=1)
    b2b_min_batch_size: int = Field(default=6, ge=1)
    b2b_max_batch_size: int = Field(default=100, ge=1)
    keep_it_threshold_percent: float = Field(default=100.0, ge=0)
    inspection_saturation_threshold: int = Field(default=50, ge=0)
    return_rate_spike_threshold_percent: float = Field(default=20.0, ge=0)
    cycle_time_threshold_hours: int = Field(default=72, ge=0)
    scoring_weights: dict[str, float] = Field(default_factory=dict)


class PromptVersion(BaseModel):
    version: str
    description: str
    rules: list[str]
    active: bool
    created_at: datetime
    created_by: str


class ScoringWeights(BaseModel):
    distance_weight: float = Field(default=0.2, ge=0, le=1)
    weight_weight: float = Field(default=0.3, ge=0, le=1)
    value_weight: float = Field(default=0.25, ge=0, le=1)
    condition_weight: float = Field(default=0.15, ge=0, le=1)
    customization_weight: float = Field(default=0.1, ge=0, le=1)


DEFAULT_CONFIG = {
    "max_drop_off_weight_kg": 15.0,
    "max_drop_off_items": 5,
    "b2b_min_batch_size": 6,
    "b2b_max_batch_size": 100,
    "keep_it_threshold_percent": 100.0,
    "inspection_saturation_threshold": 50,
    "return_rate_spike_threshold_percent": 20.0,
    "cycle_time_threshold_hours": 72,
    "scoring_weights": {
        "distance_weight": 0.2,
        "weight_weight": 0.3,
        "value_weight": 0.25,
        "condition_weight": 0.15,
        "customization_weight": 0.1,
    },
}


_current_config: dict = DEFAULT_CONFIG.copy()
_prompt_versions: list[dict] = [
    {
        "version": "v1.0",
        "description": "Reglas iniciales del motor de decision",
        "rules": ["B2C_STANDARD_DROP_OFF", "B2C_EXCEEDS_DROP_OFF_LIMITS", "KEEP_IT_COST_EXCEEDS_VALUE"],
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "system",
    }
]
_current_scoring_weights: dict = {
    "distance_weight": 0.2,
    "weight_weight": 0.3,
    "value_weight": 0.25,
    "condition_weight": 0.15,
    "customization_weight": 0.1,
}


@router.get("/config", response_model=AdminConfigSchema)
async def get_admin_config(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden acceder a la configuracion"
        )

    try:
        return AdminConfigSchema(**_current_config)
    except Exception as e:
        logger.error(f"Error getting admin config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener configuracion: {str(e)}"
        )


@router.put("/config", response_model=AdminConfigSchema)
async def put_admin_config(
    config: AdminConfigSchema,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden modificar la configuracion"
        )

    try:
        global _current_config
        _current_config = config.model_dump()
        logger.info(f"Admin config updated by user: {current_user.username}")
        return AdminConfigSchema(**_current_config)
    except Exception as e:
        logger.error(f"Error updating admin config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar configuracion: {str(e)}"
        )


@router.get("/prompts")
async def get_admin_prompts(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden acceder a los prompts"
        )

    return {
        "prompts": _prompt_versions,
        "total": len(_prompt_versions),
        "active_version": next((p["version"] for p in _prompt_versions if p["active"]), None),
    }


@router.post("/prompts")
async def create_prompt(
    description: str,
    rules: list[str],
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear prompts"
        )

    version = f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    new_prompt = {
        "version": version,
        "description": description,
        "rules": rules,
        "active": False,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.username,
    }

    _prompt_versions.append(new_prompt)

    logger.info(f"New prompt version {version} created by {current_user.username}")

    return new_prompt


@router.put("/prompts/{version}/activate")
async def activate_prompt(
    version: str,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden activar prompts"
        )

    prompt = next((p for p in _prompt_versions if p["version"] == version), None)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version de prompt {version} no encontrada"
        )

    for p in _prompt_versions:
        p["active"] = False

    prompt["active"] = True
    prompt["activated_at"] = datetime.utcnow().isoformat()
    prompt["activated_by"] = current_user.username

    logger.info(f"Prompt version {version} activated by {current_user.username}")

    return prompt


@router.get("/scoring-weights", response_model=ScoringWeights)
async def get_scoring_weights(
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role not in ["ADMIN", "KAM", "SUPERVISOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver los pesos de scoring"
        )

    return ScoringWeights(**_current_scoring_weights)


@router.put("/scoring-weights", response_model=ScoringWeights)
async def update_scoring_weights(
    weights: ScoringWeights,
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden modificar los pesos de scoring"
        )

    global _current_scoring_weights
    _current_scoring_weights = weights.model_dump()

    logger.info(f"Scoring weights updated by {current_user.username}: {_current_scoring_weights}")

    return ScoringWeights(**_current_scoring_weights)