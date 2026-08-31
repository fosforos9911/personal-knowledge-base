from dataclasses import dataclass


@dataclass(frozen=True)
class SearchFilters:
    """搜索条件；先保留最常用的个人知识库过滤项。"""

    industry: str | None = None
    document_type: str | None = None
    project_stage: str | None = None
    trust_level: str | None = None


class SearchService:
    """组织关键词检索、过滤和引用组装，不直接处理 HTTP。"""

    def __init__(self, repository):
        self.repository = repository

    def search(self, query: str, filters: SearchFilters | None = None) -> list[dict]:
        """先用 FTS5 找候选，再按文档元数据过滤并附上定位信息。"""
        normalized = self._normalize_query(query)
        if not normalized:
            return []
        candidates = self.repository.search_chunks(normalized)
        return self._apply_filters(candidates, filters or SearchFilters())

    @staticmethod
    def _normalize_query(query: str) -> str:
        """去掉常见提问尾词，让全文检索先抓住工程主题。

        这里只做轻量清洗，不宣称已经具备语义理解；真正的意图识别和
        向量召回会在后续阶段加入。
        """
        normalized = query.strip().rstrip("？?").strip()
        for suffix in ("怎么做", "如何做", "是什么", "有哪些", "吗", "呢", "？", "?"):
            normalized = normalized.removesuffix(suffix).strip()
        return normalized

    @staticmethod
    def _apply_filters(results: list[dict], filters: SearchFilters) -> list[dict]:
        """过滤放在服务层，避免把 SQLite 条件泄露到 API 和前端。"""
        fields = {
            "industry": filters.industry,
            "document_type": filters.document_type,
            "project_stage": filters.project_stage,
            "trust_level": filters.trust_level,
        }
        return [
            result for result in results
            if all(not expected or result.get(field) == expected for field, expected in fields.items())
        ]
