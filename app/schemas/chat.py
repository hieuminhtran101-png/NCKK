# app/schemas/chat.py
from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    message: str
    # student_id không còn trong body — lấy từ JWT token


class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None
    data: Optional[Any] = None