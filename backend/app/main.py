from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.config import settings
from app.db import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期编排：目录 -> 数据库 -> 接收请求。

    这就是当前 Level 0 的核心启动编排。后续可在这里注册解析器、索引器
    和模型提供方，但这些组件不应在路由函数中临时创建。
    """
    settings.ensure_directories()
    initialize_database(settings.database_path)
    yield


# FastAPI 负责传输层；业务服务将在后续等级中从 app/api 路由中调用。
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
