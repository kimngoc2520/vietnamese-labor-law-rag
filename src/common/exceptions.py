class AdaptiveRAGError(Exception):
    """Base exception for application-level errors."""


class IngestionError(AdaptiveRAGError):
    """Raised when document ingestion fails."""


class RetrievalError(AdaptiveRAGError):
    """Raised when retrieval fails."""


class GenerationError(AdaptiveRAGError):
    """Raised when answer generation fails."""


class VerificationError(AdaptiveRAGError):
    """Raised when answer/evidence verification fails."""


class ToolError(AdaptiveRAGError):
    """Raised when an agent tool fails."""