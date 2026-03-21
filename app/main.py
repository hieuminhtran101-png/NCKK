# main.py  (UPDATED — thêm GPA module)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import auth, event, telegram, chat, gpa   # ✅ thêm gpa
from app.bot.telegram_bot import build_bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.service.notification_service import send_upcoming_reminders
from app.service.gpa_notification_service import (   # ✅ thêm
    send_gpa_alerts,
    send_weak_course_reminders,
    send_monthly_gpa_report,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://nckk-u8qo.vercel.app"],
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
 
    # Nhắc lịch học hàng ngày lúc 14:20
    scheduler.add_job(send_upcoming_reminders, "cron", hour=14, minute=20)
 
    # Cảnh báo GPA mỗi thứ Hai 8:00
    scheduler.add_job(send_gpa_alerts, "cron", day_of_week="mon", hour=8, minute=0)
 
    # Nhắc môn tín chỉ cao đầu mỗi tháng (ngày 1, 8:30)
    scheduler.add_job(send_weak_course_reminders, "cron", day=1, hour=8, minute=30)
 
    # ✅ Báo cáo GPA tháng — ngày 1 hàng tháng lúc 8:00
    scheduler.add_job(send_monthly_gpa_report, "cron", day=1, hour=8, minute=0)
 
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
    scheduler.shutdown()