# app/schemas/chat.py
from pydantic import BaseModel
from typing import Any, Optional


class HistoryPart(BaseModel):
    text: str


class HistoryTurn(BaseModel):
    role: str          # "user" | "model"
    parts: list[HistoryPart]


class ChatRequest(BaseModel):
    message: str
    # FE truyền lịch sử hội thoại để AI đọc context đa lượt.
    # Mỗi turn: {"role": "user"|"model", "parts": [{"text": "..."}]}
    # Không bắt buộc — nếu FE chưa truyền thì vẫn hoạt động bình thường.
    history: Optional[list[HistoryTurn]] = None


class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None
    data: Optional[Any]   = None