from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: str | None = None


@router.post("")
def chat(request: ChatRequest) -> dict[str, object]:
    """调用问答服务；未配置模型时返回明确错误，不隐式外发资料。"""
    try:
        answer = settings.chat_service.answer(request.question, request.conversation_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "conversation_id": answer.conversation_id,
        "message_id": answer.message_id,
        "content": answer.content,
        "citations": answer.citations,
    }
