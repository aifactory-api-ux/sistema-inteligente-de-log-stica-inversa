# backend/shared/logging_config.py

import sys
import logging
import structlog
from typing import Any
from datetime import datetime

from config import settings


def add_trace_id(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add trace_id to log entries"""
    from shared.tracing import get_current_trace_id
    trace_id = get_current_trace_id()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add standardized timestamp"""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def rename_event_key(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Rename 'event' key to 'message' for standardization"""
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def setup_logging() -> None:
    """Configure structured logging with structlog"""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])
    else:
        processors.extend([
            rename_event_key,
            structlog.processors.Printer(),
        ])

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding contextual information to logs"""

    def __init__(self, logger: structlog.stdlib.BoundLogger, **context):
        self.logger = logger
        self.context = context
        self._token = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        self._token = structlog.contextvars.bind_contextvars(**self.context)
        return self.logger.bind(**self.context)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())
