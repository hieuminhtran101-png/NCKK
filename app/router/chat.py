# app/router/chat.py
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.service.ai_service import handle_chat

router = APIRouter(prefix="/api/chat", tags=["Chat AI"])

@router.post("/", response_model=ChatResponse)
def chat(data: ChatRequest):
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống")

    result = handle_chat(
        message=data.message,
        student_id=data.student_id
    )

    return ChatResponse(
        reply=result["reply"],
        action=result.get("action"),
        data=result.get("data")
    )