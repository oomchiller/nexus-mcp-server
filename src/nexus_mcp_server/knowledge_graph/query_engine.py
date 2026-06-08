from .entities import EntityType, RelationshipType
from .graph import KnowledgeGraph
from typing import Dict, Any

class QueryEngine:
    """Interrogates the Knowledge Graph to answer high-level architectural questions with evidence."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def _get_name(self, entity_id: str) -> str:
        ent = self.graph.get_entity(entity_id)
        return ent.name if ent else "Unknown"

    def explain_storage_strategy(self) -> Dict[str, Any]:
        """Explains how storage is utilized across the instance with evidence."""
        blobstores = self.graph.get_entities_by_type(EntityType.BLOBSTORE)

        details = []
        for bs in blobstores:
            incoming = self.graph.get_incoming_relationships(bs.id, RelationshipType.USES_BLOBSTORE)
            repo_names = [self._get_name(r.source_id) for r in incoming]

            details.append({
                "blobstore": bs.name,
                "type": bs.properties.get("type", "unknown"),
                "managed_repositories": repo_names,
                "evidence": [f"Relationship: Repository {name} -> USES_BLOBSTORE -> {bs.name}" for name in repo_names]
            })

        return {
            "summary": f"Data is distributed across {len(blobstores)} blob stores.",
            "findings": [
                {
                    "id": "storage_topology",
                    "title": "Storage Topology",
                    "severity": "info",
                    "confidence": "high",
                    "details": details,
                    "evidence": [f"Entity: {bs.name} exists" for bs in blobstores]
                }
            ],
            "limitations": [
                "Real-time disk usage requires direct OS/Cloud access, not available via REST API.",
                *self.graph.metadata.get("limitations", []),
            ]
        }

    def explain_repository(self, repo_name: str) -> Dict[str, Any]:
        """Provides a complete semantic picture of a single repository with evidence."""
        repo_id = f"repo:{repo_name}"
        repo = self.graph.get_entity(repo_id)
        if not repo:
            return {"error": f"Repository '{repo_name}' not found."}

        storage_rels = self.graph.get_outgoing_relationships(repo_id, RelationshipType.USES_BLOBSTORE)
        storage_name = self._get_name(storage_rels[0].target_id) if storage_rels else "Unknown"

        policy_rels = self.graph.get_outgoing_relationships(repo_id, RelationshipType.APPLIES_CLEANUP_POLICY)
        policies = [self._get_name(r.target_id) for r in policy_rels]

        group_rels = self.graph.get_incoming_relationships(repo_id, RelationshipType.MEMBER_OF_GROUP)
        parent_groups = [self._get_name(r.source_id) for r in group_rels]

        return {
            "summary": f"Repository '{repo_name}' is a {repo.properties.get('format')} {repo.properties.get('type')} repository.",
            "findings": [
                {
                    "id": "repo_config",
                    "severity": "info",
                    "confidence": "high",
                    "evidence": [
                        f"repo.type={repo.properties.get('type')}",
                        f"repo.storage={storage_name}",
                        f"repo.cleanup_policies={policies}"
                    ],
                    "details": {
                        "storage_backend": storage_name,
                        "cleanup_policies": policies,
                        "member_of": parent_groups
                    }
                }
            ],
            "limitations": self.graph.metadata.get("limitations", []),
        }

    def explain_security_model(self) -> Dict[str, Any]:
        """Explains the security posture (Users, Roles, Privileges) with evidence."""
        users = self.graph.get_entities_by_type(EntityType.USER)
        roles = self.graph.get_entities_by_type(EntityType.ROLE)
        privs = self.graph.get_entities_by_type(EntityType.PRIVILEGE)

        active_users = [u for u in users if u.properties.get("status") == "active"]

        return {
            "summary": f"The instance has {len(users)} users, {len(roles)} roles, and {len(privs)} privileges defined.",
            "findings": [
                {
                    "id": "user_count",
                    "title": "User Inventory",
                    "severity": "info",
                    "confidence": "high",
                    "evidence": [f"security/users returns {len(users)} items"],
                    "details": {"active_users": len(active_users), "total_users": len(users)}
                }
            ],
            "limitations": [
                "External LDAP/SAML user details may be incomplete depending on realm configuration.",
                *self.graph.metadata.get("limitations", []),
            ]
        }
