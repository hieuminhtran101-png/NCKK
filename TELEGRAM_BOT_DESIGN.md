# 🤖 Telegram Bot Integration Design

## Hiện Tại Có

```python
# app/api/endpoints/telegram.py
POST /telegram/connect
  ├─ Headers: X-User-Id: 1
  └─ Body: {"chat_id": "123456"}
  └─ Action: Gán telegram chat_id với user_id

POST /telegram/webhook
  ├─ Body: Telegram update JSON (message, callback_query, etc)
  └─ Actions:
     ├─ Extract chat_id từ update
     ├─ Find user_id by chat_id
     ├─ Process command (/today, /connect, etc)
     └─ Send response via send_message()
```

```python
# app/core/telegram.py
register_chat(user_id, chat_id)      # Lưu link
find_user_by_telegram_chat(chat_id)  # Tìm user từ chat
send_message(chat_id, text)          # Gửi tin nhắn (hiện đang dùng outbox)
handle_update(update_json)           # Xử lý update từ Telegram
```

---

## Luồng Mong Muốn (Các Bước)

### Bước 1: Web Login & Get Telegram Connect Token

```
User truy cập Web App
    ↓
Đăng nhập (email, password)
    ↓
API: POST /auth/login → response: {access_token, user_id}
    ↓
Frontend lưu token + user_id
    ↓
User click button "Kết nối Telegram"
    ↓
Frontend gọi: POST /auth/generate-telegram-token
    ├─ Headers: Authorization: Bearer {access_token}
    └─ Response: {telegram_token: "jwt_token"}
    ↓
Frontend hiển thị:
    ├─ QR Code pointing to: https://t.me/YourBotName?start={telegram_token}
    └─ OR: Button "Mở Telegram Bot" (deep link)
```

### Bước 2: Telegram Bot /start Command

```
User click link → Telegram mở bot
    ↓
User nhấn START
    ↓
Telegram sends: /start {telegram_token}
    ↓
Bot nhận update, gửi: POST /telegram/webhook
    {
      "message": {
        "chat": {"id": 123456789},
        "text": "/start {telegram_token}"
      }
    }
    ↓
Backend (handle_update):
    1. Extract token từ text
    2. Verify JWT token → extract user_id
    3. Extract chat_id = 123456789
    4. Call register_chat(user_id, chat_id)
    5. Send message: "Kết nối thành công! 🎉"
       "Gõ /today để xem lịch hôm nay"
```

### Bước 3: Telegram Commands

```
User gõ trong Telegram:
/today          → Hiển thị lịch hôm nay
/tomorrow       → Hiển thị lịch ngày mai
/schedule       → Hiển thị toàn bộ lịch tuần
/help           → Hiển thị danh sách lệnh

Natural chat:
"Hôm nay có gì vui không?"
    ↓
Backend forward to LLM: POST /chat
    {
      "text": "Hôm nay có gì vui không?",
      "user_id": 1
    }
    ↓
LLM return: chat intent + natural response
    ↓
Bot send response to user
```

---

## Cần Implement (Phase 2)

### 1. API Endpoints (Backend)

#### A. Generate Telegram Token

```
POST /auth/generate-telegram-token
Headers:
  - Authorization: Bearer {access_token}

Response:
{
  "ok": true,
  "telegram_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."  // JWT for Telegram /start
}
```

**Logic:**

```python
def generate_telegram_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now() + timedelta(minutes=10),  # 10 min validity
        "purpose": "telegram_connect"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token
```

#### B. Verify Telegram Token (in handle_update)

```python
def verify_telegram_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "telegram_connect":
            return None
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None  # Token hết hạn
    except jwt.InvalidTokenError:
        return None
```

### 2. Telegram Bot Setup

#### Get Bot Token from BotFather

```
1. Open Telegram, search: @BotFather
2. Send: /newbot
3. Choose name: "FastAPI Books Bot"
4. Choose username: @fastapi_books_bot
5. Get token: 123456789:ABCDEFGHIJKLMNOP
6. Save to .env: TELEGRAM_BOT_TOKEN=123456...
```

#### Set Webhook URL

```python
# After getting bot token:
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://your-domain.com/telegram/webhook"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)
print(response.json())  # {"ok": true, "result": true, ...}
```

#### Commands Menu (Optional)

```python
# Define commands shown to user
requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands",
    json={
        "commands": [
            {"command": "today", "description": "Xem lịch hôm nay"},
            {"command": "tomorrow", "description": "Xem lịch ngày mai"},
            {"command": "help", "description": "Danh sách lệnh"},
        ]
    }
)
```

### 3. Update handle_update() in telegram.py

```python
def handle_update(update: Dict[str, Any]):
    msg = update.get("message") or {}
    chat = msg.get("chat", {})
    chat_id = str(chat.get("id"))
    text = msg.get("text", "")

    # Check /start with token
    if text.startswith("/start "):
        token = text.split(" ", 1)[1]
        user_id = verify_telegram_token(token)
        if user_id:
            register_chat(user_id, chat_id)
            send_message(chat_id, "✅ Kết nối thành công!\nGõ /help để xem lệnh")
            return {"ok": True, "action": "connected"}
        else:
            send_message(chat_id, "❌ Token không hợp lệ hoặc hết hạn")
            return {"ok": False}

    # Find user by chat_id
    user = auth_core.find_user_by_telegram_chat(chat_id)
    if not user:
        send_message(chat_id, "⚠️  Bạn chưa kết nối. Nhấn nút 'Kết nối Telegram' trong app")
        return {"ok": False}

    user_id = int(user['id'])

    # Commands
    if text == "/today":
        # ... existing logic
    elif text == "/tomorrow":
        # ... similar to /today but next day
    elif text == "/help":
        help_text = """
        /today - Lịch hôm nay
        /tomorrow - Lịch ngày mai
        /schedule - Lịch tuần
        """
        send_message(chat_id, help_text)
    else:
        # Natural chat → forward to LLM
        # ... call agent.handle_parse() with chat intent
        pass

    return {"ok": True}
```

### 4. Send Real Telegram Messages

Update send_message() to use real Telegram API:

```python
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_message(chat_id: str, text: str):
    """Send message via Telegram Bot API (Real)"""
    if not BOT_TOKEN:
        # Fallback to outbox for testing
        TELEGRAM_OUTBOX.append((chat_id, text))
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"  # Support HTML formatting
    }

    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            logger.error(f"Telegram API error: {response.text}")
            # Fallback if API fails
            TELEGRAM_OUTBOX.append((chat_id, text))
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        TELEGRAM_OUTBOX.append((chat_id, text))
```

### 5. Auto-Send Reminders via Telegram

In app/core/scheduler.py, update reminder logic:

```python
# When sending reminders:
def send_reminder(event, user):
    chat_id = user.get("telegram_chat_id")
    if chat_id:
        message = f"⏰ Nhắc nhở: {event['title']} lúc {event['start'].strftime('%H:%M')}"
        send_message(chat_id, message)  # Real Telegram
    else:
        # User hasn't connected Telegram yet
        pass
```

---

## .env Updates

```env
# Existing
HF_API_KEY=hf_...

# New for Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOP
WEBHOOK_URL=https://your-domain.com/telegram/webhook

# JWT for Telegram tokens (use same as main JWT secret or separate)
TELEGRAM_JWT_SECRET=your_secret_key
```

---

## File Changes Summary

| File                            | Change                                                 | Priority |
| ------------------------------- | ------------------------------------------------------ | -------- |
| `app/api/endpoints/auth.py`     | Add `/generate-telegram-token`                         | High     |
| `app/core/telegram.py`          | Add `verify_telegram_token()`, update `send_message()` | High     |
| `app/api/endpoints/telegram.py` | Update `handle_update()` for /start + JWT              | High     |
| `app/core/auth.py`              | Already has `find_user_by_telegram_chat()` ✅          | -        |
| `.env`                          | Add `TELEGRAM_BOT_TOKEN`, `WEBHOOK_URL`                | Required |
| `app/main.py`                   | Already loads .env ✅                                  | -        |

---

## Testing Telegram Flow

### Local Testing (Without Real Telegram)

```python
# tests/test_telegram_flow.py
import pytest
from app.core import telegram as tg
from app.core import auth as auth_core

def test_telegram_connect_flow():
    # 1. Create user
    auth_core.register("user@test.com", "password123")
    user = auth_core.login("user@test.com", "password123")
    user_id = user['id']

    # 2. Simulate /start with token
    update = {
        "message": {
            "chat": {"id": "987654321"},
            "text": "/start {telegram_token}"  # Token would be generated
        }
    }

    # 3. Handle update
    result = tg.handle_update(update)
    assert result["ok"] == True

    # 4. Verify link created
    found_user = auth_core.find_user_by_telegram_chat("987654321")
    assert found_user['id'] == user_id
```

### Real Testing (With Mock Telegram)

```bash
# Set up ngrok to expose local webhook
ngrok http 8000

# Configure webhook on Telegram
TELEGRAM_BOT_TOKEN=...
WEBHOOK_URL=https://xxx-ngrok.io/telegram/webhook

# Set in .env and restart server

# Send test message from Telegram
/start {token}
/today
Natural chat test
```

---

## Deployment Checklist

- [ ] Get real Telegram Bot token (BotFather)
- [ ] Set TELEGRAM_BOT_TOKEN in .env
- [ ] Deploy to public URL (ngrok for dev, real server for prod)
- [ ] Register webhook: `POST /bot/setWebhook`
- [ ] Test /start command
- [ ] Test /today command
- [ ] Test natural chat
- [ ] Set command menu (optional)
- [ ] Monitor logs for Telegram errors

---

## Architecture Benefits

✅ **Stateless**: Each request includes chat_id or user_id
✅ **Scalable**: Can distribute webhook across multiple servers
✅ **Graceful degradation**: Falls back to outbox if API unavailable
✅ **Secure**: JWT token for /start, expires in 10 minutes
✅ **Flexible**: Supports both commands and natural chat

---

**Status: Design ready, implementation pending real Telegram bot token**
