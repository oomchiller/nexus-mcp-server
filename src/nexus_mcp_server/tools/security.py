from typing import List, Any, Dict
from ..nexus_client import NexusClient
from ..models import User, Role, Privilege

async def list_users(client: NexusClient) -> List[User]:
    """List all users."""
    data = await client.request("GET", "/service/rest/v1/security/users")
    return [User(**item) for item in data]

async def list_roles(client: NexusClient) -> List[Role]:
    """List all roles."""
    data = await client.request("GET", "/service/rest/v1/security/roles")
    return [Role(**item) for item in data]

async def list_privileges(client: NexusClient) -> List[Privilege]:
    """List all privileges."""
    data = await client.request("GET", "/service/rest/v1/security/privileges")
    return [Privilege(**item) for item in data]

async def get_anonymous_status(client: NexusClient) -> Dict[str, Any]:
    """Get anonymous access status."""
    data = await client.request("GET", "/service/rest/v1/security/anonymous")
    return dict(data) if isinstance(data, dict) else {"status": data}

async def list_realms(client: NexusClient) -> List[str]:
    """List active security realms."""
    data = await client.request("GET", "/service/rest/v1/security/realms/active")
    return list(data) if isinstance(data, list) else []
