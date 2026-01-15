from fastapi import APIRouter, Header, HTTPException, Request
from typing import Optional
from app.core import telegram as tg_core

router = APIRouter()


@router.post('/telegram/connect')
def connect(chat: dict, x_user_id: Optional[int] = Header(None)):
    # body: {"chat_id": "12345"}
    if x_user_id is None:
        raise HTTPException(status_code=401, detail='Missing X-User-Id header')
    chat_id = chat.get('chat_id')
    if not chat_id:
        raise HTTPException(status_code=400, detail='chat_id required')
    try:
        tg_core.register_chat(int(x_user_id), str(chat_id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post('/telegram/webhook')
async def webhook(req: Request):
    payload = await req.json()
    res = tg_core.handle_update(payload)
    return res
