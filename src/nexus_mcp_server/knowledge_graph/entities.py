from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel, Field

class EntityType(str, Enum):
    INSTANCE = "NexusInstance"
    REPOSITORY = "Repository"
    BLOBSTORE = "BlobStore"
    TASK = "Task"
    CLEANUP_POLICY = "CleanupPolicy"
    ROUTING_RULE = "RoutingRule"
    ROLE = "Role"
    PRIVILEGE = "Privilege"
    USER = "User"
    CONTENT_SELECTOR = "ContentSelector"
    CAPABILITY = "Capability"

class GraphEntity(BaseModel):
    id: str  # Unique identifier within the graph (e.g., "repo:maven-central")
    type: EntityType
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class RelationshipType(str, Enum):
    USES_BLOBSTORE = "USES_BLOBSTORE"
    APPLIES_CLEANUP_POLICY = "APPLIES_CLEANUP_POLICY"
    USES_ROUTING_RULE = "USES_ROUTING_RULE"
    MEMBER_OF_GROUP = "MEMBER_OF_GROUP"
    HAS_PRIVILEGE = "HAS_PRIVILEGE"
    ASSIGNED_ROLE = "ASSIGNED_ROLE"
    AFFECTS_REPOSITORY = "AFFECTS_REPOSITORY"
    AFFECTS_BLOBSTORE = "AFFECTS_BLOBSTORE"
    RUNS_TASK = "RUNS_TASK"
    MANAGED_BY = "MANAGED_BY"

class GraphRelationship(BaseModel):
    source_id: str
    target_id: str
    type: RelationshipType
    properties: Dict[str, Any] = Field(default_factory=dict)
