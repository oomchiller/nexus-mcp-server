import os
from nexus_mcp_server.config import Settings, McpMode


def test_config_defaults() -> None:
    # Set required env vars
    os.environ["NEXUS_URL"] = "http://localhost:8081"

    settings = Settings()  # type: ignore[call-arg]
    assert settings.nexus_mcp_mode == McpMode.READONLY
    assert str(settings.nexus_url).rstrip("/") == "http://localhost:8081"
    assert settings.nexus_verify_tls is True
    assert settings.nexus_mcp_enable_raw_api is False


def test_all_secrets() -> None:
    os.environ["NEXUS_URL"] = "http://localhost:8081"
    os.environ["NEXUS_PASSWORD"] = "secret1"

    settings = Settings()  # type: ignore[call-arg]
    secrets = settings.all_secrets
    assert "secret1" in secrets
