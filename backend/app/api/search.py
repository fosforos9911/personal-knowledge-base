from fastapi import APIRouter, Query

from app.config import settings
from app.services.search_service import SearchFilters


router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    industry: str | None = None,
    document_type: str | None = None,
    project_stage: str | None = None,
    trust_level: str | None = None,
) -> dict[str, object]:
    """执行全文检索并返回分块级引用，正文只来自本地资料库。"""
    results = settings.search_service.search(
        q, SearchFilters(industry, document_type, project_stage, trust_level)
    )
    return {"query": q, "count": len(results), "results": results}
