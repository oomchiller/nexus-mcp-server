from typing import Any

class NexusMcpError(Exception):
    """Base exception for Nexus MCP."""
    pass


class NexusApiError(NexusMcpError):
    """Raised when the Nexus API returns an error."""
    def __init__(self, message: str, status_code: int | None = None, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class NexusAuthError(NexusApiError):
    """Raised on authentication failure."""
    pass


class NexusPermissionError(NexusApiError):
    """Raised on permission failure (403)."""
    pass


class NexusNotFoundError(NexusApiError):
    """Raised when a resource is not found (404)."""
    pass


class NexusRateLimitError(NexusApiError):
    """Raised on rate limiting (429)."""
    pass


class NexusServerError(NexusApiError):
    """Raised on Nexus server errors (5xx)."""
    pass


class ConfigurationError(NexusMcpError):
    """Raised when there is a configuration error."""
    pass


class SafetyError(NexusMcpError):
    """Raised when a safety gate blocks an operation."""
    pass
