from typing import Any, Dict, Optional, Literal
from ..nexus_client import NexusClient
from ..safety import redact_secrets, validate_operation, validate_path
from ..config import Settings

async def call_raw_api(
    client: NexusClient,
    settings: Settings,
    method: Literal["GET", "HEAD", "POST", "PUT", "DELETE"],
    path: str,
    query: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call a raw Nexus API endpoint with safety checks."""
    validate_operation(settings, method, is_raw_api=True)
    safe_path = validate_path(path)

    response = await client.request(
        method=method,
        path=safe_path,
        params=query,
        json=json_body
    )

    return {
        "status": "success",
        "data": redact_secrets(response, settings.all_secrets)
    }
