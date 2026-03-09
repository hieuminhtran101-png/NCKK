# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import auth, event, telegram, chat   # ✅ thêm chat
from app.bot.telegram_bot import build_bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.service.notification_service import send_upcoming_reminders

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()
telegram_app = build_bot()

@app.get("/")
def root():
    return {"message": "Chao mung den voi AI nhac lich hoc"}

# ✅ Routers
app.include_router(auth.router)
app.include_router(event.router)
app.include_router(telegram.router)
app.include_router(chat.router)      # ✅ thêm

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    scheduler.add_job(send_upcoming_reminders, "cron", hour=14, minute=20)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
    scheduler.shutdown()