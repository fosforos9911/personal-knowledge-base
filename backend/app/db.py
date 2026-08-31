import sqlite3
from pathlib import Path


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
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT OR IGNORE INTO app_meta(key, value) VALUES (?, ?)",
            ("schema_version", "1"),
        )


def database_is_initialized(database_path: Path) -> bool:
    if not database_path.exists():
        return False
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
    return row is not None
