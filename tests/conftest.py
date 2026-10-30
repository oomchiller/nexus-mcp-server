import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from nexus_mcp_server.config import reset_settings


@pytest.fixture(autouse=True)
def isolated_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    """Keep a developer's .env and NEXUS_* variables out of tests."""
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.startswith("NEXUS_"):
            monkeypatch.delenv(name)
    reset_settings()
    yield
    reset_settings()
