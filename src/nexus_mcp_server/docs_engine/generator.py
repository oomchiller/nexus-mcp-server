from ..knowledge_graph.graph import KnowledgeGraph
from ..knowledge_graph.entities import EntityType, RelationshipType

class DocsGenerator:
    """Generates documentation from the Knowledge Graph."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def generate_architecture_md(self) -> str:
        instance = self.graph.get_entities_by_type(EntityType.INSTANCE)[0]
        repos = self.graph.get_entities_by_type(EntityType.REPOSITORY)
        blobs = self.graph.get_entities_by_type(EntityType.BLOBSTORE)

        md = "# Nexus Architecture Overview\n\n"
        md += f"**Target:** {instance.name}\n"
        md += f"**Version:** {instance.properties.get('version', 'Unknown')}\n\n"

        md += "## Summary\n"
        md += f"This instance manages {len(repos)} repositories backed by {len(blobs)} blob stores.\n\n"

        md += "## Storage Topology\n"
        for bs in blobs:
            incoming = self.graph.get_incoming_relationships(bs.id, RelationshipType.USES_BLOBSTORE)
            md += f"- **{bs.name}** ({bs.properties.get('type')}): Serves {len(incoming)} repositories.\n"

        md += self._limitations_md()

        return md

    def generate_repository_catalog_md(self) -> str:
        repos = self.graph.get_entities_by_type(EntityType.REPOSITORY)

        md = "# Repository Catalog\n\n"

        for r in sorted(repos, key=lambda x: (x.properties.get("type", ""), x.name)):
            repo_type = r.properties.get("type", "unknown").upper()
            repo_format = r.properties.get("format", "unknown")
            md += f"### {r.name}\n"
            md += f"- **Type:** {repo_type}\n"
            md += f"- **Format:** {repo_format}\n"
            md += f"- **Status:** {'Online' if r.properties.get('online') else 'Offline'}\n"

            # Connections
            storage = self.graph.get_outgoing_relationships(r.id, RelationshipType.USES_BLOBSTORE)
            if storage and self.graph.get_entity(storage[0].target_id):
                md += f"- **Blob Store:** {self.graph.get_entity(storage[0].target_id).name}\n" # type: ignore

            groups = self.graph.get_incoming_relationships(r.id, RelationshipType.MEMBER_OF_GROUP)
            if groups:
                group_names = [self.graph.get_entity(g.source_id).name for g in groups if self.graph.get_entity(g.source_id)] # type: ignore
                md += f"- **Member of Groups:** {', '.join(group_names)}\n"

            md += "\n"

        md += self._limitations_md()

        return md

    def _limitations_md(self) -> str:
        limitations = self.graph.metadata.get("limitations", [])
        if not limitations:
            return ""

        md = "## Limitations\n"
        for item in limitations:
            md += f"- {item}\n"
        return f"\n{md}"
