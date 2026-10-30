from typing import Any

import pytest

from nexus_mcp_server.errors import (
    NexusApiError,
    NexusNotFoundError,
    NexusPermissionError,
)
from nexus_mcp_server.knowledge_graph.builder import _run_collector
from nexus_mcp_server.knowledge_graph.graph import KnowledgeGraph
from nexus_mcp_server.tools.blobstores import get_blobstore
from nexus_mcp_server.tools.components import get_component
from nexus_mcp_server.tools.config_objects import get_routing_rule
from nexus_mcp_server.tools.system import readiness_basic_check
from nexus_mcp_server.tools.tasks import get_task


class RaisingClient:
    def __init__(self, error: Exception):
        self.error = error
        self.paths: list[str] = []

    async def request(self, method: str, path: str, **_: Any) -> Any:
        self.paths.append(path)
        raise self.error


GETTERS = [get_task, get_component, get_blobstore, get_routing_rule]


@pytest.mark.asyncio
@pytest.mark.parametrize("getter", GETTERS)
async def test_getters_return_none_only_when_not_found(getter: Any) -> None:
    client: Any = RaisingClient(NexusNotFoundError("missing", 404))

    assert await getter(client, "a/b") is None
    assert client.paths[0].endswith("/a%2Fb")


@pytest.mark.asyncio
@pytest.mark.parametrize("getter", GETTERS)
async def test_getters_surface_operational_failures(getter: Any) -> None:
    client: Any = RaisingClient(NexusPermissionError("denied", 403))

    with pytest.raises(NexusPermissionError):
        await getter(client, "name")


@pytest.mark.asyncio
async def test_readiness_reports_unreachable_api() -> None:
    class StatusOnlyClient:
        async def request(self, method: str, path: str) -> Any:
            if path.endswith("/status"):
                return {}
            raise NexusApiError("connection refused")

    result = await readiness_basic_check(StatusOnlyClient())  # type: ignore[arg-type]

    assert result["api_reachable"] is False


@pytest.mark.asyncio
async def test_optional_collector_records_nexus_failure_as_limitation() -> None:
    graph = KnowledgeGraph()

    async def collect() -> Any:
        raise NexusPermissionError("denied", 403)

    result = await _run_collector(graph, "roles", "optional", collect, default=[])

    assert result == []
    assert any("roles unavailable" in item for item in graph.metadata["limitations"])


@pytest.mark.asyncio
async def test_collector_does_not_hide_programming_errors() -> None:
    graph = KnowledgeGraph()

    async def collect() -> Any:
        raise AttributeError("bug")

    with pytest.raises(AttributeError):
        await _run_collector(graph, "roles", "optional", collect, default=[])
