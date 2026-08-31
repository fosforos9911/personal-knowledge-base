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
            self._rebuild_fts_for_document(db, document_id)

    def _rebuild_fts_for_document(self, db, document_id: str) -> None:
        """同步一个文档的检索副本，重处理文档时不会残留旧结果。"""
        db.execute("DELETE FROM chunk_fts WHERE document_id=?", (document_id,))
        document = db.execute(
            "SELECT title, industry, author, keywords_json FROM documents WHERE id=?",
            (document_id,),
        ).fetchone()
        if not document:
            return
        chunks = db.execute(
            "SELECT id, sequence, content, location FROM document_chunks WHERE document_id=? ORDER BY sequence",
            (document_id,),
        ).fetchall()
        keywords = " ".join(json.loads(document["keywords_json"] or "[]"))
        db.executemany(
            "INSERT INTO chunk_fts(chunk_id,document_id,title,content,industry,author,keywords) VALUES (?,?,?,?,?,?,?)",
            [(chunk["id"], document_id, document["title"], chunk["content"],
              document["industry"] or "", document["author"] or "", keywords) for chunk in chunks],
        )

    def search_chunks(self, query: str) -> list[dict]:
        """返回命中分块和文档元数据，供 SearchService 统一组装结果。"""
        # FTS5 适合精确术语；LIKE 是中文连续文本的保底路径。
        with connect(self.database_path) as db:
            try:
                rows = db.execute(
                    """SELECT f.chunk_id, f.document_id, f.title, f.content,
                    d.document_type, d.industry, d.author, d.project_stage,
                    d.trust_level, c.sequence, c.location
                    FROM chunk_fts f JOIN document_chunks c ON c.id=f.chunk_id
                    JOIN documents d ON d.id=f.document_id
                    WHERE chunk_fts MATCH ? ORDER BY rank LIMIT 50""",
                    (query,),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []
            if not rows:
                like = f"%{query}%"
                rows = db.execute(
                    """SELECT c.id AS chunk_id, c.document_id, d.title, c.content,
                    d.document_type, d.industry, d.author, d.project_stage,
                    d.trust_level, c.sequence, c.location
                    FROM document_chunks c JOIN documents d ON d.id=c.document_id
                    WHERE c.content LIKE ? OR d.title LIKE ? OR d.industry LIKE ?
                    ORDER BY d.updated_at DESC, c.sequence LIMIT 50""",
                    (like, like, like),
                ).fetchall()
            return [dict(row) for row in rows]
