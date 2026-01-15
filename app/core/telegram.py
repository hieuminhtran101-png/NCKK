from typing import Optional, Dict, Any
from app.core import auth as auth_core
from app.core import events as events_core

# Outbox for testing (collect sent messages)
TELEGRAM_OUTBOX = []  # list of tuples (chat_id, text)


def register_chat(user_id: int, chat_id: str):
    auth_core.set_user_telegram_chat(user_id, chat_id)


def send_message(chat_id: str, text: str):
    # In real implementation, call Telegram Bot API here.
    TELEGRAM_OUTBOX.append((chat_id, text))


def handle_update(update: Dict[str, Any]):
    # Simplified handler expecting Telegram update shape
    msg = update.get("message") or {}
    chat = msg.get("chat", {})
    chat_id = str(chat.get("id"))
    text = msg.get("text", "")
    # find user by chat
    user = auth_core.find_user_by_telegram_chat(chat_id)
    if not user:
        send_message(chat_id, "Bạn chưa kết nối tài khoản. Vui lòng /connect trong app.")
        return {"ok": False, "message": "no_user"}
    user_id = int(user['id'])
    if text.strip().lower().startswith('/today'):
        events = events_core.list_events(user_id)
        if not events:
            send_message(chat_id, "Hôm nay bạn không có sự kiện nào.")
        else:
            lines = []
            for e in events:
                lines.append(f"{e['title']} - {e['start'].strftime('%H:%M')} to {e['end'].strftime('%H:%M')}")
            send_message(chat_id, "\n".join(lines))
        return {"ok": True}
    # default echo
    send_message(chat_id, "Lệnh không nhận diện. Gõ /today để xem lịch hôm nay.")
    return {"ok": True}