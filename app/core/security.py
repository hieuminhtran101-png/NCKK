# app/core/security.py
import os
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
 
SECRET_KEY  = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM   = "HS256"
EXPIRE_DAYS = 30   # sinh viên không cần đăng nhập lại thường xuyên
 
 
def create_access_token(student_id: str) -> str:
    payload = {
        "sub": student_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
 
 
def decode_access_token(token: str) -> str | None:
    """Trả về student_id nếu token hợp lệ, None nếu không."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None