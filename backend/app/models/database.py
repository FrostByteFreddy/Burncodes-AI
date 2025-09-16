from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

class SourceType(str, Enum):
    URL = "URL"
    FILE = "FILE"

class SourceStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class TenantFineTune(BaseModel):
    id: Optional[int] = None
    tenant_id: UUID
    trigger: str
    instruction: str

class TenantSource(BaseModel):
    id: Optional[int] = None
    tenant_id: UUID
    source_type: SourceType
    source_location: str
    status: SourceStatus

class Tenant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str
    intro_message: str
    system_persona: str
    rag_prompt_template: str
    fine_tune_rules: List[TenantFineTune] = []
    sources: List[TenantSource] = []
