import json

from app.db import connect
from app.domain.models import Document, DocumentChunk, utc_now


class SQLiteDocumentRepository:
    """文档持久化适配器，把领域对象转换成 SQLite 行。"""

    def __init__(self, database_path):
        self.database_path = database_path

    def create(self, document: Document) -> None:
        """先写入 pending，确保导入失败也有记录可追踪。"""
        with connect(self.database_path) as db:
            db.execute(
                """INSERT INTO documents
                (id,title,document_type,industry,author,language,trust_level,
                 project_stage,keywords_json,related_products_json,version,status,
                 created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (document.id, document.title, document.document_type, document.industry,
                 document.author, document.language, document.trust_level,
                 document.project_stage, json.dumps(document.keywords, ensure_ascii=False),
                 json.dumps(document.related_products, ensure_ascii=False), document.version,
                 document.status, document.created_at, document.updated_at),
            )

    def mark_status(self, document_id: str, status: str, error: str | None = None) -> None:
        """更新导入状态；错误暂写入 app_meta，后续可独立成任务表。"""
        with connect(self.database_path) as db:
            db.execute("UPDATE documents SET status=?, updated_at=? WHERE id=?", (status, utc_now(), document_id))
            if error:
                db.execute("INSERT OR REPLACE INTO app_meta(key,value) VALUES (?,?)", (f"error:{document_id}", error))

    def replace_chunks(self, document_id: str, chunks: list[DocumentChunk]) -> None:
        """事务内替换分块，重复处理同一文档不会留下旧分块。"""
        with connect(self.database_path) as db:
            db.execute("DELETE FROM document_chunks WHERE document_id=?", (document_id,))
            db.executemany(
                "INSERT INTO document_chunks(id,document_id,sequence,content,location,created_at) VALUES (?,?,?,?,?,?)",
                [(c.id, c.document_id, c.sequence, c.content, c.location, c.created_at) for c in chunks],
            )
