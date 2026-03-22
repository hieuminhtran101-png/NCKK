# app/service/auth_service.py
from app.core.database import user_collection
from app.core.security import create_access_token
from passlib.context import CryptContext
from datetime import datetime, timezone

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def register_user(data):
    existing = user_collection.find_one({"student_id": data.student_id})
    if existing:
        return None

    user = {
        "student_id":        data.student_id,
        "password":          pwd.hash(data.password),
        "full_name":         data.full_name,
        "email":             data.email,
        "telegram_chat_id":  None,
        "is_telegram_linked": False,
        "created_at":        datetime.now(timezone.utc),
    }

    result = user_collection.insert_one(user)
    user["id"] = str(result.inserted_id)
    return user


def login_user(data):
    user = user_collection.find_one({"student_id": data.student_id})
    if not user:
        return None
    if not pwd.verify(data.password, user["password"]):
        return None

    token = create_access_token(user["student_id"])

    return {
        "id":           str(user["_id"]),
        "student_id":   user["student_id"],
        "full_name":    user["full_name"],
        "access_token": token,
        "token_type":   "bearer",
    }