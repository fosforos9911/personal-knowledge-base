from uuid import uuid4

from app.db import connect
from app.domain.models import utc_now


class SQLiteChatRepository:
    """保存对话、消息和引用关系。"""

    def __init__(self, database_path):
        self.database_path = database_path

    def create_conversation(self, title: str) -> str:
        conversation_id = str(uuid4())
        now = utc_now()
        with connect(self.database_path) as db:
            db.execute("INSERT INTO conversations VALUES (?,?,?,?)", (conversation_id, title, now, now))
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> str:
        message_id = str(uuid4())
        with connect(self.database_path) as db:
            db.execute("INSERT INTO messages VALUES (?,?,?,?,?)", (message_id, conversation_id, role, content, utc_now()))
            db.execute("UPDATE conversations SET updated_at=? WHERE id=?", (utc_now(), conversation_id))
        return message_id

    def add_citations(self, message_id: str, evidence: list[dict]) -> None:
        with connect(self.database_path) as db:
            db.executemany(
                "INSERT INTO citations VALUES (?,?,?,?,?,?)",
                [(str(uuid4()), message_id, item["document_id"], item["chunk_id"], item["sequence"], utc_now()) for item in evidence],
            )
