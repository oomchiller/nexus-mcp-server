import ssl
from enum import Enum
from typing import Optional
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class McpMode(str, Enum):
    READONLY = "readonly"
    AUDIT = "audit"
    ADMIN = "admin"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Mode
    nexus_mcp_mode: McpMode = Field(default=McpMode.READONLY, alias="NEXUS_MCP_MODE")

    # Source Nexus
    nexus_url: HttpUrl = Field(alias="NEXUS_URL")
    nexus_username: Optional[str] = Field(default=None, alias="NEXUS_USERNAME")
    nexus_password: Optional[str] = Field(default=None, alias="NEXUS_PASSWORD")
    nexus_verify_tls: bool = Field(default=True, alias="NEXUS_VERIFY_TLS")
    nexus_ca_bundle: Optional[str] = Field(default=None, alias="NEXUS_CA_BUNDLE")
    nexus_timeout_seconds: int = Field(default=30, alias="NEXUS_TIMEOUT_SECONDS")
    nexus_allowed_hosts: str = Field(default="localhost,127.0.0.1", alias="NEXUS_ALLOWED_HOSTS")

    # Target Nexus
    nexus_target_url: Optional[HttpUrl] = Field(default=None, alias="NEXUS_TARGET_URL")
    nexus_target_username: Optional[str] = Field(default=None, alias="NEXUS_TARGET_USERNAME")
    nexus_target_password: Optional[str] = Field(default=None, alias="NEXUS_TARGET_PASSWORD")
    nexus_target_verify_tls: bool = Field(default=True, alias="NEXUS_TARGET_VERIFY_TLS")
    nexus_target_ca_bundle: Optional[str] = Field(default=None, alias="NEXUS_TARGET_CA_BUNDLE")

    # Logging
    nexus_log_level: str = Field(default="INFO", alias="NEXUS_LOG_LEVEL")

    # Safety & Raw API
    nexus_mcp_enable_raw_api: bool = Field(default=False, alias="NEXUS_MCP_ENABLE_RAW_API")
    nexus_mcp_raw_api_get_only: bool = Field(default=False, alias="NEXUS_MCP_RAW_API_GET_ONLY")
    nexus_mcp_enable_write_tools: bool = Field(default=False, alias="NEXUS_MCP_ENABLE_WRITE_TOOLS")
    nexus_mcp_max_page_size: int = Field(default=100, alias="NEXUS_MCP_MAX_PAGE_SIZE")
    nexus_mcp_max_raw_response_bytes: int = Field(default=1048576, alias="NEXUS_MCP_MAX_RAW_RESPONSE_BYTES")

    # MCP surface
    nexus_mcp_enable_prompts: bool = Field(default=True, alias="NEXUS_MCP_ENABLE_PROMPTS")
    nexus_mcp_enable_resources: bool = Field(default=True, alias="NEXUS_MCP_ENABLE_RESOURCES")

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.nexus_allowed_hosts.split(",") if h.strip()]

    @property
    def all_secrets(self) -> list[str]:
        secrets = []
        if self.nexus_password:
            secrets.append(self.nexus_password)
        if self.nexus_target_password:
            secrets.append(self.nexus_target_password)
        return secrets


def load_ca_bundle(path: str, variable: str = "CA bundle") -> ssl.SSLContext:
    """TLS context trusting only the certificates in a PEM bundle file."""
    try:
        return ssl.create_default_context(cafile=path)
    except (OSError, ssl.SSLError) as error:
        reason = getattr(error, "reason", None) or getattr(error, "strerror", None) or type(error).__name__
        raise ValueError(f"{variable} cannot be loaded from {path}: {reason}") from None


def check_tls_settings(settings: Settings) -> None:
    """Fail at startup on an unusable CA bundle.

    Runs outside pydantic validation, whose errors echo the input values,
    passwords included.
    """
    for variable, bundle, verify in (
        ("NEXUS_CA_BUNDLE", settings.nexus_ca_bundle, settings.nexus_verify_tls),
        ("NEXUS_TARGET_CA_BUNDLE", settings.nexus_target_ca_bundle, settings.nexus_target_verify_tls),
    ):
        if bundle:
            if not verify:
                raise ValueError(f"{variable} is set but TLS verification is disabled")
            load_ca_bundle(bundle, variable)


_settings: Optional[Settings] = None


def reset_settings() -> None:
    global _settings
    _settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        settings = Settings()  # type: ignore
        check_tls_settings(settings)
        _settings = settings
    return _settings
