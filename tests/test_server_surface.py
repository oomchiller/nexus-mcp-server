from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP

from nexus_mcp_server import server
from nexus_mcp_server.config import Settings
from nexus_mcp_server.server import mcp, register_optional_capabilities

EXPECTED_TOOLS = {
    "nexus_understand_architecture",
    "nexus_explain_repository",
    "nexus_explain_storage_strategy",
    "nexus_audit_repository_content",
    "nexus_generate_inventory_json",
    "nexus_generate_architecture_md",
    "nexus_generate_repository_catalog_md",
    "nexus_detect_architecture_smells",
    "nexus_generate_audit_report",
    "nexus_generate_terraform_context",
    "nexus_generate_puppet_context",
    "nexus_compare_live_state_with_declared_state",
    "nexus_openapi_list_operations",
    "nexus_generate_capability_map",
    "nexus_delete_repository",
    "nexus_run_task",
    "nexus_api_call",
}


def settings(**overrides: Any) -> Settings:
    return Settings.model_validate({"NEXUS_URL": "http://loc", **overrides})


def test_surface_flags_default_to_enabled() -> None:
    current = settings()

    assert current.nexus_mcp_enable_prompts is True
    assert current.nexus_mcp_enable_resources is True


def test_surface_flags_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEXUS_URL", "http://loc")
    monkeypatch.setenv("NEXUS_MCP_ENABLE_PROMPTS", "false")
    monkeypatch.setenv("NEXUS_MCP_ENABLE_RESOURCES", "false")

    current = Settings()  # type: ignore[call-arg]

    assert current.nexus_mcp_enable_prompts is False
    assert current.nexus_mcp_enable_resources is False


@pytest.mark.asyncio
async def test_module_import_registers_only_tools() -> None:
    tools = {tool.name for tool in await mcp.list_tools()}

    assert tools == EXPECTED_TOOLS
    assert await mcp.list_prompts() == []
    assert await mcp.list_resources() == []


@pytest.mark.asyncio
async def test_default_settings_register_resources_and_prompts() -> None:
    instance = FastMCP("test")

    register_optional_capabilities(instance, settings())

    prompts = {prompt.name for prompt in await instance.list_prompts()}
    resources = {str(resource.uri) for resource in await instance.list_resources()}
    assert prompts == {"nexus_audit_prompt", "nexus_iac_drift_prompt"}
    assert resources == {uri for uri, _ in server.RESOURCES}
    assert len(resources) == 8


@pytest.mark.asyncio
async def test_tools_only_settings_register_nothing_optional() -> None:
    instance = FastMCP("test")

    register_optional_capabilities(
        instance,
        settings(NEXUS_MCP_ENABLE_PROMPTS=False, NEXUS_MCP_ENABLE_RESOURCES=False),
    )

    assert await instance.list_prompts() == []
    assert await instance.list_resources() == []


@pytest.mark.asyncio
async def test_prompts_and_resources_switch_independently() -> None:
    instance = FastMCP("test")

    register_optional_capabilities(
        instance, settings(NEXUS_MCP_ENABLE_PROMPTS=False)
    )

    assert await instance.list_prompts() == []
    assert len(await instance.list_resources()) == 8


def test_instance_configuration_from_environment_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEXUS_URL", "https://repo.example")
    monkeypatch.setenv("NEXUS_USERNAME", "reader")
    monkeypatch.setenv("NEXUS_VERIFY_TLS", "false")
    monkeypatch.setenv("NEXUS_ALLOWED_HOSTS", "repo.example")

    current = Settings()  # type: ignore[call-arg]

    assert str(current.nexus_url) == "https://repo.example/"
    assert current.nexus_username == "reader"
    assert current.nexus_verify_tls is False
    assert current.allowed_hosts_list == ["repo.example"]
