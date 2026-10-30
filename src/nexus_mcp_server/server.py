import argparse
import json
import os
from typing import Optional, Literal, Any, Awaitable, Callable, Dict, List, TypeVar, cast

from mcp.server.fastmcp import FastMCP

from .config import Settings, get_settings, reset_settings
from .logging import setup_logging, get_logger
from .nexus_client import NexusClient
from .openapi import OpenApiHelper
from .safety import redact_secrets
logger = get_logger("server")
T = TypeVar("T")

# Initialize MCP server
mcp = FastMCP("Sonatype Nexus MCP Server")

# Global state for clients
source_client: Optional[NexusClient] = None
target_client: Optional[NexusClient] = None
openapi_helper: Optional[OpenApiHelper] = None

def get_clients() -> tuple[NexusClient, Optional[NexusClient], OpenApiHelper]:
    global source_client, target_client, openapi_helper
    settings = get_settings()

    if source_client is None:
        source_client = NexusClient(
            base_url=str(settings.nexus_url),
            username=settings.nexus_username,
            password=settings.nexus_password,
            verify_tls=settings.nexus_verify_tls,
            timeout=settings.nexus_timeout_seconds,
            allowed_hosts=settings.allowed_hosts_list,
            max_response_bytes=settings.nexus_mcp_max_raw_response_bytes,
        )
        openapi_helper = OpenApiHelper(source_client)

    if target_client is None and settings.nexus_target_url:
        target_client = NexusClient(
            base_url=str(settings.nexus_target_url),
            username=settings.nexus_target_username,
            password=settings.nexus_target_password,
            verify_tls=settings.nexus_target_verify_tls,
            timeout=settings.nexus_timeout_seconds,
            allowed_hosts=settings.allowed_hosts_list,
            max_response_bytes=settings.nexus_mcp_max_raw_response_bytes,
        )

    assert source_client is not None
    assert openapi_helper is not None
    return source_client, target_client, openapi_helper

async def _get_graph() -> Any:
    """Helper to get a built Knowledge Graph."""
    client, _, _ = get_clients()
    from .knowledge_graph.builder import build_knowledge_graph
    return await build_knowledge_graph(client)

def _safe_output(value: T) -> T:
    return cast(T, redact_secrets(value, get_settings().all_secrets))

def _safe_json(value: Any) -> str:
    return json.dumps(_safe_output(value), indent=2)

# =============================================================================
# RESOURCES (Read-only context, registered by register_optional_capabilities)
# =============================================================================

async def get_instance_summary_resource() -> str:
    """Get a high-level summary of the Nexus instance identity."""
    client, _, _ = get_clients()
    from .tools.system import get_system_status
    status = await get_system_status(client)
    return _safe_json(status)

async def get_repositories_resource() -> str:
    """Live repository inventory context."""
    client, _, _ = get_clients()
    from .tools.repositories import list_repositories
    repos = await list_repositories(client)
    return _safe_json([r.model_dump() for r in repos])

async def get_blobstores_resource() -> str:
    """Live blob store inventory context."""
    client, _, _ = get_clients()
    from .tools.blobstores import list_blobstores
    blobs = await list_blobstores(client)
    return _safe_json([b.model_dump() for b in blobs])

async def get_tasks_resource() -> str:
    """Live scheduled tasks context."""
    client, _, _ = get_clients()
    from .tools.tasks import list_tasks
    tasks = await list_tasks(client)
    return _safe_json([t.model_dump() for t in tasks])

async def get_cleanup_policies_resource() -> str:
    """Live cleanup policies context."""
    client, _, _ = get_clients()
    from .tools.config_objects import list_cleanup_policies
    policies = await list_cleanup_policies(client)
    return _safe_json([p.model_dump() for p in policies])

async def get_security_summary_resource() -> str:
    """High-level security configuration summary."""
    client, _, _ = get_clients()
    from .knowledge_graph.query_engine import QueryEngine
    graph = await _get_graph()
    return _safe_json(QueryEngine(graph).explain_security_model())

async def get_architecture_resource() -> str:
    """Generated architecture Markdown documentation."""
    graph = await _get_graph()
    from .docs_engine.generator import DocsGenerator
    return _safe_output(DocsGenerator(graph).generate_architecture_md())

async def get_knowledge_graph_resource() -> str:
    """Full semantic Knowledge Graph representation."""
    graph = await _get_graph()
    return _safe_json(graph.to_dict())

# =============================================================================
# TOOLS - OBSERVABILITY & SEMANTICS
# =============================================================================

@mcp.tool()
async def nexus_understand_architecture() -> dict[str, Any]:
    """Provide a graph-derived summary of Nexus storage architecture with evidence."""
    graph = await _get_graph()
    from .knowledge_graph.query_engine import QueryEngine
    return _safe_output(QueryEngine(graph).explain_storage_strategy()) # Reuse for now or expand

@mcp.tool()
async def nexus_explain_repository(name: str) -> dict[str, Any]:
    """Provide a complete semantic picture of a single repository, including its storage, groups, and policies."""
    graph = await _get_graph()
    from .knowledge_graph.query_engine import QueryEngine
    return _safe_output(QueryEngine(graph).explain_repository(name))

@mcp.tool()
async def nexus_explain_storage_strategy() -> dict[str, Any]:
    """Analyze how storage (blobstores) is utilized across the instance architecture with evidence."""
    graph = await _get_graph()
    from .knowledge_graph.query_engine import QueryEngine
    return _safe_output(QueryEngine(graph).explain_storage_strategy())

# =============================================================================
# TOOLS - INVENTORY & DOCUMENTATION
# =============================================================================

@mcp.tool()
async def nexus_audit_repository_content(
    repository: str,
    max_pages: int = 100,
    max_components: int = 5000,
) -> dict[str, Any]:
    """Collect a bounded complete repository component inventory server-side.

    Continuation tokens never leave the server. The result includes every
    component and asset reached, plus explicit completion and latest-download
    evidence; incomplete results must not be used for retirement decisions.
    """
    client, _, _ = get_clients()
    from .tools.repository_content import audit_repository_content
    return _safe_output(
        await audit_repository_content(client, repository, max_pages, max_components)
    )

@mcp.tool()
async def nexus_generate_inventory_json() -> str:
    """Generate a structured JSON inventory of all core Nexus objects."""
    graph = await _get_graph()
    from .iac.generator import IaCContextGenerator
    return _safe_output(IaCContextGenerator(graph).generate_inventory_json())

@mcp.tool()
async def nexus_generate_architecture_md() -> str:
    """Generate a high-level architecture overview document (Markdown)."""
    graph = await _get_graph()
    from .docs_engine.generator import DocsGenerator
    return _safe_output(DocsGenerator(graph).generate_architecture_md())

@mcp.tool()
async def nexus_generate_repository_catalog_md() -> str:
    """Generate a detailed repository catalog document (Markdown)."""
    graph = await _get_graph()
    from .docs_engine.generator import DocsGenerator
    return _safe_output(DocsGenerator(graph).generate_repository_catalog_md())

# =============================================================================
# TOOLS - AUDIT & SMELLS
# =============================================================================

@mcp.tool()
async def nexus_detect_architecture_smells() -> List[Dict[str, Any]]:
    """Expert system to detect unused resources, offline repos, and architectural inconsistencies."""
    graph = await _get_graph()
    from .operational.expert import OperationalExpert
    return _safe_output(OperationalExpert(graph).detect_risks())

@mcp.tool()
async def nexus_generate_audit_report() -> dict[str, Any]:
    """Generate the current audit report from available Nexus APIs."""
    client, _, _ = get_clients()
    from .tools.documentation import generate_audit_report
    return _safe_output(await generate_audit_report(client))

# =============================================================================
# TOOLS - IaC SUPPORT
# =============================================================================

@mcp.tool()
async def nexus_generate_terraform_context() -> str:
    """Expose live Nexus state as structured JSON for Terraform development."""
    graph = await _get_graph()
    from .iac.generator import IaCContextGenerator
    return _safe_output(IaCContextGenerator(graph).generate_terraform_context())

@mcp.tool()
async def nexus_generate_puppet_context() -> str:
    """Expose live Nexus state as YAML for Puppet Hiera development."""
    graph = await _get_graph()
    from .iac.generator import IaCContextGenerator
    return _safe_output(IaCContextGenerator(graph).generate_puppet_context())

@mcp.tool()
async def nexus_compare_live_state_with_declared_state(declared_state: dict[str, Any]) -> dict[str, Any]:
    """Detect drift between live Nexus state and a provided declared state (JSON/YAML)."""
    graph = await _get_graph()
    from .iac.generator import IaCContextGenerator
    return _safe_output(IaCContextGenerator(graph).detect_drift(declared_state))

# =============================================================================
# TOOLS - OPENAPI DISCOVERY
# =============================================================================

@mcp.tool()
async def nexus_openapi_list_operations() -> list[dict[str, Any]]:
    """Discover available REST operations from live OpenAPI documentation."""
    _, _, helper = get_clients()
    return _safe_output(await helper.list_operations())

@mcp.tool()
async def nexus_generate_capability_map() -> dict[str, list[dict[str, str]]]:
    """Group all available REST operations by functional domain (repositories, security, etc.)."""
    _, _, helper = get_clients()
    return _safe_output(await helper.generate_capability_map())

# =============================================================================
# TOOLS - WRITE OPERATIONS / ADMIN (DISABLED BY DEFAULT)
# =============================================================================

@mcp.tool()
async def nexus_delete_repository(name: str) -> dict[str, Any]:
    """Delete a repository by name. Requires admin mode and explicit enablement (NEXUS_MCP_ENABLE_WRITE_TOOLS)."""
    client, _, _ = get_clients()
    settings = get_settings()
    from .tools.admin import delete_repository
    return _safe_output(await delete_repository(client, settings, name))

@mcp.tool()
async def nexus_run_task(task_id: str) -> dict[str, Any]:
    """Run a scheduled task immediately. Requires admin mode and explicit enablement (NEXUS_MCP_ENABLE_WRITE_TOOLS)."""
    client, _, _ = get_clients()
    settings = get_settings()
    from .tools.admin import run_task
    return _safe_output(await run_task(client, settings, task_id))

@mcp.tool()
async def nexus_api_call(
    method: Literal["GET", "HEAD", "POST", "PUT", "DELETE"],
    path: str,
    query: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Safe, audited generic API caller. Write methods require admin mode and explicit enablement."""
    client, _, _ = get_clients()
    settings = get_settings()
    from .tools.raw_api import call_raw_api
    return _safe_output(await call_raw_api(client, settings, method, path, query, json_body))

# =============================================================================
# PROMPTS (Workflows, registered by register_optional_capabilities)
# =============================================================================

def nexus_audit_prompt() -> str:
    """Standard prompt for starting a Nexus audit workflow."""
    return (
        "Perform a limited Nexus configuration audit using the currently implemented tools. "
        "1. Start by discovering the architecture with 'nexus_understand_architecture'. "
        "2. Check for risks using 'nexus_detect_architecture_smells'. "
        "3. Generate an evidence-based report with 'nexus_generate_audit_report'. "
        "Summarize findings, evidence, confidence, and limitations. "
        "Do not describe the result as a complete security audit."
    )

def nexus_iac_drift_prompt() -> str:
    """Standard prompt for investigating configuration drift."""
    return (
        "I need to check for configuration drift in our Nexus instance. "
        "Please ask the user for their declared state (JSON or YAML), "
        "then use 'nexus_compare_live_state_with_declared_state' to identify differences."
    )

RESOURCES: tuple[tuple[str, Callable[[], Awaitable[str]]], ...] = (
    ("nexus://instance/summary", get_instance_summary_resource),
    ("nexus://repositories", get_repositories_resource),
    ("nexus://blobstores", get_blobstores_resource),
    ("nexus://tasks", get_tasks_resource),
    ("nexus://cleanup-policies", get_cleanup_policies_resource),
    ("nexus://security/summary", get_security_summary_resource),
    ("nexus://architecture", get_architecture_resource),
    ("nexus://knowledge_graph", get_knowledge_graph_resource),
)

PROMPTS: tuple[Callable[[], str], ...] = (
    nexus_audit_prompt,
    nexus_iac_drift_prompt,
)


def register_optional_capabilities(server: FastMCP, settings: Settings) -> None:
    """Register resources and prompts unless disabled by settings.

    Tools are always registered. Resources and prompts are optional because
    gateways that prefix tool names per server do not prefix resource URIs or
    prompt names, so several instances in one gateway collide on them.
    """
    if settings.nexus_mcp_enable_resources:
        for uri, resource in RESOURCES:
            server.resource(uri)(resource)
    if settings.nexus_mcp_enable_prompts:
        for prompt in PROMPTS:
            server.prompt()(prompt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Nexus MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--nexus-url",
        help="Nexus URL; overrides NEXUS_URL",
    )
    parser.add_argument(
        "--nexus-username",
        help="Nexus API username; overrides NEXUS_USERNAME",
    )
    parser.add_argument(
        "--verify-ssl",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Verify Nexus TLS certificates; overrides NEXUS_VERIFY_TLS",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind host for sse or streamable-http transport",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP bind port for sse or streamable-http transport",
    )
    return parser


def apply_cli_overrides(args: argparse.Namespace) -> None:
    if args.nexus_url:
        os.environ["NEXUS_URL"] = args.nexus_url
    if args.nexus_username:
        os.environ["NEXUS_USERNAME"] = args.nexus_username
    if args.verify_ssl is not None:
        os.environ["NEXUS_VERIFY_TLS"] = str(args.verify_ssl).lower()
    reset_settings()


def main() -> None:
    args = build_parser().parse_args()
    apply_cli_overrides(args)
    if args.transport != "stdio":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
    settings = get_settings()
    setup_logging(settings.nexus_log_level, settings.all_secrets)
    register_optional_capabilities(mcp, settings)
    logger.info(
        "Starting Nexus MCP Server in %s mode using %s transport",
        settings.nexus_mcp_mode,
        args.transport,
    )
    mcp.run(transport=args.transport)

if __name__ == "__main__":
    main()
