from pathlib import Path

from app.adapters.file_store import LocalFileStore
from app.adapters.parsers import ParserRegistry
from app.adapters.sqlite_repository import SQLiteDocumentRepository
from app.db import connect, initialize_database
from app.domain.models import Document
from app.services.document_service import DocumentService, FixedSizeChunker


def test_import_text_document(tmp_path: Path) -> None:
    database = tmp_path / "db.sqlite3"
    source = tmp_path / "whitepaper.md"
    source.write_text("工业现场数据采集\n这是第一份学习资料。", encoding="utf-8")
    initialize_database(database)
    service = DocumentService(
        SQLiteDocumentRepository(database), LocalFileStore(tmp_path / "storage"),
        ParserRegistry(), FixedSizeChunker(size=10),
    )

    result = service.import_document(source, Document(title="测试白皮书", industry="制造"))

    assert result.status == "ready"
    with connect(database) as db:
        document = db.execute("SELECT status FROM documents WHERE id=?", (result.id,)).fetchone()
        chunks = db.execute("SELECT COUNT(*) AS count FROM document_chunks WHERE document_id=?", (result.id,)).fetchone()
    assert document["status"] == "ready"
    assert chunks["count"] >= 2
    assert (tmp_path / "storage" / "documents" / result.id / "whitepaper.md").exists()
