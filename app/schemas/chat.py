# app/schemas/chat.py
from pydantic import BaseModel
from typing import Optional, Any

class ChatRequest(BaseModel):
    message: str
    student_id: str

class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None   # action Gemini đã chọn
    data: Optional[Any] = None     # kết quả từ service (nếu có)