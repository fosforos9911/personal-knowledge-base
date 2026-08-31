from pathlib import Path
import tempfile

from fastapi import APIRouter, File, Form, UploadFile

from app.config import settings
from app.domain.models import Document


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("note"),
    industry: str | None = Form(None),
    author: str | None = Form(None),
    language: str | None = Form(None),
    trust_level: str = Form("medium"),
    project_stage: str = Form("learning"),
) -> dict[str, object]:
    """接收上传请求，把具体导入工作交给 DocumentService。"""
    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
        temporary.write(await file.read())
        temporary_path = Path(temporary.name)
    document = Document(title=title, document_type=document_type, industry=industry,
                        author=author, language=language, trust_level=trust_level,
                        project_stage=project_stage)
    try:
        result = settings.document_service.import_document(temporary_path, document)
        return {"id": result.id, "title": result.title, "status": result.status}
    finally:
        temporary_path.unlink(missing_ok=True)
