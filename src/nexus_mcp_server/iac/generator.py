from typing import Dict, Any
from ..knowledge_graph.graph import KnowledgeGraph
from ..knowledge_graph.entities import EntityType

class IaCContextGenerator:
    """Generates IaC contexts (Terraform, Puppet) from the Knowledge Graph."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def generate_inventory_json(self) -> str:
        """Generates a structured JSON inventory of all core Nexus objects."""
        import json
        data = {
            "metadata": self.graph.metadata,
            "repositories": [e.properties for e in self.graph.get_entities_by_type(EntityType.REPOSITORY)],
            "blobstores": [e.properties for e in self.graph.get_entities_by_type(EntityType.BLOBSTORE)],
            "cleanup_policies": [e.name for e in self.graph.get_entities_by_type(EntityType.CLEANUP_POLICY)],
            "routing_rules": [e.properties for e in self.graph.get_entities_by_type(EntityType.ROUTING_RULE)],
        }
        return json.dumps(data, indent=2)

    def generate_terraform_context(self) -> str:
        """Generates a JSON context suitable for terraform-provider-nexus ingestion."""
        # Simplified representation for terraform drift analysis
        import json
        repos = {}
        for r in self.graph.get_entities_by_type(EntityType.REPOSITORY):
            repos[r.name] = {
                "format": r.properties.get("format"),
                "type": r.properties.get("type"),
                "online": r.properties.get("online")
            }
        return json.dumps({"nexus_repository": repos}, indent=2)

    def generate_puppet_context(self) -> str:
        """Generates a YAML context suitable for Puppet Hiera (nexus module)."""
        import yaml
        repos = {}
        for r in self.graph.get_entities_by_type(EntityType.REPOSITORY):
            repos[r.name] = {
                "ensure": "present",
                "format": r.properties.get("format"),
                "type": r.properties.get("type")
            }
        return str(yaml.dump({"nexus::repositories": repos}))

    def detect_drift(self, declared_state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect drift between live state and a provided declared state (JSON/YAML)."""
        live_repos = {r.name: r for r in self.graph.get_entities_by_type(EntityType.REPOSITORY)}
        declared_repos = declared_state.get("repositories", {})

        drift: Dict[str, Any] = {
            "missing_in_live": [],
            "extra_in_live": [],
            "changed": [],
            "unsupported": [],
            "limitations": ["This version compares Repository name, format, and type."]
        }

        for name, config in declared_repos.items():
            if name not in live_repos:
                drift["missing_in_live"].append(name)
            else:
                live = live_repos[name]
                if live.properties.get("format") != config.get("format") or live.properties.get("type") != config.get("type"):
                    drift["changed"].append({
                        "name": name,
                        "live": {"format": live.properties.get("format"), "type": live.properties.get("type")},
                        "declared": config
                    })

        for name in live_repos:
            if name not in declared_repos:
                drift["extra_in_live"].append(name)

        return drift
