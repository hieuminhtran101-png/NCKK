#app/router/telegram.py
from fastapi import APIRouter, Header, HTTPException
from app.schemas.telegram import TelegramStatusResponse
from app.service.telegram_service import get_telegram_status, unlink_telegram

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])

# FE gọi để lấy trạng thái + link
@router.get("/status", response_model=TelegramStatusResponse)
def telegram_status(student_id: str = Header()):
    result = get_telegram_status(student_id=student_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

# Huỷ liên kết
@router.delete("/unlink")
def telegram_unlink(student_id: str = Header()):
    success = unlink_telegram(student_id=student_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Đã huỷ liên kết Telegram"}