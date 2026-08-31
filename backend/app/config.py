from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Personal Knowledge Base"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = Path("data")
    storage_dir: Path = Path("storage")
    database_path: Path = Path("data/knowledge_base.sqlite3")

    @classmethod
    def from_env(cls) -> "Settings":
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
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)


settings = Settings.from_env()
