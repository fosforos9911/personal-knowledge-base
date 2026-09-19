from pathlib import Path
import shutil


class LocalFileStore:
    """把用户文件存放到 storage/documents/{document_id}/ 下。"""

    def __init__(self, root: Path):
        self.root = root

    def save(self, source: Path, document_id: str) -> Path:
        """保存文件并返回实际路径；不覆盖其他文档目录。"""
        target_dir = self.root / "documents" / document_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        shutil.copy2(source, target)
        return target
