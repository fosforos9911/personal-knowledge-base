from fastapi import APIRouter

from app.config import settings
from app.db import database_is_initialized


router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    """Return a small local diagnostic without exposing document content."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "database_initialized": database_is_initialized(settings.database_path),
    }


@router.get("/modules")
def modules() -> list[dict[str, object]]:
    """Return the navigation contract used by the extensible frontend shell."""
    return [
        {"key": "dashboard", "label": "工作台", "route": "/", "enabled": True},
        {"key": "documents", "label": "文档库", "route": "/documents", "enabled": True},
        {"key": "search", "label": "全局检索", "route": "/search", "enabled": True},
        {"key": "chat", "label": "AI 问答", "route": "/chat", "enabled": True},
        {"key": "notes", "label": "个人笔记", "route": "/notes", "enabled": True},
        {"key": "graph", "label": "知识图谱", "route": "/graph", "enabled": False},
        {"key": "projects", "label": "项目空间", "route": "/projects", "enabled": False},
        {"key": "settings", "label": "设置", "route": "/settings", "enabled": True},
    ]
