from pydantic import BaseModel
from datetime import datetime,timezone,date
from typing import Optional


class EventCreate(BaseModel):
    title: str
    room: str
    teacher: str
    day_of_week: str
    session: str
    period_start: int
    period_end: int
    start_date: date
    end_date: date
    
class EventBulkCreate(BaseModel):
    events: list[EventCreate]
    
class EventUpdate(BaseModel):
    title: Optional[str] = None
    room: Optional[str] = None
    teacher: Optional[str] = None
    day_of_week: Optional[str] = None
    session: Optional[str] = None
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None