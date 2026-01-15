import hashlib
import hmac
import base64
import secrets
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Simple config (override later with secure env vars)
SECRET_KEY = "dev-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# In-memory user store (shared helper functions)
_USERS: Dict[int, Dict] = {}
_next_id = 1


def create_user(email: str, password: str, full_name: str = None) -> Dict[str, Any]:
    global _next_id
    for u in _USERS.values():
        if u["email"] == email:
            raise ValueError("Email already registered")
    hp = hash_password(password)
    user = {
        "id": str(_next_id),
        "email": email,
        "hashed_password": hp["hashed_password"],
        "salt": hp["salt"],
        "full_name": full_name,
        "created_at": datetime.utcnow(),
        "telegram_chat_id": None,
        "timezone": None,
    }
    _USERS[_next_id] = user
    _next_id += 1
    return user


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    for u in _USERS.values():
        if u["email"] == email:
            return u
    return None


def get_user_by_id(uid: int) -> Optional[Dict[str, Any]]:
    return _USERS.get(uid)


def set_user_telegram_chat(user_id: int, chat_id: str):
    u = _USERS.get(user_id)
    if not u:
        raise ValueError("User not found")
    u["telegram_chat_id"] = chat_id


def find_user_by_telegram_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    for u in _USERS.values():
        if u.get("telegram_chat_id") == chat_id:
            return u
    return None


def hash_password(password: str, salt: str = None) -> Dict[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    hashed = base64.b64encode(dk).decode()
    return {"salt": salt, "hashed_password": hashed}


def verify_password(password: str, salt: str, hashed_password: str) -> bool:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return base64.b64encode(dk).decode() == hashed_password


# Minimal JWT implementation (HMAC SHA256)
import hmac
import hashlib


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(data: Dict[str, Any], expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + int(expires_minutes * 60)
    header_b = _b64url_encode(json.dumps(header, separators=(',', ':')).encode())
    payload_b = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode())
    signing_input = f"{header_b}.{payload_b}".encode()
    sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    signature = _b64url_encode(sig)
    return f"{header_b}.{payload_b}.{signature}"


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        header_b, payload_b, signature = token.split('.')
        signing_input = f"{header_b}.{payload_b}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected_sig), signature):
            raise ValueError("Invalid signature")
        payload = json.loads(_b64url_decode(payload_b))
        if "exp" in payload and int(time.time()) > int(payload["exp"]):
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise ValueError("Invalid token") from e
