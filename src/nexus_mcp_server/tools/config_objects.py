from typing import List, Optional
from ..errors import NexusNotFoundError
from ..nexus_client import NexusClient
from ..models import CleanupPolicy, RoutingRule, ContentSelector

async def list_cleanup_policies(client: NexusClient) -> List[CleanupPolicy]:
    """List all cleanup policies."""
    try:
        data = await client.request("GET", "/service/rest/v1/cleanup")
    except NexusNotFoundError:
        return []
    return [CleanupPolicy(**item) for item in data]

async def list_routing_rules(client: NexusClient) -> List[RoutingRule]:
    """List all routing rules."""
    data = await client.request("GET", "/service/rest/v1/routing-rules")
    return [RoutingRule(**item) for item in data]

async def get_routing_rule(client: NexusClient, name: str) -> Optional[RoutingRule]:
    """Get a specific routing rule by name."""
    try:
        data = await client.request("GET", f"/service/rest/v1/routing-rules/{name}")
        return RoutingRule(**data)
    except Exception:
        return None

async def list_content_selectors(client: NexusClient) -> List[ContentSelector]:
    """List all content selectors."""
    # Note: path might vary or requires specific permissions
    data = await client.request("GET", "/service/rest/v1/security/content-selectors")
    return [ContentSelector(**item) for item in data]
