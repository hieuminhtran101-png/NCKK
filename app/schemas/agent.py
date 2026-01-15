from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel
from datetime import date as date_type, datetime

class DateRange(BaseModel):
    start: datetime
    end: datetime

class ParseResult(BaseModel):
    intent: Literal["get_schedule", "get_free_time", "check_availability", "create_event"]
    confidence: float
    raw_text: str
    date: Optional[date_type] = None
    time_range: Optional[Dict[str, str]] = None  # {'start': '13:00', 'end': '18:00'}
    timezone: Optional[str] = None
    channel_hint: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class EventOut(BaseModel):
    title: str
    start: datetime
    end: datetime

class FreeSlot(BaseModel):
    start: str
    end: str

class InterpretResponse(BaseModel):
    ok: bool
    action: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    messages: Optional[list] = []
    needs_clarification: Optional[bool] = False
