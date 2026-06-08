from typing import Any, Dict, List, Optional
from .nexus_client import NexusClient
from .logging import get_logger

logger = get_logger("openapi")

class OpenApiHelper:
    """Helper for fetching and parsing Nexus OpenAPI docs."""

    def __init__(self, client: NexusClient):
        self.client = client
        self._spec: Optional[Dict[str, Any]] = None

    async def fetch_spec(self, force: bool = False) -> Dict[str, Any]:
        """Fetch /service/rest/swagger.json."""
        if self._spec is None or force:
            logger.info("Fetching OpenAPI spec from Nexus...")
            self._spec = await self.client.request("GET", "/service/rest/swagger.json")
        return self._spec

    async def get_paths(self) -> set[str]:
        """Return available REST paths from live OpenAPI documentation."""
        spec = await self.fetch_spec()
        return set(spec.get("paths", {}).keys())

    async def has_path(self, path: str, method: str = "get") -> bool:
        """Check whether a path/method exists in live OpenAPI documentation."""
        spec = await self.fetch_spec()
        methods = spec.get("paths", {}).get(path, {})
        return method.lower() in methods

    async def list_operations(self) -> List[Dict[str, Any]]:
        """List all operations from the spec."""
        spec = await self.fetch_spec()
        operations = []

        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, op in methods.items():
                if not isinstance(op, dict):
                    continue
                operations.append({
                    "operationId": op.get("operationId"),
                    "method": method.upper(),
                    "path": path,
                    "tags": op.get("tags", []),
                    "summary": op.get("summary", ""),
                })
        return operations

    async def find_operations(self, query: str) -> List[Dict[str, Any]]:
        """Search operations by various fields."""
        ops = await self.list_operations()
        query = query.lower()
        results = []
        for op in ops:
            search_fields = [
                op["operationId"] or "",
                op["method"],
                op["path"],
                op["summary"],
                " ".join(op["tags"])
            ]
            if any(query in f.lower() for f in search_fields):
                results.append(op)
        return results

    async def get_operation_schema(self, operation_id: Optional[str] = None, method_path: Optional[str] = None) -> Dict[str, Any]:
        """Get request/response schema for an operation."""
        spec = await self.fetch_spec()

        target_op = None
        if operation_id:
            for path, methods in spec.get("paths", {}).items():
                for method, op in methods.items():
                    if op.get("operationId") == operation_id:
                        target_op = op
                        break
                if target_op:
                    break
        elif method_path:
            # Expected format: "GET /service/rest/v1/repositories"
            parts = method_path.split(" ", 1)
            if len(parts) == 2:
                m, p = parts[0].lower(), parts[1]
                target_op = spec.get("paths", {}).get(p, {}).get(m)

        if not target_op:
            return {"error": "Operation not found"}

        return {
            "parameters": target_op.get("parameters", []),
            "responses": target_op.get("responses", {}),
            "summary": target_op.get("summary", "")
        }

    async def generate_capability_map(self) -> Dict[str, List[Dict[str, str]]]:
        """Group operations by functional domain."""
        ops = await self.list_operations()
        cmap: Dict[str, List[Dict[str, str]]] = {
            "repositories": [],
            "blobstores": [],
            "components_assets": [],
            "tasks": [],
            "security": [],
            "system": [],
            "lifecycle": [],
            "other": []
        }

        for op in ops:
            path = op["path"]
            entry = {"method": op["method"], "path": path, "summary": op["summary"]}

            if "/repositories" in path:
                cmap["repositories"].append(entry)
            elif "/blobstores" in path:
                cmap["blobstores"].append(entry)
            elif "/components" in path or "/assets" in path:
                cmap["components_assets"].append(entry)
            elif "/tasks" in path:
                cmap["tasks"].append(entry)
            elif "/security" in path:
                cmap["security"].append(entry)
            elif "/status" in path or "/metrics" in path:
                cmap["system"].append(entry)
            elif "/support" in path:
                cmap["lifecycle"].append(entry)
            else:
                cmap["other"].append(entry)
        return cmap
