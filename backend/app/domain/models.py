from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> str:
    """统一生成 UTC 时间，避免不同机器的时间格式不一致。"""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Document:
    """文档在导入过程中的最小领域对象。"""
    title: str
    document_type: str = "note"
    industry: str | None = None
    author: str | None = None
    language: str | None = None
    trust_level: str = "medium"
    project_stage: str = "learning"
    keywords: list[str] = field(default_factory=list)
    related_products: list[str] = field(default_factory=list)
    version: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "pending"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class DocumentChunk:
    """文档的可检索片段；location 保存页码或章节信息。"""
    document_id: str
    sequence: int
    content: str
    location: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
