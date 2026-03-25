#app/service/notification_service.py
from telegram import Bot
from datetime import datetime, timedelta, timezone
from app.core.database import user_collection
from app.service.event_service import get_events_by_date
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

async def send_upcoming_reminders():
    # Tính ngày mai theo giờ Việt Nam (UTC+7)
    tomorrow = (datetime.now(timezone.utc) + timedelta(hours=7) + timedelta(days=1)).date()
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    users = list(user_collection.find({"is_telegram_linked": True}))

    for user in users:
        student_id = user["student_id"]
        chat_id    = user.get("telegram_chat_id")
        if not chat_id:
            continue

        # Dùng đúng hàm đã có — tính cả skip_dates, extra_dates, day_of_week
        events = get_events_by_date(creator_id=student_id, date=tomorrow_str)
        if not events:
            continue

        lines = [f"📅 *Lịch học ngày mai ({tomorrow.strftime('%d/%m/%Y')})*\n Đại vương ơi"]
        for event in events:
            etype = event.get("event_type", "buoi_hoc")
            EMOJI = {
                "buoi_hoc": "📚", "thi": "📝", "deadline": "⏰",
                "hop_nhom": "👥", "su_kien": "🎉"
            }.get(etype, "📌")
            lines.append(
                f"{EMOJI} *{event['title']}*\n"
                f"   🏫 Phòng: `{event['room']}`\n"
                f"   👨‍🏫 GV: {event['teacher']}\n"
                f"   ⏰ Tiết: {event['period_start']} - {event['period_end']}\n"
            )

        try:
            await bot.send_message(
                chat_id=chat_id,
                text="\n".join(lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[Reminder] Lỗi gửi Telegram {student_id}: {e}")