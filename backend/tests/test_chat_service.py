from pathlib import Path

from app.adapters.file_store import LocalFileStore
from app.adapters.llm_provider import FakeLLMProvider
from app.adapters.parsers import ParserRegistry
from app.adapters.sqlite_chat_repository import SQLiteChatRepository
from app.adapters.sqlite_repository import SQLiteDocumentRepository
from app.db import connect, initialize_database
from app.domain.models import Document
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService, FixedSizeChunker
from app.services.search_service import SearchService


def test_chat_retrieves_evidence_and_saves_citations(tmp_path: Path) -> None:
    database = tmp_path / "db.sqlite3"
    source = tmp_path / "guide.md"
    source.write_text("边缘网关负责工业现场数据采集。", encoding="utf-8")
    initialize_database(database)
    repository = SQLiteDocumentRepository(database)
    document_service = DocumentService(repository, LocalFileStore(tmp_path / "storage"), ParserRegistry(), FixedSizeChunker())
    document_service.import_document(source, Document(title="现场方案"))
    chat = ChatService(SearchService(repository), SQLiteChatRepository(database), FakeLLMProvider())

    answer = chat.answer("工业现场数据采集怎么做？")

    assert answer.content.startswith("基于检索资料")
    assert answer.citations
    with connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM citations").fetchone()[0] == 1
