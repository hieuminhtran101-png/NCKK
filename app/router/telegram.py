# app/router/telegram.py
from fastapi import APIRouter, HTTPException, Depends
from app.core.deps import get_current_user
from app.schemas.telegram import TelegramStatusResponse
from app.service.telegram_service import get_telegram_status, unlink_telegram

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])


@router.get("/status", response_model=TelegramStatusResponse)
def telegram_status(student_id: str = Depends(get_current_user)):
    result = get_telegram_status(student_id=student_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.delete("/unlink")
def telegram_unlink(student_id: str = Depends(get_current_user)):
    success = unlink_telegram(student_id=student_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Đã huỷ liên kết Telegram"}