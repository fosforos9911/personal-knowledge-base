from pathlib import Path


class ParserRegistry:
    """按扩展名选择解析器，后续可注册 docx、图片 OCR 等解析器。"""

    def parse(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".markdown"}:
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            return self._parse_pdf(path)
        raise ValueError(f"暂不支持的文件类型：{suffix or '无扩展名'}")

    @staticmethod
    def _parse_pdf(path: Path) -> str:
        """使用 pypdf 提取文本；扫描 PDF 在后续 OCR 阶段处理。"""
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
