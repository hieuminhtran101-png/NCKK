from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    remind_before_minutes: Optional[int] = 30
    notify_via: Optional[List[str]] = ["telegram"]

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    remind_before_minutes: Optional[int] = None
    notify_via: Optional[List[str]] = None

class EventOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    start: datetime
    end: datetime
    remind_before_minutes: int
    notify_via: List[str]
