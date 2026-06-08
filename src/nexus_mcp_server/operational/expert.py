from typing import Dict, Any, List
from ..knowledge_graph.graph import KnowledgeGraph
from ..knowledge_graph.entities import EntityType, RelationshipType

class OperationalExpert:
    """Expert system that detects Nexus configuration smells and operational risks."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def detect_risks(self) -> List[Dict[str, Any]]:
        """Returns a list of structured findings about the Nexus environment."""
        findings = []

        # 1. Unused Blobstores
        for bs in self.graph.get_entities_by_type(EntityType.BLOBSTORE):
            incoming = self.graph.get_incoming_relationships(bs.id, RelationshipType.USES_BLOBSTORE)
            if not incoming:
                findings.append({
                    "id": "unused_blobstore",
                    "title": "Unused Blob Store",
                    "severity": "low",
                    "confidence": "high",
                    "affected_objects": [bs.name],
                    "evidence": [f"BlobStore {bs.id} has 0 incoming USES_BLOBSTORE relationships"],
                    "suggested_action": f"Verify if data in '{bs.name}' is needed. If not, consider decommissioning it to save resources."
                })

        # 2. Empty Group Repositories
        for repo in self.graph.get_entities_by_type(EntityType.REPOSITORY):
            if repo.properties.get("type") == "group":
                members = self.graph.get_outgoing_relationships(repo.id, RelationshipType.MEMBER_OF_GROUP)
                if not members:
                    findings.append({
                        "id": "empty_group",
                        "title": "Empty Group Repository",
                        "severity": "medium",
                        "confidence": "high",
                        "affected_objects": [repo.name],
                        "evidence": [f"Group {repo.id} has 0 outgoing MEMBER_OF_GROUP relationships"],
                        "suggested_action": f"Add member repositories to '{repo.name}' or remove the empty group."
                    })

        # 3. Offline Repositories
        for repo in self.graph.get_entities_by_type(EntityType.REPOSITORY):
            if not repo.properties.get("online", True):
                findings.append({
                    "id": "offline_repo",
                    "title": "Repository Offline",
                    "severity": "high",
                    "confidence": "high",
                    "affected_objects": [repo.name],
                    "evidence": [f"repo.properties.online=False for {repo.name}"],
                    "suggested_action": f"Check the health and remote connectivity of '{repo.name}'."
                })

        # 4. Orphaned Cleanup Policies
        for policy in self.graph.get_entities_by_type(EntityType.CLEANUP_POLICY):
            incoming = self.graph.get_incoming_relationships(policy.id, RelationshipType.APPLIES_CLEANUP_POLICY)
            if not incoming:
                findings.append({
                    "id": "orphaned_policy",
                    "title": "Orphaned Cleanup Policy",
                    "severity": "info",
                    "confidence": "high",
                    "affected_objects": [policy.name],
                    "evidence": [f"Policy {policy.id} has 0 incoming APPLIES_CLEANUP_POLICY relationships"],
                    "suggested_action": f"Attach policy '{policy.name}' to a repository or delete it if no longer needed."
                })

        return findings
