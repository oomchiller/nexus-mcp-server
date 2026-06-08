from typing import Optional, List, Any
from pydantic import BaseModel, Field

class Repository(BaseModel):
    name: str
    format: str = "unknown"
    type: str = "unknown"
    url: Optional[str] = None
    online: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict)

class BlobStore(BaseModel):
    name: str
    type: str = "unknown"
    blobCount: Optional[int] = None
    totalSizeInBytes: Optional[int] = None
    availableSpaceInBytes: Optional[int] = None

class Component(BaseModel):
    id: str
    repository: str = "unknown"
    format: str = "unknown"
    group: Optional[str] = None
    name: str = "unknown"
    version: Optional[str] = None

class Asset(BaseModel):
    id: str
    path: str = ""
    format: str = "unknown"
    repository: str = "unknown"

class NexusTask(BaseModel):
    id: str
    name: str = "unknown"
    type: str = "unknown"
    status: str = "unknown"
    lastRunResult: Optional[str] = None
    nextRun: Optional[str] = None

class CleanupPolicy(BaseModel):
    name: str
    format: str = "unknown"
    notes: Optional[str] = None
    criteria: dict[str, Any] = Field(default_factory=dict)

class RoutingRule(BaseModel):
    name: str
    description: Optional[str] = None
    mode: str = "unknown"
    matchers: List[str] = Field(default_factory=list)

class ContentSelector(BaseModel):
    name: str
    description: Optional[str] = None
    expression: str = ""

class User(BaseModel):
    userId: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    emailAddress: Optional[str] = None
    source: str = "unknown"
    status: str = "unknown"
    roles: List[str] = Field(default_factory=list)

class Role(BaseModel):
    id: str
    name: str = "unknown"
    description: Optional[str] = None
    privileges: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)

class Privilege(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "unknown"
    readOnly: bool = False
    properties: dict[str, Any] = Field(default_factory=dict)

class MigrationReadiness(BaseModel):
    nexus_url: str
    version: Optional[str] = None
    repository_count: int
    repositories_by_type: dict[str, int]
    blobstore_count: int
    findings: List[str]
    recommendations: List[str]
