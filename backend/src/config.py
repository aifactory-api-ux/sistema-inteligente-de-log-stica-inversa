import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://logistics_user:logistics_pass@localhost:5432/logistics_db",
        description="PostgreSQL connection string with asyncpg driver"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, le=50)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=100)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg or postgresql protocol")
        return v


class RedisSettings(BaseSettings):
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=1)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must use redis:// protocol")
        return v


class JWTSettings(BaseSettings):
    JWT_SECRET: str = Field(
        default="",
        description="Secret key for JWT signing (required in production)"
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1, le=1440)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    JWT_MIN_SECRET_LENGTH: int = Field(default=32, ge=16)

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters long. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v


class APISettings(BaseSettings):
    API_VERSION: str = Field(default="v1")
    API_TITLE: str = Field(default="Sistema Inteligente de Logistica Inversa")
    API_DESCRIPTION: str = Field(
        default="API RESTful para la gestion inteligente de devoluciones y logística inversa"
    )
    API_V1_PREFIX: str = Field(default="/api/v1")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")


class SecuritySettings(BaseSettings):
    BCRYPT_COST_FACTOR: int = Field(default=12, ge=4, le=16)
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)
    SESSION_CACHE_TTL_SECONDS: int = Field(default=3600, ge=60)


class BusinessRulesSettings(BaseSettings):
    B2C_MAX_ITEMS_DROP_OFF: int = Field(default=5)
    B2C_MAX_WEIGHT_DROP_OFF_KG: float = Field(default=15.0)
    B2B_LOT_SIZE_THRESHOLD: int = Field(default=50)
    B2B_WEIGHT_THRESHOLD_KG: float = Field(default=15.0)
    KEEP_IT_COST_THRESHOLD_RATIO: float = Field(default=1.0)
    INSPECTION_SATURATION_THRESHOLD: int = Field(default=50)
    RETURN_RATE_SPIKE_THRESHOLD: float = Field(default=0.10)
    CYCLE_TIME_EXCEEDED_HOURS: float = Field(default=72.0)
    COST_THRESHOLD_BREACH_EUR: float = Field(default=100.0)
    KAM_AUTO_ESCALATION_TIMEOUT_HOURS: int = Field(default=24)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    api: APISettings = Field(default_factory=APISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    business_rules: BusinessRulesSettings = Field(default_factory=BusinessRulesSettings)

    @classmethod
    def from_env(cls, require_jwt_secret: bool = True) -> "Settings":
        settings = cls()

        if require_jwt_secret:
            try:
                _ = settings.jwt.JWT_SECRET
            except ValueError as e:
                raise RuntimeError(
                    f"Failed to initialize settings: {e}. "
                    "Set JWT_SECRET environment variable with a secure 32+ character string."
                ) from e

        return settings


@lru_cache
def get_settings(require_jwt_secret: bool = True) -> Settings:
    return Settings.from_env(require_jwt_secret=require_jwt_secret)


settings = get_settings(require_jwt_secret=False)


def get_database_url() -> str:
    return get_settings().database.DATABASE_URL


def get_redis_url() -> str:
    return get_settings().redis.REDIS_URL


def get_jwt_secret() -> str:
    return get_settings().jwt.JWT_SECRET


def get_jwt_algorithm() -> str:
    return get_settings().jwt.JWT_ALGORITHM


def get_api_version() -> str:
    return get_settings().api.API_VERSION


def get_log_level() -> str:
    return get_settings().api.LOG_LEVEL
