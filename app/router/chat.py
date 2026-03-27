# app/router/chat.py
from fastapi import APIRouter, HTTPException, Depends
from app.core.deps import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.service.ai_service import handle_chat

router = APIRouter(prefix="/api/chat", tags=["Chat AI"])


@router.post("/", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    student_id: str = Depends(get_current_user),
):
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống")

    result = handle_chat(message=data.message, student_id=student_id, history=data.history)

    return ChatResponse(
        reply=result["reply"],
        action=result.get("action"),
        data=result.get("data"),
    )