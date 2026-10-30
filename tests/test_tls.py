from pathlib import Path
import ssl
from typing import Any

import certifi
import httpx
import pytest

from nexus_mcp_server.config import get_settings
from nexus_mcp_server.nexus_client import NexusClient

PASSWORD = "synthetic-password-value"


@pytest.fixture
def source_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_URL", "https://nexus.example")
    monkeypatch.setenv("NEXUS_PASSWORD", PASSWORD)


def test_ca_bundles_are_unset_by_default(source_env: None) -> None:
    settings = get_settings()

    assert settings.nexus_ca_bundle is None
    assert settings.nexus_target_ca_bundle is None


@pytest.mark.parametrize("variable", ["NEXUS_CA_BUNDLE", "NEXUS_TARGET_CA_BUNDLE"])
def test_valid_ca_bundle_is_accepted(source_env: None, monkeypatch: pytest.MonkeyPatch, variable: str) -> None:
    monkeypatch.setenv(variable, certifi.where())

    get_settings()


@pytest.mark.parametrize("variable", ["NEXUS_CA_BUNDLE", "NEXUS_TARGET_CA_BUNDLE"])
def test_missing_ca_bundle_fails_at_startup_without_secrets(
    source_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, variable: str
) -> None:
    missing = tmp_path / "missing.pem"
    monkeypatch.setenv(variable, str(missing))

    with pytest.raises(ValueError) as raised:
        get_settings()

    message = str(raised.value)
    assert variable in message and str(missing) in message
    assert PASSWORD not in message


def test_ca_bundle_without_certificates_is_rejected(
    source_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bundle = tmp_path / "empty.pem"
    bundle.write_text("not a certificate\n")
    monkeypatch.setenv("NEXUS_CA_BUNDLE", str(bundle))

    with pytest.raises(ValueError, match="NEXUS_CA_BUNDLE cannot be loaded"):
        get_settings()


@pytest.mark.parametrize(
    ("bundle", "verify"),
    [("NEXUS_CA_BUNDLE", "NEXUS_VERIFY_TLS"), ("NEXUS_TARGET_CA_BUNDLE", "NEXUS_TARGET_VERIFY_TLS")],
)
def test_ca_bundle_with_verification_disabled_is_rejected(
    source_env: None, monkeypatch: pytest.MonkeyPatch, bundle: str, verify: str
) -> None:
    monkeypatch.setenv(bundle, certifi.where())
    monkeypatch.setenv(verify, "false")

    with pytest.raises(ValueError, match="TLS verification is disabled") as raised:
        get_settings()

    assert PASSWORD not in str(raised.value)


@pytest.mark.asyncio
async def test_client_verifies_with_the_bundle_context(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    real_client = httpx.AsyncClient

    def spy(**kwargs: Any) -> httpx.AsyncClient:
        captured.update(kwargs)
        return real_client(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", spy)
    client = NexusClient("https://nexus.example", ca_bundle=certifi.where())
    await client.get_client()
    await client.close()

    assert isinstance(captured["verify"], ssl.SSLContext)
    assert captured["verify"].verify_mode == ssl.CERT_REQUIRED
    assert captured["trust_env"] is False


@pytest.mark.asyncio
async def test_client_default_verification_is_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    real_client = httpx.AsyncClient

    def spy(**kwargs: Any) -> httpx.AsyncClient:
        captured.update(kwargs)
        return real_client(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", spy)
    client = NexusClient("https://nexus.example")
    await client.get_client()
    await client.close()

    assert captured["verify"] is True


def test_client_rejects_bundle_without_verification() -> None:
    with pytest.raises(ValueError, match="requires TLS verification"):
        NexusClient("https://nexus.example", verify_tls=False, ca_bundle=certifi.where())
