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
    nexus_timeout_seconds: int = Field(default=30, alias="NEXUS_TIMEOUT_SECONDS")
    nexus_allowed_hosts: str = Field(default="localhost,127.0.0.1", alias="NEXUS_ALLOWED_HOSTS")

    # Target Nexus
    nexus_target_url: Optional[HttpUrl] = Field(default=None, alias="NEXUS_TARGET_URL")
    nexus_target_username: Optional[str] = Field(default=None, alias="NEXUS_TARGET_USERNAME")
    nexus_target_password: Optional[str] = Field(default=None, alias="NEXUS_TARGET_PASSWORD")
    nexus_target_verify_tls: bool = Field(default=True, alias="NEXUS_TARGET_VERIFY_TLS")

    # Logging
    nexus_log_level: str = Field(default="INFO", alias="NEXUS_LOG_LEVEL")

    # Safety & Raw API
    nexus_mcp_enable_raw_api: bool = Field(default=False, alias="NEXUS_MCP_ENABLE_RAW_API")
    nexus_mcp_raw_api_get_only: bool = Field(default=False, alias="NEXUS_MCP_RAW_API_GET_ONLY")
    nexus_mcp_enable_write_tools: bool = Field(default=False, alias="NEXUS_MCP_ENABLE_WRITE_TOOLS")
    nexus_mcp_max_page_size: int = Field(default=100, alias="NEXUS_MCP_MAX_PAGE_SIZE")
    nexus_mcp_max_raw_response_bytes: int = Field(default=1048576, alias="NEXUS_MCP_MAX_RAW_RESPONSE_BYTES")

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


_settings: Optional[Settings] = None


def reset_settings() -> None:
    global _settings
    _settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore
    return _settings
