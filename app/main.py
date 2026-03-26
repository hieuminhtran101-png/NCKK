# main.py  (UPDATED — thêm GPA module)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import auth, event, telegram, chat, gpa   # ✅ thêm gpa
from app.bot.telegram_bot import build_bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.service.notification_service import (
    send_upcoming_reminders,
    send_evening_reminders,
    send_1h_before_reminders,
)
from app.service.gpa_notification_service import (
    send_gpa_alerts,
    send_monthly_gpa_report,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler     = AsyncIOScheduler()
telegram_app  = build_bot()


@app.get("/")
def root():
    return {"message": "Chao mung den voi AI nhac lich hoc"}


# ── Routers ──────────────────────────────
app.include_router(auth.router)
app.include_router(event.router)
app.include_router(telegram.router)
app.include_router(chat.router)
app.include_router(gpa.router)      # ✅ thêm


@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
 
    # Nhắc lịch học buổi tối 21:00
    scheduler.add_job(send_evening_reminders, "cron", hour=21, minute=0)

    # Nhắc 1 tiếng trước buổi học — chạy mỗi 30 phút
    scheduler.add_job(send_1h_before_reminders, "cron", minute="0,30")
 
    # Cảnh báo GPA mỗi thứ Hai 8:00
    scheduler.add_job(send_gpa_alerts, "cron", day_of_week="mon", hour=8, minute=0)
 
    # ✅ Báo cáo GPA tháng — ngày 1 hàng tháng lúc 8:00 (gộp cả gợi ý môn yếu)
    scheduler.add_job(send_monthly_gpa_report, "cron", day=1, hour=8, minute=0)
 
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
    scheduler.shutdown()