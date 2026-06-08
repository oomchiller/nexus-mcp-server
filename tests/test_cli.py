import argparse

import pytest

from nexus_mcp_server.config import get_settings
from nexus_mcp_server.server import apply_cli_overrides, build_parser


def test_cli_defaults_to_stdio() -> None:
    args = build_parser().parse_args([])

    assert args.transport == "stdio"
    assert args.verify_ssl is None


def test_cli_overrides_nexus_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_URL", "https://old.example")
    monkeypatch.setenv("NEXUS_VERIFY_TLS", "true")
    args = argparse.Namespace(
        transport="stdio",
        nexus_url="https://nexus.example",
        nexus_username="reader",
        verify_ssl=False,
    )

    apply_cli_overrides(args)
    settings = get_settings()

    assert str(settings.nexus_url) == "https://nexus.example/"
    assert settings.nexus_username == "reader"
    assert settings.nexus_verify_tls is False
