from typing import Any

from nexus_mcp_server.errors import NexusNotFoundError
from nexus_mcp_server.tools.config_objects import list_cleanup_policies


class NotFoundClient:
    async def request(self, method: str, path: str) -> Any:
        raise NexusNotFoundError("Resource not found", 404, {"path": path})


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def request(self, method: str, path: str) -> Any:
        self.calls.append((method, path))
        return []


def test_cleanup_policies_uses_current_nexus_endpoint() -> None:
    import asyncio

    client = RecordingClient()
    policies = asyncio.run(list_cleanup_policies(client))  # type: ignore[arg-type]

    assert policies == []
    assert client.calls == [("GET", "/service/rest/v1/cleanup-policies")]


def test_cleanup_policies_absent_endpoint_returns_empty_list() -> None:
    import asyncio

    policies = asyncio.run(list_cleanup_policies(NotFoundClient()))  # type: ignore[arg-type]

    assert policies == []
