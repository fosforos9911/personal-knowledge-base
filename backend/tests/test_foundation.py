from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db import database_is_initialized, initialize_database
from app.main import app


def test_database_initialization(tmp_path: Path) -> None:
    database_path = tmp_path / "knowledge.sqlite3"
    assert not database_is_initialized(database_path)
    initialize_database(database_path)
    assert database_is_initialized(database_path)


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_module_contract() -> None:
    with TestClient(app) as client:
        modules = client.get("/api/modules").json()
    keys = {module["key"] for module in modules}
    assert {"dashboard", "documents", "search", "chat", "settings"} <= keys
    assert next(module for module in modules if module["key"] == "graph")["enabled"] is False
