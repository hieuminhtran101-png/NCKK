# app/schemas/events.py
from pydantic import BaseModel
from datetime import date
from typing import Optional
from enum import Enum


class EventType(str, Enum):
    buoi_hoc  = "buoi_hoc"   # 📚 Lịch học thường
    thi       = "thi"        # 📝 Thi giữa kỳ / cuối kỳ
    deadline  = "deadline"   # ⏰ Nộp báo cáo / bài tập
    hop_nhom  = "hop_nhom"   # 👥 Họp nhóm / meeting
    su_kien   = "su_kien"    # 🎉 Sự kiện trường


class EventCreate(BaseModel):
    title:        str
    room:         str
    teacher:      str
    day_of_week:  str
    session:      str
    period_start: int
    period_end:   int
    start_date:   date
    end_date:     date
    event_type:   EventType = EventType.buoi_hoc  # ✅ mặc định là buổi học


class EventBulkCreate(BaseModel):
    events: list[EventCreate]


class EventUpdate(BaseModel):
    title:        Optional[str]       = None
    room:         Optional[str]       = None
    teacher:      Optional[str]       = None
    day_of_week:  Optional[str]       = None
    session:      Optional[str]       = None
    period_start: Optional[int]       = None
    period_end:   Optional[int]       = None
    start_date:   Optional[date]      = None
    end_date:     Optional[date]      = None
    event_type:   Optional[EventType] = None  # ✅ có thể update type