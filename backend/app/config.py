from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class Settings:
    """应用运行所需的最小配置。

    设计决策：配置集中在一个不可变对象中，业务函数不直接读取环境变量。
    这样测试时可以传入临时目录，未来改成 PostgreSQL 或对象存储时也只需
    增加配置，不会把路径判断散落到各个 API 中。
    """
    app_name: str = "Personal Knowledge Base"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = Path("data")
    storage_dir: Path = Path("storage")
    database_path: Path = Path("data/knowledge_base.sqlite3")
    # 启动时注入的应用服务；它不是持久化配置，只是依赖组装结果。
    document_service: object | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量构造配置；未设置时使用个人单机默认值。"""
        data_dir = Path(os.getenv("PKB_DATA_DIR", "data"))
        storage_dir = Path(os.getenv("PKB_STORAGE_DIR", "storage"))
        database_path = Path(
            os.getenv("PKB_DATABASE_PATH", str(data_dir / "knowledge_base.sqlite3"))
        )
        return cls(
            environment=os.getenv("PKB_ENVIRONMENT", "development"),
            host=os.getenv("PKB_HOST", "127.0.0.1"),
            port=int(os.getenv("PKB_PORT", "8000")),
            data_dir=data_dir,
            storage_dir=storage_dir,
            database_path=database_path,
        )

    def ensure_directories(self) -> None:
        """启动前创建应用需要的目录，不创建用户资料之外的目录。"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)


# 模块级配置供应用入口使用；测试可以直接构造 Settings 覆盖默认值。
settings = Settings.from_env()
