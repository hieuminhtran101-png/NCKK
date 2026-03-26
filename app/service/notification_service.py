# app/service/notification_service.py
from telegram import Bot
from datetime import datetime, timedelta, timezone
from app.core.database import user_collection
from app.service.event_service import get_events_by_date, PERIOD_TIME_MAP
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

EMOJI_MAP = {
    "buoi_hoc": "📚",
    "thi":      "📝",
    "deadline": "⏰",
    "hop_nhom": "👥",
    "su_kien":  "🎉",
}

def _get_start_time(period_start: int) -> str:
    return PERIOD_TIME_MAP.get(period_start, "??:??")

def _get_end_time(period_end: int) -> str:
    return PERIOD_TIME_MAP.get(period_end, "??:??")

def _format_event_block(event: dict) -> str:
    etype      = event.get("event_type", "buoi_hoc")
    emoji      = EMOJI_MAP.get(etype, "📌")
    start_time = _get_start_time(event["period_start"])
    end_time   = _get_end_time(event["period_end"])
    return (
        f"{emoji} *{event['title']}*\n"
        f"   🏫 Phòng: `{event['room']}`\n"
        f"   👨‍🏫 GV: {event['teacher']}\n"
        f"   ⏰ {start_time} - {end_time}\n"
    )


# ─────────────────────────────────────────
# 1. Nhắc buổi tối (21:00) — lịch ngày mai
# ─────────────────────────────────────────
async def send_evening_reminders():
    """Chạy lúc 21:00 mỗi ngày — nhắc lịch học ngày mai."""
    tomorrow     = (datetime.now(timezone.utc) + timedelta(hours=7) + timedelta(days=1)).date()
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    tomorrow_fmt = tomorrow.strftime("%d/%m/%Y")

    users = list(user_collection.find({"is_telegram_linked": True}))

    for user in users:
        student_id = user["student_id"]
        chat_id    = user.get("telegram_chat_id")
        if not chat_id:
            continue

        events = get_events_by_date(creator_id=student_id, date=tomorrow_str)
        if not events:
            continue

        events.sort(key=lambda e: e.get("period_start", 0))

        lines = [f"🌙 *Lịch học ngày mai ({tomorrow_fmt})*\n"]
        for event in events:
            lines.append(_format_event_block(event))
        lines.append("💤 Ngủ sớm để học tốt nhé!")

        try:
            await bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown")
        except Exception as e:
            print(f"[Evening Reminder] Lỗi gửi {student_id}: {e}")


# ─────────────────────────────────────────
# 2. Nhắc 1 tiếng trước buổi học
# Chạy mỗi 30 phút — tự tìm môn bắt đầu trong 55–65 phút tới
# ─────────────────────────────────────────
async def send_1h_before_reminders():
    """Chạy mỗi 30 phút. Nhắc môn học bắt đầu trong ~60 phút."""
    now_vn    = datetime.now(timezone.utc) + timedelta(hours=7)
    today_str = now_vn.date().strftime("%Y-%m-%d")
    now_min   = now_vn.hour * 60 + now_vn.minute

    users = list(user_collection.find({"is_telegram_linked": True}))

    for user in users:
        student_id = user["student_id"]
        chat_id    = user.get("telegram_chat_id")
        if not chat_id:
            continue

        events = get_events_by_date(creator_id=student_id, date=today_str)
        if not events:
            continue

        for event in events:
            start_str = PERIOD_TIME_MAP.get(event.get("period_start"))
            if not start_str or start_str == "??:??":
                continue

            eh, em     = map(int, start_str.split(":"))
            event_min  = eh * 60 + em
            diff       = event_min - now_min  # số phút còn lại

            # Chỉ nhắc nếu còn 55–65 phút (buffer ±5)
            if not (55 <= diff <= 65):
                continue

            end_str = _get_end_time(event.get("period_end", 0))
            etype   = event.get("event_type", "buoi_hoc")
            emoji   = EMOJI_MAP.get(etype, "📌")

            message = (
                f"⏰ *Còn 1 tiếng nữa có lớp!*\n\n"
                f"{emoji} *{event['title']}*\n"
                f"   🏫 Phòng : `{event['room']}`\n"
                f"   👨‍🏫 GV    : {event['teacher']}\n"
                f"   ⏰ Giờ   : {start_str} - {end_str}\n\n"
                f"🎒 Chuẩn bị đồ đạc và đến đúng giờ nhé!"
            )

            try:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            except Exception as e:
                print(f"[1h Reminder] Lỗi gửi {student_id}: {e}")


# ─────────────────────────────────────────
# Giữ lại hàm cũ để không break scheduler
# ─────────────────────────────────────────
async def send_upcoming_reminders():
    """DEPRECATED — dùng send_evening_reminders() thay thế."""
    await send_evening_reminders()