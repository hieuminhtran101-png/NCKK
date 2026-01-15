"""
Authentication với MongoDB + JWT + Roles
"""

import hashlib
import hmac
import base64
import secrets
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel

# Config
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


# Enum cho Roles
class UserRole(str, Enum):
    """User roles - phân quyền"""
    ADMIN = "admin"           # Quản trị viên
    INSTRUCTOR = "instructor" # Giáo viên
    USER = "user"            # Sinh viên bình thường


class User(BaseModel):
    """User model cho MongoDB"""
    id: Optional[str] = None  # MongoDB ObjectId as string
    email: str
    username: Optional[str] = None
    hashed_password: str
    salt: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    telegram_chat_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None


class LoginResponse(BaseModel):
    """Response từ login"""
    ok: bool
    access_token: str
    user_id: str
    role: str
    expires_in: int


def hash_password(password: str, salt: str = None) -> Dict[str, str]:
    """Hash password with PBKDF2"""
    if not salt:
        salt = secrets.token_hex(16)
    
    # PBKDF2-SHA256: 100,000 iterations
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return {
        "hashed_password": base64.b64encode(hashed).decode('utf-8'),
        "salt": salt
    }


def verify_password(password: str, salt: str, hashed_password: str) -> bool:
    """Verify password"""
    result = hash_password(password, salt)
    return hmac.compare_digest(result["hashed_password"], hashed_password)


def generate_salt() -> str:
    """Generate random salt"""
    return secrets.token_hex(16)


def create_access_token(user_id: str, role: str, expires_delta: timedelta = None) -> str:
    """Tạo JWT token"""
    import json
    import time
    
    if not expires_delta:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = time.time() + expires_delta.total_seconds()
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire
    }
    
    # HMAC-SHA256
    message = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{base64.b64encode(message.encode()).decode()}.{signature}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token"""
    import json
    import time
    
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        message_b64, signature = parts
        message = base64.b64decode(message_b64).decode()
        
        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        payload = json.loads(message)
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
    except Exception:
        return None


# Cho MongoDB operations
async def register_user(db, email: str, password: str, full_name: str = None, role: str = "user") -> Dict[str, Any]:
    """Đăng ký user mới"""
    users_col = db["users"]
    
    # Check email đã tồn tại
    existing = await users_col.find_one({"email": email})
    if existing:
        raise ValueError("Email already registered")
    
    hp = hash_password(password)
    user = {
        "email": email,
        "username": email.split("@")[0],  # username từ email
        "hashed_password": hp["hashed_password"],
        "salt": hp["salt"],
        "full_name": full_name or email.split("@")[0],
        "role": role,  # default: user
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await users_col.insert_one(user)
    user["_id"] = str(result.inserted_id)
    return user


async def login_user(db, email: str, password: str) -> Optional[Dict[str, Any]]:
    """Login user"""
    users_col = db["users"]
    user = await users_col.find_one({"email": email})
    
    if not user:
        return None
    
    if not user.get("is_active"):
        return None
    
    if not verify_password(password, user["salt"], user["hashed_password"]):
        return None
    
    return user


async def get_user_by_id(db, user_id: str) -> Optional[Dict[str, Any]]:
    """Lấy user từ ID"""
    from bson import ObjectId
    users_col = db["users"]
    
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
        return user
    except:
        return None


async def get_user_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    """Lấy user từ email"""
    users_col = db["users"]
    return await users_col.find_one({"email": email})


async def find_user_by_telegram_chat(db, chat_id: str) -> Optional[Dict[str, Any]]:
    """Tìm user từ telegram chat_id"""
    users_col = db["users"]
    return await users_col.find_one({"telegram_chat_id": chat_id})


async def set_user_telegram_chat(db, user_id: str, chat_id: str):
    """Gán telegram chat_id cho user"""
    from bson import ObjectId
    users_col = db["users"]
    
    try:
        await users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"telegram_chat_id": chat_id, "updated_at": datetime.utcnow()}}
        )
    except Exception as e:
        raise ValueError(f"Failed to set telegram chat: {e}")


async def has_role(db, user_id: str, required_role: str) -> bool:
    """Kiểm tra user có role này không"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    user_role = user.get("role", "user")
    
    # Admin có toàn bộ quyền
    if user_role == "admin":
        return True
    
    # Check exact role
    return user_role == required_role

# FastAPI Depends for verify_token
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(credentials = Depends(security)) -> Dict[str, Any]:
    """Dependency để lấy current user từ JWT token"""
    token = credentials.credentials
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user