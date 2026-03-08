from pydantic import BaseModel,EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    full_name : str
    student_id : str
    password : str
    email : Optional[EmailStr] = None
    
class LoginRequest(BaseModel):
    student_id: str
    password: str
    