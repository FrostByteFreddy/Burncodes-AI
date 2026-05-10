from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceType(str, Enum):
    URL = "URL"       # crawled web page
    FILE = "FILE"     # user-uploaded file
    FILE_URL = "FILE_URL"  # file link discovered during a crawl (shown as FILE in UI)


class SourceStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    UNSUPPORTED = "UNSUPPORTED"  # file type not accepted by File Search


class CrawlMode(str, Enum):
    SOUP = "soup"                     # httpx + trafilatura, no browser, no LLM
    PLAYWRIGHT = "playwright"         # Crawl4AI + Playwright, heuristic chunking
    PLAYWRIGHT_LLM = "playwright_llm" # Crawl4AI + Playwright + LLM (default)


class CrawlingStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

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
    status_code: Optional[int] = None
    gemini_document_name: Optional[str] = None  # File Search doc resource name (for deletion)
    created_at: Optional[str] = None


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
    crawl_mode: CrawlMode = CrawlMode.PLAYWRIGHT_LLM
    gemini_file_store_name: Optional[str] = None  # Gemini File Search Store resource name
    fine_tune_rules: List[TenantFineTune] = []
    sources: List[TenantSource] = []


class CrawlingJob(BaseModel):
    id: Optional[int] = None
    tenant_id: UUID
    start_url: str
    max_depth: int
    status: CrawlingStatus = CrawlingStatus.PENDING
    excluded_urls: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CrawlingTask(BaseModel):
    id: Optional[int] = None
    job_id: int
    url: str
    depth: int
    status: CrawlingStatus = CrawlingStatus.PENDING
    parent_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
