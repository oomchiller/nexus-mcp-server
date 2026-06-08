from typing import Any

from nexus_mcp_server.errors import NexusNotFoundError
from nexus_mcp_server.tools.config_objects import list_cleanup_policies


class NotFoundClient:
    async def request(self, method: str, path: str) -> Any:
        raise NexusNotFoundError("Resource not found", 404, {"path": path})


def test_cleanup_policies_absent_endpoint_returns_empty_list() -> None:
    import asyncio

    policies = asyncio.run(list_cleanup_policies(NotFoundClient()))  # type: ignore[arg-type]

    assert policies == []
