from collections.abc import Awaitable, Callable
from typing import Any, Literal

from ..errors import NexusApiError
from ..models import BlobStore, CleanupPolicy, ContentSelector, NexusTask, Privilege, Repository, Role, RoutingRule, User
from ..nexus_client import NexusClient
from ..tools.blobstores import list_blobstores
from ..tools.config_objects import list_cleanup_policies, list_content_selectors, list_routing_rules
from ..tools.repositories import enrich_repositories_with_details, list_repositories
from ..tools.security import list_privileges, list_roles, list_users
from ..tools.system import get_system_status
from ..tools.tasks import list_tasks
from .entities import EntityType, GraphEntity, GraphRelationship, RelationshipType
from .graph import KnowledgeGraph

CollectorKind = Literal["core", "optional", "pro_only", "experimental"]


async def build_knowledge_graph(client: NexusClient) -> KnowledgeGraph:
    """Build a version-tolerant Nexus graph from available REST endpoints."""
    graph = KnowledgeGraph()
    capabilities = await _discover_capabilities(client, graph)
    available_paths = set(capabilities.get("paths", []))

    status: dict[str, Any] = await _run_collector(
        graph,
        "system_status",
        "core",
        lambda: get_system_status(client),
        default={},
    )
    instance_id = "instance:local"
    graph.add_entity(
        GraphEntity(
            id=instance_id,
            type=EntityType.INSTANCE,
            name=client.base_url,
            properties={"version": status.get("version"), "state": status.get("state")},
        )
    )

    blobs: list[BlobStore] = await _run_collector(
        graph,
        "blobstores",
        "core",
        lambda: list_blobstores(client),
        default=[],
        required_paths=("/v1/blobstores",),
        available_paths=available_paths,
    )
    for b_item in blobs:
        graph.add_entity(
            GraphEntity(
                id=f"blobstore:{b_item.name}",
                type=EntityType.BLOBSTORE,
                name=b_item.name,
                properties={
                    "type": b_item.type,
                    "totalSizeInBytes": b_item.totalSizeInBytes,
                    "blobCount": b_item.blobCount,
                },
            )
        )
        graph.add_relationship(
            GraphRelationship(
                source_id=instance_id,
                target_id=f"blobstore:{b_item.name}",
                type=RelationshipType.MANAGED_BY,
            )
        )

    policies: list[CleanupPolicy] = await _run_collector(
        graph,
        "cleanup_policies",
        "optional",
        lambda: list_cleanup_policies(client),
        default=[],
        required_paths=("/v1/cleanup", "/v1/cleanup-policies"),
        available_paths=available_paths,
    )
    for p_item in policies:
        graph.add_entity(GraphEntity(id=f"policy:{p_item.name}", type=EntityType.CLEANUP_POLICY, name=p_item.name))

    rules: list[RoutingRule] = await _run_collector(
        graph,
        "routing_rules",
        "optional",
        lambda: list_routing_rules(client),
        default=[],
        required_paths=("/v1/routing-rules",),
        available_paths=available_paths,
    )
    for r_item in rules:
        graph.add_entity(
            GraphEntity(
                id=f"rule:{r_item.name}",
                type=EntityType.ROUTING_RULE,
                name=r_item.name,
                properties={"mode": r_item.mode},
            )
        )

    selectors: list[ContentSelector] = await _run_collector(
        graph,
        "content_selectors",
        "optional",
        lambda: list_content_selectors(client),
        default=[],
        required_paths=("/v1/security/content-selectors",),
        available_paths=available_paths,
    )
    for s_item in selectors:
        graph.add_entity(GraphEntity(id=f"selector:{s_item.name}", type=EntityType.CONTENT_SELECTOR, name=s_item.name))

    repos: list[Repository] = await _run_collector(
        graph,
        "repositories",
        "core",
        lambda: list_repositories(client),
        default=[],
        required_paths=("/v1/repositories",),
        available_paths=available_paths,
    )
    repos = await _run_collector(
        graph,
        "repository_details",
        "experimental",
        lambda: enrich_repositories_with_details(client, repos, available_paths),
        default=repos,
    )
    if repos and not any(_blobstore_name(repo.attributes) for repo in repos):
        graph.add_limitation(
            "Repository detail endpoints did not provide storage metadata; repository-to-blobstore relationships may be incomplete."
        )
    for repo in repos:
        repo_id = f"repo:{repo.name}"
        graph.add_entity(
            GraphEntity(
                id=repo_id,
                type=EntityType.REPOSITORY,
                name=repo.name,
                properties={"format": repo.format, "type": repo.type, "online": repo.online, "url": repo.url},
            )
        )
        graph.add_relationship(
            GraphRelationship(source_id=instance_id, target_id=repo_id, type=RelationshipType.MANAGED_BY)
        )

        attrs = repo.attributes
        bs_name = _blobstore_name(attrs)
        if bs_name:
            graph.add_relationship(
                GraphRelationship(source_id=repo_id, target_id=f"blobstore:{bs_name}", type=RelationshipType.USES_BLOBSTORE)
            )

        if repo.type == "group":
            for member in (attrs.get("group") or {}).get("memberNames", []):
                graph.add_relationship(
                    GraphRelationship(source_id=repo_id, target_id=f"repo:{member}", type=RelationshipType.MEMBER_OF_GROUP)
                )

        for policy_name in (attrs.get("cleanup") or {}).get("policyNames", []):
            graph.add_relationship(
                GraphRelationship(
                    source_id=repo_id,
                    target_id=f"policy:{policy_name}",
                    type=RelationshipType.APPLIES_CLEANUP_POLICY,
                )
            )

        rule_name = (attrs.get("routing") or {}).get("name") or attrs.get("routingRuleName") or attrs.get("routingRule")
        if rule_name:
            graph.add_relationship(
                GraphRelationship(source_id=repo_id, target_id=f"rule:{rule_name}", type=RelationshipType.USES_ROUTING_RULE)
            )

    privs: list[Privilege] = await _run_collector(
        graph,
        "security_privileges",
        "optional",
        lambda: list_privileges(client),
        default=[],
        required_paths=("/v1/security/privileges",),
        available_paths=available_paths,
    )
    for priv in privs:
        graph.add_entity(
            GraphEntity(
                id=f"privilege:{priv.name}",
                type=EntityType.PRIVILEGE,
                name=priv.name,
                properties={"type": priv.type},
            )
        )

    roles: list[Role] = await _run_collector(
        graph,
        "security_roles",
        "optional",
        lambda: list_roles(client),
        default=[],
        required_paths=("/v1/security/roles",),
        available_paths=available_paths,
    )
    for role in roles:
        role_id = f"role:{role.id}"
        graph.add_entity(GraphEntity(id=role_id, type=EntityType.ROLE, name=role.name))
        for p_name in role.privileges:
            graph.add_relationship(
                GraphRelationship(source_id=role_id, target_id=f"privilege:{p_name}", type=RelationshipType.HAS_PRIVILEGE)
            )
        for sr_name in role.roles:
            graph.add_relationship(
                GraphRelationship(source_id=role_id, target_id=f"role:{sr_name}", type=RelationshipType.ASSIGNED_ROLE)
            )

    users: list[User] = await _run_collector(
        graph,
        "security_users",
        "optional",
        lambda: list_users(client),
        default=[],
        required_paths=("/v1/security/users",),
        available_paths=available_paths,
    )
    for user in users:
        user_id = f"user:{user.userId}"
        graph.add_entity(GraphEntity(id=user_id, type=EntityType.USER, name=user.userId, properties={"status": user.status}))
        for r_name in user.roles:
            graph.add_relationship(
                GraphRelationship(source_id=user_id, target_id=f"role:{r_name}", type=RelationshipType.ASSIGNED_ROLE)
            )

    tasks: list[NexusTask] = await _run_collector(
        graph,
        "tasks",
        "optional",
        lambda: list_tasks(client),
        default=[],
        required_paths=("/v1/tasks",),
        available_paths=available_paths,
    )
    for task in tasks:
        task_id = f"task:{task.id}"
        graph.add_entity(
            GraphEntity(
                id=task_id,
                type=EntityType.TASK,
                name=task.name,
                properties={"type": task.type, "status": task.status},
            )
        )
        graph.add_relationship(GraphRelationship(source_id=instance_id, target_id=task_id, type=RelationshipType.RUNS_TASK))

    return graph


async def _discover_capabilities(client: NexusClient, graph: KnowledgeGraph) -> dict[str, Any]:
    try:
        swagger = await client.request("GET", "/service/rest/swagger.json")
    except NexusApiError as exc:
        message = f"OpenAPI discovery failed; collector availability is inferred by calling endpoints. Error: {exc}"
        graph.add_warning(message)
        graph.add_limitation(message)
        graph.record_collector("openapi_discovery", "core", "failed", str(exc))
        capabilities: dict[str, Any] = {"openapi_available": False, "paths": []}
        graph.metadata["capabilities"] = capabilities
        return capabilities

    paths = sorted(swagger.get("paths", {}).keys()) if isinstance(swagger, dict) else []
    capabilities = {
        "openapi_available": True,
        "version": swagger.get("info", {}).get("version") if isinstance(swagger, dict) else None,
        "paths": paths,
    }
    graph.metadata["capabilities"] = capabilities
    graph.record_collector("openapi_discovery", "core", "ok")
    return capabilities


async def _run_collector(
    graph: KnowledgeGraph,
    name: str,
    kind: CollectorKind,
    collect: Callable[[], Awaitable[Any]],
    default: Any,
    required_paths: tuple[str, ...] = (),
    available_paths: set[str] | None = None,
) -> Any:
    if available_paths and required_paths and not any(path in available_paths for path in required_paths):
        message = f"{name} skipped: none of {', '.join(required_paths)} is advertised by Nexus OpenAPI."
        graph.record_collector(name, kind, "skipped", message)
        graph.add_limitation(message)
        if kind == "core":
            raise RuntimeError(message)
        return default

    try:
        result = await collect()
    except Exception as exc:
        message = f"{name} unavailable: {exc}"
        graph.record_collector(name, kind, "failed", message)
        graph.add_limitation(message)
        if kind == "core":
            raise
        return default

    graph.record_collector(name, kind, "ok")
    return result


def _blobstore_name(attributes: dict[str, Any]) -> str | None:
    storage = attributes.get("storage") or {}
    if isinstance(storage, dict):
        value = storage.get("blobStoreName")
        return str(value) if value else None
    return None
