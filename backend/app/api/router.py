from fastapi import APIRouter

from app.config import settings
from app.db import database_is_initialized


# 路由只负责 HTTP 输入输出；真正的文档、检索和问答逻辑应放到 services。
# 这样页面/API 改变时，不会把业务规则绑定在 FastAPI 装饰器上。
router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    """返回本地诊断信息，不暴露文档正文和路径。"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "database_initialized": database_is_initialized(settings.database_path),
    }


@router.get("/modules")
def modules() -> list[dict[str, object]]:
    """返回前端导航契约。

    enabled=False 的模块表示“路由已规划但功能尚未实现”，避免用户误以为
    知识图谱已经可以工作；以后可以改成从模块注册表或配置中读取。
    """
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
