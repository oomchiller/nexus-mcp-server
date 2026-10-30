from typing import Any

import pytest

from nexus_mcp_server.config import McpMode, Settings
from nexus_mcp_server.errors import SafetyError
from nexus_mcp_server.tools.admin import delete_repository, run_task
from nexus_mcp_server.tools.raw_api import call_raw_api


class RecordingClient:
    def __init__(self, response: Any = None):
        self.calls: list[dict[str, Any]] = []
        self.response = response if response is not None else {"ok": True}

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        self.calls.append({"method": method, "path": path, "params": params, "json": json})
        return self.response


def admin_settings(**overrides: Any) -> Settings:
    data = {
        "NEXUS_URL": "http://loc",
        "NEXUS_MCP_MODE": McpMode.ADMIN,
        "NEXUS_MCP_ENABLE_WRITE_TOOLS": True,
    }
    data.update(overrides)
    return Settings.model_validate(data)


@pytest.mark.asyncio
async def test_delete_repository_url_encodes_name() -> None:
    client: Any = RecordingClient()

    await delete_repository(client, admin_settings(), "repo/name")

    assert client.calls[0]["method"] == "DELETE"
    assert client.calls[0]["path"] == "/service/rest/v1/repositories/repo%2Fname"


@pytest.mark.asyncio
async def test_run_task_url_encodes_task_id() -> None:
    client: Any = RecordingClient()

    await run_task(client, admin_settings(), "task/id")

    assert client.calls[0]["method"] == "POST"
    assert client.calls[0]["path"] == "/service/rest/v1/tasks/task%2Fid/run"


@pytest.mark.asyncio
async def test_raw_api_requires_enablement() -> None:
    client: Any = RecordingClient()
    settings = Settings.model_validate({"NEXUS_URL": "http://loc"})

    with pytest.raises(SafetyError, match="Raw API calls are disabled"):
        await call_raw_api(
            client,
            settings,
            "GET",
            "/service/rest/v1/repositories",
        )


@pytest.mark.asyncio
async def test_raw_api_redacts_response_and_uses_canonical_path() -> None:
    client: Any = RecordingClient({"token": "abc", "message": "secret-value"})
    settings = Settings.model_validate(
        {
            "NEXUS_URL": "http://loc",
            "NEXUS_PASSWORD": "secret-value",
            "NEXUS_MCP_ENABLE_RAW_API": True,
        }
    )

    result = await call_raw_api(
        client,
        settings,
        "GET",
        "/service/rest/v1/repositories",
    )

    assert client.calls[0]["path"] == "/service/rest/v1/repositories"
    assert result["data"] == {"token": "********", "message": "********"}


@pytest.mark.asyncio
async def test_write_tools_never_reach_nexus_without_both_gates() -> None:
    gate_sets: list[dict[str, Any]] = [
        {},
        {"NEXUS_MCP_ENABLE_WRITE_TOOLS": True},
        {"NEXUS_MCP_MODE": McpMode.ADMIN},
        {"NEXUS_MCP_MODE": McpMode.AUDIT, "NEXUS_MCP_ENABLE_WRITE_TOOLS": True},
    ]
    for gates in gate_sets:
        client: Any = RecordingClient()
        settings = Settings.model_validate({"NEXUS_URL": "http://loc", **gates})

        with pytest.raises(SafetyError):
            await delete_repository(client, settings, "repo")
        with pytest.raises(SafetyError):
            await run_task(client, settings, "task")
        raw_settings = Settings.model_validate(
            {"NEXUS_URL": "http://loc", "NEXUS_MCP_ENABLE_RAW_API": True, **gates}
        )
        for method in ("POST", "PUT", "DELETE"):
            with pytest.raises(SafetyError):
                await call_raw_api(
                    client, raw_settings, method, "/service/rest/v1/repositories"
                )

        assert client.calls == []
