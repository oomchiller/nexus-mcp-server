import asyncio
from typing import Any

from nexus_mcp_server.docs_engine.generator import DocsGenerator
from nexus_mcp_server.errors import NexusNotFoundError
from nexus_mcp_server.iac.generator import IaCContextGenerator
from nexus_mcp_server.knowledge_graph.builder import build_knowledge_graph
from nexus_mcp_server.knowledge_graph.entities import RelationshipType
from nexus_mcp_server.knowledge_graph.query_engine import QueryEngine


class Nexus370SparseClient:
    base_url = "http://nexus.example"

    async def request(self, method: str, path: str) -> Any:
        if path == "/service/rest/swagger.json":
            return {
                "info": {"version": "3.70.1-02"},
                "paths": {
                    "/v1/status": {"get": {}},
                    "/v1/repositories": {"get": {}},
                    "/v1/repositories/maven2/proxy/{repositoryName}": {"get": {}},
                    "/v1/blobstores": {"get": {}},
                    "/v1/tasks": {"get": {}},
                },
            }
        if path == "/service/rest/v1/status":
            return {"version": "3.70.1-02", "state": "STARTED"}
        if path == "/service/rest/v1/repositories":
            return [
                {
                    "name": "central",
                    "format": "maven2",
                    "type": "proxy",
                    "url": "http://nexus.example/repository/central",
                    "attributes": {"proxy": {"remoteUrl": "https://repo1.maven.org/maven2/"}},
                }
            ]
        if path == "/service/rest/v1/repositories/maven2/proxy/central":
            return {
                "name": "central",
                "format": "maven2",
                "type": "proxy",
                "online": True,
                "storage": {"blobStoreName": "default"},
            }
        if path == "/service/rest/v1/blobstores":
            return [{"name": "default", "type": "File"}]
        if path == "/service/rest/v1/tasks":
            return {
                "items": [
                    {
                        "id": "task-1",
                        "name": "Compact blob store",
                        "type": "blobstore.compact",
                        "currentState": "WAITING",
                    }
                ]
            }
        raise NexusNotFoundError("Resource not found", 404, {"path": path})


class OptionalEndpointFailureClient(Nexus370SparseClient):
    async def request(self, method: str, path: str) -> Any:
        if path == "/service/rest/swagger.json":
            data = await super().request(method, path)
            data["paths"].update(
                {
                    "/v1/routing-rules": {"get": {}},
                    "/v1/security/content-selectors": {"get": {}},
                    "/v1/security/users": {"get": {}},
                    "/v1/security/roles": {"get": {}},
                    "/v1/security/privileges": {"get": {}},
                }
            )
            return data
        if path in {
            "/service/rest/v1/routing-rules",
            "/service/rest/v1/security/content-selectors",
            "/service/rest/v1/security/users",
            "/service/rest/v1/security/roles",
            "/service/rest/v1/security/privileges",
        }:
            raise NexusNotFoundError("Resource not found", 404, {"path": path})
        return await super().request(method, path)


def test_graph_tolerates_nexus_370_sparse_repository_list() -> None:
    graph = asyncio.run(build_knowledge_graph(Nexus370SparseClient()))  # type: ignore[arg-type]

    repo = graph.get_entity("repo:central")
    assert repo is not None
    assert repo.properties["online"] is True
    assert graph.get_entity("task:task-1") is not None
    assert graph.metadata["capabilities"]["version"] == "3.70.1-02"


def test_graph_reports_missing_optional_endpoints_as_limitations() -> None:
    graph = asyncio.run(build_knowledge_graph(Nexus370SparseClient()))  # type: ignore[arg-type]

    limitations = "\n".join(graph.metadata["limitations"])
    assert "cleanup_policies skipped" in limitations
    assert "routing_rules skipped" in limitations
    assert "content_selectors skipped" in limitations
    assert "security_users skipped" in limitations


def test_optional_endpoint_404_does_not_fail_graph_tools() -> None:
    graph = asyncio.run(build_knowledge_graph(OptionalEndpointFailureClient()))  # type: ignore[arg-type]

    architecture = QueryEngine(graph).explain_storage_strategy()
    catalog = DocsGenerator(graph).generate_repository_catalog_md()
    inventory = IaCContextGenerator(graph).generate_inventory_json()

    assert architecture["findings"][0]["details"][0]["managed_repositories"] == ["central"]
    assert "## Limitations" in catalog
    assert '"metadata"' in inventory
    assert "security_privileges unavailable" in "\n".join(graph.metadata["limitations"])


def test_repository_detail_creates_blobstore_relationship() -> None:
    graph = asyncio.run(build_knowledge_graph(Nexus370SparseClient()))  # type: ignore[arg-type]

    relationships = graph.get_outgoing_relationships("repo:central", RelationshipType.USES_BLOBSTORE)
    assert len(relationships) == 1
    assert relationships[0].target_id == "blobstore:default"
