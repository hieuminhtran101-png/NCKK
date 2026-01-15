from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

class UserDB(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    salt: str
    full_name: Optional[str] = None
    created_at: datetime
    telegram_chat_id: Optional[str] = None
    timezone: Optional[str] = None
