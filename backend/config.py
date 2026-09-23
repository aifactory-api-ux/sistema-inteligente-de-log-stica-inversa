# backend/config.py

import os
from functools import lru_cache
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:25432/logistica",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v


class RedisSettings(BaseModel):
    REDIS_URL: str = Field(
        default="redis://localhost:26379/0",
        description="Redis connection string"
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=1)


class SecuritySettings(BaseModel):
    SECRET_KEY: str = Field(
        default="change-me-in-production-minimum-32-chars!!",
        description="JWT signing secret"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)
    PASSWORD_Bcrypt_COST: int = Field(default=12, ge=4, le=16)
    CORS_ORIGINS: str = Field(
        default="http://localhost:21002,http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )


class ApiSettings(BaseModel):
    API_TITLE: str = Field(default="Sistema Inteligente de Logistica Inversa")
    API_DESCRIPTION: str = Field(
        default="API RESTful para la gestion inteligente de devoluciones y logistica inversa"
    )
    API_V1_PREFIX: str = Field(default="/api/v1")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    VERSION: str = Field(default="v1")


class BusinessRulesSettings(BaseModel):
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


class JWTSettings(BaseModel):
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


class SMTPSettings(BaseModel):
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM: str = Field(default="no-reply@logistica-inversa.com")


class MapsSettings(BaseModel):
    MAPS_API_KEY: str = Field(default="")
    MAPS_PROVIDER: str = Field(default="mapbox")


class FeatureFlags(BaseModel):
    ENABLE_KAM_APPROVALS: bool = Field(default=True)
    ENABLE_BATCH_UPLOAD: bool = Field(default=True)
    ENABLE_QR_GENERATION: bool = Field(default=True)
    ENABLE_REPORTS: bool = Field(default=True)
    DECISION_ENGINE_V2: bool = Field(default=False)


class ApplicationSettings(BaseModel):
    MAX_BATCH_SIZE: int = Field(default=1000, ge=1)
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1)
    SESSION_TIMEOUT_MINUTES: int = Field(default=60)
    QR_CODE_EXPIRY_HOURS: int = Field(default=72)
    KAM_APPROVAL_TIMEOUT_HOURS: int = Field(default=24)


class AlertThresholds(BaseModel):
    INSPECTION_SATURATION_THRESHOLD: float = Field(default=0.85, ge=0, le=1)
    RETURN_RATE_SPIKE_THRESHOLD: float = Field(default=10.0, ge=0)
    CYCLE_TIME_ALERT_HOURS: float = Field(default=24.0, ge=0)


class ObservabilitySettings(BaseModel):
    OTEL_SERVICE_NAME: str = Field(default="logistica-backend")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://localhost:4317")
    OTEL_ENABLED: bool = Field(default=False)
    PROMETHEUS_ENABLED: bool = Field(default=True)


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    business_rules: BusinessRulesSettings = Field(default_factory=BusinessRulesSettings)
    smtp: SMTPSettings = Field(default_factory=SMTPSettings)
    maps: MapsSettings = Field(default_factory=MapsSettings)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    alert_thresholds: AlertThresholds = Field(default_factory=AlertThresholds)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", self.database.DATABASE_URL)

    @property
    def DATABASE_POOL_SIZE(self) -> int:
        return self.database.DATABASE_POOL_SIZE

    @property
    def REDIS_URL(self) -> str:
        return os.getenv("REDIS_URL", self.redis.REDIS_URL)

    @property
    def SECRET_KEY(self) -> str:
        return os.getenv("SECRET_KEY", self.security.SECRET_KEY)

    @property
    def OTEL_SERVICE_NAME(self) -> str:
        return self.observability.OTEL_SERVICE_NAME

    @property
    def OTEL_EXPORTER_OTLP_ENDPOINT(self) -> str:
        return self.observability.OTEL_EXPORTER_OTLP_ENDPOINT

    @property
    def OTEL_ENABLED(self) -> bool:
        return self.observability.OTEL_ENABLED


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
