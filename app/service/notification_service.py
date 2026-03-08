from telegram import Bot
from datetime import datetime, timedelta, timezone
from app.core.database import event_collection, user_collection
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

async def send_upcoming_reminders():
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end   = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)

    # Quét tất cả events ngày mai
    events = list(event_collection.find({
        "start_date": {"$gte": tomorrow_start, "$lte": tomorrow_end}
    }))

    if not events:
        return

    for event in events:
        # Tìm user theo student_id (khóa chính của bạn)
        user = user_collection.find_one({"student_id": event["creator_id"]})

        # Bỏ qua nếu chưa liên kết Telegram
        if not user or not user.get("is_telegram_linked"):
            continue

        await bot.send_message(
            chat_id=user["telegram_chat_id"],
            text=(
                f"📚 *Nhắc nhở buổi học ngày mai!*\n\n"
                f"📌 *{event['title']}*\n"
                f"🏫 Phòng: `{event['room']}`\n"
                f"👨‍🏫 Giáo viên: {event['teacher']}\n"
                f"⏰ Tiết: {event['period_start']} - {event['period_end']}\n"
                f"📅 Ngày: {event['start_date'].strftime('%d/%m/%Y')}"
            ),
            parse_mode="Markdown"
        )