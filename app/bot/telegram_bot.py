#app/bot/telegram_bot.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from app.service.telegram_service import link_telegram  # ✅ gọi service
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    student_id = context.args[0] if context.args else None

    if not student_id:
        await update.message.reply_text(
            "❌ Liên kết không hợp lệ!\n"
            "Vui lòng vào app và nhấn nút 'Liên kết Telegram'."
        )
        return

    success = link_telegram(student_id, chat_id)

    if not success:
        await update.message.reply_text("❌ Không tìm thấy tài khoản!")
        return

    await update.message.reply_text(
        "✅ Liên kết thành công!\n\n"
        "📚 Bạn sẽ nhận thông báo lịch học trước 1 ngày nhé!",
        parse_mode="Markdown"
    )

def build_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    return app