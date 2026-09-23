# backend/shared/tracing.py

import logging
from typing import Optional
from uuid import UUID
from contextvars import ContextVar
from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Span, Status, StatusCode

from config import settings

logger = logging.getLogger(__name__)

trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

_tracer: Optional[trace.Tracer] = None


@dataclass
class TraceContext:
    """Distributed tracing context"""
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    enabled: bool = False


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing"""
    global _tracer

    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry tracing is disabled")
        return

    try:
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: settings.OTEL_SERVICE_NAME,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        })

        provider = TracerProvider(resource=resource)

        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
                insecure=True,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception as e:
            logger.warning(f"Failed to setup OTLP exporter: {e}")

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(settings.OTEL_SERVICE_NAME)
        logger.info(f"OpenTelemetry tracing initialized for {settings.OTEL_SERVICE_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")


def get_tracer() -> trace.Tracer:
    """Get the configured tracer"""
    global _tracer
    if _tracer is None:
        return trace.get_tracer("logistica-inversa")
    return _tracer


def create_span(
    name: str,
    attributes: Optional[dict] = None,
) -> Span:
    """Create a new span"""
    tracer = get_tracer()
    span = tracer.start_span(name)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    return span


def inject_trace_context(headers: dict) -> dict:
    """Inject trace context into HTTP headers"""
    if settings.OTEL_ENABLED:
        span = trace.get_current_span()
        if span:
            ctx = span.get_span_context()
            if ctx.is_valid:
                headers["traceparent"] = f"00-{ctx.trace_id:032x}-{ctx.span_id:016x}-01"
    return headers


def extract_trace_context(headers: dict) -> TraceContext:
    """Extract trace context from HTTP headers"""
    context = TraceContext(enabled=settings.OTEL_ENABLED)

    if not settings.OTEL_ENABLED:
        return context

    traceparent = headers.get("traceparent")
    if traceparent:
        try:
            parts = traceparent.split("-")
            if len(parts) == 4:
                context.trace_id = parts[1]
                context.span_id = parts[2]
        except Exception as e:
            logger.debug(f"Failed to parse traceparent: {e}")

    return context


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return trace_id_var.get()


def set_span_status(span: Span, success: bool, message: Optional[str] = None) -> None:
    """Set span status"""
    if success:
        span.set_status(Status(StatusCode.OK))
    else:
        span.set_status(Status(StatusCode.ERROR, message or "Error"))


def record_exception(span: Span, exception: Exception) -> None:
    """Record an exception on the span"""
    span.record_exception(exception)
    span.set_status(Status(StatusCode.ERROR, str(exception)))
