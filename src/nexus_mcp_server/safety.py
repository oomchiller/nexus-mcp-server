import posixpath
from typing import Any, Literal
from urllib.parse import unquote, urlsplit

from .config import McpMode, Settings
from .errors import SafetyError

SENSITIVE_KEYS = {
    "authorization",
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "credential",
    "credentials",
}

def validate_operation(
    settings: Settings,
    method: Literal["GET", "HEAD", "POST", "PUT", "DELETE"],
    is_raw_api: bool = False
) -> None:
    """Validate if an operation is allowed based on safety gates."""

    # Raw API check
    if is_raw_api and not settings.nexus_mcp_enable_raw_api:
        raise SafetyError("Raw API calls are disabled. Enable NEXUS_MCP_ENABLE_RAW_API to use them.")

    if is_raw_api and settings.nexus_mcp_raw_api_get_only and method != "GET":
        raise SafetyError("Raw API is configured for GET requests only.")

    # Write operation check
    is_write = method in ("POST", "PUT", "DELETE")

    if is_write:
        if settings.nexus_mcp_mode == McpMode.READONLY:
            raise SafetyError(f"Operation {method} is not allowed in readonly mode.")

        if settings.nexus_mcp_mode == McpMode.AUDIT:
            raise SafetyError(f"Operation {method} is not allowed in audit mode.")

        if not settings.nexus_mcp_enable_write_tools:
            raise SafetyError("Write operations are disabled. Enable NEXUS_MCP_ENABLE_WRITE_TOOLS.")

def validate_path(path: str) -> str:
    """Canonicalize and validate a Nexus REST path."""
    parts = urlsplit(path)
    if parts.scheme or parts.netloc:
        raise SafetyError("Access denied: raw API path must be relative to the configured Nexus URL.")

    decoded_path = unquote(parts.path)
    if "\x00" in decoded_path:
        raise SafetyError("Access denied: null byte detected in path.")

    normalized = posixpath.normpath(decoded_path)
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"

    if not normalized.startswith("/service/rest/"):
        raise SafetyError(f"Access denied: path must stay under /service/rest/. Path: {path}")

    if decoded_path != normalized:
        raise SafetyError(f"Access denied: non-canonical or traversal path rejected: {path}")

    return normalized


def redact_secrets(value: Any, configured_secrets: list[str] | None = None) -> Any:
    """Recursively redact common secret-bearing keys and configured secret values."""
    secrets = [secret for secret in (configured_secrets or []) if secret]

    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in SENSITIVE_KEYS):
                redacted[key] = "********"
            else:
                redacted[key] = redact_secrets(item, secrets)
        return redacted

    if isinstance(value, list):
        return [redact_secrets(item, secrets) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_secrets(item, secrets) for item in value)

    if isinstance(value, str):
        redacted_text = value
        for secret in secrets:
            redacted_text = redacted_text.replace(secret, "********")
        return redacted_text

    return value
