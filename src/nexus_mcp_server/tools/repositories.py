from typing import Any, List, Optional, Dict
from urllib.parse import quote
from ..errors import NexusApiError, NexusNotFoundError
from ..nexus_client import NexusClient
from ..models import Repository


def _merge_repository_attributes(summary: Repository, details: dict[str, Any]) -> Repository:
    attributes = dict(summary.attributes)
    for key in ("storage", "group", "cleanup", "proxy", "routingRule", "routingRuleName"):
        if key in details:
            attributes[key] = details[key]

    return Repository(
        name=summary.name,
        format=details.get("format", summary.format),
        type=details.get("type", summary.type),
        url=summary.url,
        online=details.get("online", summary.online),
        attributes=attributes,
    )

async def list_repositories(
    client: NexusClient,
    format: Optional[str] = None,
    repository_type: Optional[str] = None
) -> List[Repository]:
    """List all repositories with optional filtering."""
    data = await client.request("GET", "/service/rest/v1/repositories")
    repos = []
    for item in data:
        if format and item.get("format") != format:
            continue
        if repository_type and item.get("type") != repository_type:
            continue

        repos.append(Repository(
            name=item["name"],
            format=item.get("format", "unknown"),
            type=item.get("type", "unknown"),
            url=item.get("url"),
            online=item.get("online", True),
            attributes=item.get("attributes") or {}
        ))
    return repos


async def enrich_repositories_with_details(
    client: NexusClient,
    repositories: List[Repository],
    available_paths: set[str],
) -> List[Repository]:
    """Fetch format/type repository details when supported by this Nexus version."""
    detail_paths = {
        path for path in available_paths
        if path.startswith("/v1/repositories/") and path.count("/") >= 4
    }
    if not detail_paths:
        return repositories

    enriched = []
    for repo in repositories:
        if repo.format == "unknown" or repo.type == "unknown":
            enriched.append(repo)
            continue
        detail_path = _repository_detail_path(repo, detail_paths)
        if not detail_path:
            enriched.append(repo)
            continue
        try:
            details = await client.request("GET", detail_path)
        except (NexusApiError, NexusNotFoundError):
            enriched.append(repo)
            continue
        if isinstance(details, dict):
            enriched.append(_merge_repository_attributes(repo, details))
        else:
            enriched.append(repo)
    return enriched


def _repository_detail_path(repo: Repository, available_paths: set[str]) -> str | None:
    """Return the concrete settings endpoint advertised for this repository."""
    for template in sorted(available_paths):
        parts = template.strip("/").split("/")
        if len(parts) < 5:
            continue
        if parts[0] != "v1" or parts[1] != "repositories":
            continue
        if parts[2] != repo.format or parts[3] != repo.type:
            continue
        if not parts[4].startswith("{"):
            continue
        encoded_name = quote(repo.name, safe="")
        concrete = template.replace(parts[4], encoded_name, 1)
        return f"/service/rest{concrete}"
    return None

async def get_repository(client: NexusClient, name: str) -> Optional[Repository]:
    """Get a specific repository by name."""
    # Nexus doesn't have a direct /repositories/{name} GET in v1 usually,
    # we might have to find it in the list or check generic settings if available.
    # However, for this tool we'll search the list for simplicity and consistency.
    repos = await list_repositories(client)
    for r in repos:
        if r.name == name:
            return r
    return None

async def find_repositories_by_type(client: NexusClient, rtype: str) -> List[Repository]:
    """Find repositories by type (hosted, proxy, group)."""
    return await list_repositories(client, repository_type=rtype)

async def find_hosted_repositories(client: NexusClient) -> Dict[str, List[Repository]]:
    """Find hosted repositories grouped by format."""
    repos = await find_repositories_by_type(client, "hosted")
    grouped: Dict[str, List[Repository]] = {}
    for r in repos:
        grouped.setdefault(r.format, []).append(r)
    return grouped

async def find_proxy_repositories(client: NexusClient) -> List[Repository]:
    """Find proxy repositories."""
    return await find_repositories_by_type(client, "proxy")

async def find_group_repositories(client: NexusClient) -> List[Repository]:
    """Find group repositories."""
    return await find_repositories_by_type(client, "group")
