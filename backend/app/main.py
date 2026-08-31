from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.api.documents import router as documents_router
from app.adapters.file_store import LocalFileStore
from app.adapters.parsers import ParserRegistry
from app.adapters.sqlite_repository import SQLiteDocumentRepository
from app.config import settings
from app.db import initialize_database
from app.services.document_service import DocumentService, FixedSizeChunker


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期编排：目录 -> 数据库 -> 接收请求。

    这就是当前 Level 0 的核心启动编排。后续可在这里注册解析器、索引器
    和模型提供方，但这些组件不应在路由函数中临时创建。
    """
    settings.ensure_directories()
    initialize_database(settings.database_path)
    # 组合根集中组装依赖；API 不需要知道 SQLite 和本地文件的实现细节。
    settings.document_service = DocumentService(
        SQLiteDocumentRepository(settings.database_path),
        LocalFileStore(settings.storage_dir),
        ParserRegistry(),
        FixedSizeChunker(),
    )
    yield


# FastAPI 负责传输层；业务服务将在后续等级中从 app/api 路由中调用。
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")
app.include_router(documents_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
