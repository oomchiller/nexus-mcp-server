from typing import Any, Dict, List, Optional
from .entities import GraphEntity, GraphRelationship, EntityType, RelationshipType

class KnowledgeGraph:
    """In-memory semantic graph representing the Nexus environment."""

    def __init__(self) -> None:
        self.entities: Dict[str, GraphEntity] = {}
        self.relationships: List[GraphRelationship] = []
        self._adjacency_list: Dict[str, List[GraphRelationship]] = {}
        self._reverse_adjacency_list: Dict[str, List[GraphRelationship]] = {}
        self.metadata: Dict[str, Any] = {
            "collectors": [],
            "limitations": [],
            "warnings": [],
            "capabilities": {},
        }

    def add_entity(self, entity: GraphEntity) -> None:
        self.entities[entity.id] = entity
        if entity.id not in self._adjacency_list:
            self._adjacency_list[entity.id] = []
        if entity.id not in self._reverse_adjacency_list:
            self._reverse_adjacency_list[entity.id] = []

    def add_relationship(self, rel: GraphRelationship) -> None:
        if rel.source_id not in self.entities or rel.target_id not in self.entities:
            # Skip dangling relationships for robust building
            return

        self.relationships.append(rel)
        self._adjacency_list[rel.source_id].append(rel)
        self._reverse_adjacency_list[rel.target_id].append(rel)

    def add_limitation(self, message: str) -> None:
        if message not in self.metadata["limitations"]:
            self.metadata["limitations"].append(message)

    def add_warning(self, message: str) -> None:
        if message not in self.metadata["warnings"]:
            self.metadata["warnings"].append(message)

    def record_collector(
        self,
        name: str,
        kind: str,
        status: str,
        message: str | None = None,
    ) -> None:
        record = {"name": name, "kind": kind, "status": status}
        if message:
            record["message"] = message
        self.metadata["collectors"].append(record)

    def get_entity(self, entity_id: str) -> Optional[GraphEntity]:
        return self.entities.get(entity_id)

    def get_entities_by_type(self, entity_type: EntityType) -> List[GraphEntity]:
        return [e for e in self.entities.values() if e.type == entity_type]

    def get_outgoing_relationships(self, entity_id: str, rel_type: Optional[RelationshipType] = None) -> List[GraphRelationship]:
        rels = self._adjacency_list.get(entity_id, [])
        if rel_type:
            return [r for r in rels if r.type == rel_type]
        return rels

    def get_incoming_relationships(self, entity_id: str, rel_type: Optional[RelationshipType] = None) -> List[GraphRelationship]:
        rels = self._reverse_adjacency_list.get(entity_id, [])
        if rel_type:
            return [r for r in rels if r.type == rel_type]
        return rels

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "entities": [e.model_dump() for e in self.entities.values()],
            "relationships": [r.model_dump() for r in self.relationships]
        }
