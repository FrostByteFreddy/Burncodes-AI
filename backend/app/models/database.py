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
    input_tokens: int = 0
    output_tokens: int = 0
    cost_chf: float = 0.0

class Tenant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str
    intro_message: str
    system_persona: str
    rag_prompt_template: str
    doc_language: Optional[str] = None
    translation_target: Optional[str] = None
    widget_config: Optional[dict] = None
    fine_tune_rules: List[TenantFineTune] = []
    sources: List[TenantSource] = []

class CrawlingStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CrawlingJob(BaseModel):
    id: Optional[int] = None
    tenant_id: UUID
    start_url: str
    max_depth: int
    status: CrawlingStatus = CrawlingStatus.PENDING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CrawlingTask(BaseModel):
    id: Optional[int] = None
    job_id: int
    url: str
    depth: int
    status: CrawlingStatus = CrawlingStatus.PENDING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
