"""
Schemas (Pydantic models) cho lịch học và sự kiện công khai.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============ Lịch học cá nhân ============

class ScheduleEntryCreate(BaseModel):
    """Tạo bài học trong lịch cá nhân."""
    subject: str
    day_of_week: str  # monday, tuesday, etc.
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    room: Optional[str] = None
    teacher: Optional[str] = None
    notes: Optional[str] = None

class ScheduleEntryUpdate(BaseModel):
    """Cập nhật bài học."""
    subject: Optional[str] = None
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room: Optional[str] = None
    teacher: Optional[str] = None
    notes: Optional[str] = None

class ScheduleEntryOut(BaseModel):
    """Trả về thông tin bài học."""
    id: str
    subject: str
    day_of_week: str
    start_time: str
    end_time: str
    room: Optional[str]
    teacher: Optional[str]
    notes: Optional[str]
    created_at: datetime


# ============ Sự kiện công khai ============

class PublicEventCreate(BaseModel):
    """Admin tạo sự kiện công khai."""
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    event_type: str = "general"  # announcement, exam, registration, etc.
    target_groups: Optional[List[str]] = None

class PublicEventUpdate(BaseModel):
    """Cập nhật sự kiện công khai."""
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
    target_groups: Optional[List[str]] = None

class PublicEventOut(BaseModel):
    """Trả về sự kiện công khai."""
    id: str
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime]
    event_type: str
    target_groups: List[str]
    created_at: datetime
