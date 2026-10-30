from typing import Dict, Any

from ..errors import NexusApiError
from ..nexus_client import NexusClient

async def get_system_status(client: NexusClient) -> Dict[str, Any]:
    """Get Nexus system status."""
    data = await client.request("GET", "/service/rest/v1/status")
    return dict(data) if isinstance(data, dict) else {"status": data}

async def get_system_metrics(client: NexusClient) -> Dict[str, Any]:
    """Get Nexus system metrics."""
    # This might require specific permissions or might be under a different path
    # in some versions, but standard is /service/rest/v1/status/check
    data = await client.request("GET", "/service/rest/v1/status/check")
    return dict(data) if isinstance(data, dict) else {"status": data}

async def readiness_basic_check(client: NexusClient) -> Dict[str, Any]:
    """Perform a basic readiness check."""
    status = await get_system_status(client)
    # Check if we can list repositories as a proxy for API health
    try:
        await client.request("GET", "/service/rest/v1/repositories")
        api_ok = True
    except NexusApiError:
        api_ok = False

    return {
        "status": status,
        "api_reachable": api_ok,
        "ready": api_ok # Simple heuristic
    }
