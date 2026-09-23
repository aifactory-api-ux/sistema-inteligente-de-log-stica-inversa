# backend/shared/exceptions.py

from typing import Optional, Any


class LogisticaException(Exception):
    """Base exception for all application exceptions"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or "LOGISTICA_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(LogisticaException):
    """Resource not found exception"""

    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[dict[str, Any]] = None,
    ):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details=details or {"resource": resource, "identifier": identifier},
        )


class ValidationException(LogisticaException):
    """Validation error exception"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details or {"field": field} if field else {},
        )


class UnauthorizedException(LogisticaException):
    """Authentication required exception"""

    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenException(LogisticaException):
    """Access forbidden exception"""

    def __init__(
        self,
        message: str = "Access forbidden",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            details=details,
        )


class RateLimitException(LogisticaException):
    """Rate limit exceeded exception"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details=details or {"retry_after": retry_after} if retry_after else {},
        )


class ExternalServiceException(LogisticaException):
    """External service communication error"""

    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details=details or {"service": service},
        )


class BatchProcessingException(LogisticaException):
    """Batch processing error"""

    def __init__(
        self,
        batch_id: str,
        message: str,
        failed_rows: Optional[list[int]] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="BATCH_PROCESSING_ERROR",
            details=details or {"batch_id": batch_id, "failed_rows": failed_rows or []},
        )


class KAMApprovalException(LogisticaException):
    """KAM approval workflow error"""

    def __init__(
        self,
        approval_id: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="KAM_APPROVAL_ERROR",
            details=details or {"approval_id": approval_id},
        )


class QRCodeGenerationException(LogisticaException):
    """QR code generation error"""

    def __init__(
        self,
        return_id: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="QR_GENERATION_ERROR",
            details=details or {"return_id": return_id},
        )


class DecisionEngineException(LogisticaException):
    """Decision engine processing error"""

    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="DECISION_ENGINE_ERROR",
            details=details or {"trace_id": trace_id} if trace_id else {},
        )
