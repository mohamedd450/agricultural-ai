"""Custom exception hierarchy for the Agricultural AI Platform."""


class AgriculturalAIException(Exception):
    """Base exception for all Agricultural AI Platform errors."""

    status_code: int = 500
    detail: str = "An internal error occurred."
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.detail)

    def to_dict(self) -> dict:
        """Serialize the exception for API responses."""
        return {
            "error_code": self.error_code,
            "detail": self.detail,
            "status_code": self.status_code,
        }


class VisionServiceError(AgriculturalAIException):
    """Raised when the vision/image-analysis service fails."""

    status_code = 502
    detail = "Vision service encountered an error."
    error_code = "VISION_SERVICE_ERROR"


class VoiceServiceError(AgriculturalAIException):
    """Raised when the voice/speech service fails."""

    status_code = 502
    detail = "Voice service encountered an error."
    error_code = "VOICE_SERVICE_ERROR"


class GraphRAGError(AgriculturalAIException):
    """Raised when the graph-RAG knowledge service fails."""

    status_code = 502
    detail = "Graph-RAG service encountered an error."
    error_code = "GRAPH_RAG_ERROR"


class VectorDBError(AgriculturalAIException):
    """Raised when the vector database service fails."""

    status_code = 502
    detail = "Vector database service encountered an error."
    error_code = "VECTOR_DB_ERROR"


class AuthenticationError(AgriculturalAIException):
    """Raised on authentication or authorization failures."""

    status_code = 401
    detail = "Authentication failed."
    error_code = "AUTHENTICATION_ERROR"


class RateLimitError(AgriculturalAIException):
    """Raised when a client exceeds the allowed request rate."""

    status_code = 429
    detail = "Rate limit exceeded. Please try again later."
    error_code = "RATE_LIMIT_ERROR"


class ValidationError(AgriculturalAIException):
    """Raised when user input fails validation."""

    status_code = 422
    detail = "Input validation failed."
    error_code = "VALIDATION_ERROR"


class ServiceUnavailableError(AgriculturalAIException):
    """Raised when a downstream service is unreachable."""

    status_code = 503
    detail = "Service is temporarily unavailable."
    error_code = "SERVICE_UNAVAILABLE"
