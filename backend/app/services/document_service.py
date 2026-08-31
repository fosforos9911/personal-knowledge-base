from pathlib import Path

from app.domain.models import Document, DocumentChunk


class DocumentService:
    """编排一次文档导入，不关心 HTTP、SQL 和具体解析库。"""

    def __init__(self, repository, file_store, parser_registry, chunker):
        self.repository = repository
        self.file_store = file_store
        self.parser_registry = parser_registry
        self.chunker = chunker

    def import_document(self, source: Path, document: Document) -> Document:
        """执行 pending -> processing -> ready；失败时留下 failed 状态。"""
        self.repository.create(document)
        try:
            self.repository.mark_status(document.id, "processing")
            stored_path = self.file_store.save(source, document.id)
            parsed_text = self.parser_registry.parse(stored_path)
            chunks = self.chunker.split(document.id, parsed_text)
            self.repository.replace_chunks(document.id, chunks)
            self.repository.mark_status(document.id, "ready")
            document.status = "ready"
            return document
        except Exception as exc:
            self.repository.mark_status(document.id, "failed", str(exc))
            raise


class FixedSizeChunker:
    """第一版简单分块器；后续可替换成按章节和语义分块。"""

    def __init__(self, size: int = 1200):
        self.size = size

    def split(self, document_id: str, text: str) -> list[DocumentChunk]:
        """按字符切分并保留顺序，保证后续可以稳定引用。"""
        cleaned = "\n".join(line.strip() for line in text.splitlines()).strip()
        return [
            DocumentChunk(document_id, index, cleaned[start : start + self.size])
            for index, start in enumerate(range(0, len(cleaned), self.size))
            if cleaned[start : start + self.size]
        ]
