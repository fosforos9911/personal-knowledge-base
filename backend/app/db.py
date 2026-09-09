import sqlite3
from pathlib import Path


# Level 0 只保存启动和后续文档功能所需的最小元数据。
# 原始 PDF 等大文件放在 storage_dir，数据库保存索引和描述信息。
SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'note',
    industry TEXT,
    author TEXT,
    published_at TEXT,
    expires_at TEXT,
    language TEXT,
    trust_level TEXT NOT NULL DEFAULT 'medium',
    region TEXT,
    project_stage TEXT NOT NULL DEFAULT 'learning',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    related_products_json TEXT NOT NULL DEFAULT '[]',
    version TEXT,
    reviewed_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(database_path: Path) -> sqlite3.Connection:
    """创建一次数据库连接。

    每个业务操作独立获取连接，配合 with 自动提交或回滚，避免长期持有
    连接造成文件锁问题。row_factory 让查询结果可以按字段名读取。
    """
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    """幂等地初始化数据库。

    幂等意味着启动一次或启动多次结果相同，便于开发、测试和未来迁移。
    schema_version 为后续数据库迁移预留位置。
    """
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT OR IGNORE INTO app_meta(key, value) VALUES (?, ?)",
            ("schema_version", "1"),
        )


def database_is_initialized(database_path: Path) -> bool:
    """只检查数据库是否完成基础初始化，不读取任何文档内容。"""
    if not database_path.exists():
        return False
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
    return row is not None
