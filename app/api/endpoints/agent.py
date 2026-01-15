from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional
from app.schemas.agent import ParseResult, InterpretResponse
from app.core import agent as agent_core
from app.core import llm

router = APIRouter()


@router.post("/agent/interpret", response_model=InterpretResponse)
def interpret(payload: ParseResult, x_user_id: Optional[int] = Header(None)):
    """
    Phân tích câu hỏi và xử lý ý định.
    
    Cách dùng:
    - POST với intent, confidence, raw_text (từ frontend hoặc LLM)
    - Hoặc gọi /chat endpoint để sử dụng LLM tự động
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    
    result = agent_core.handle_parse(payload.model_dump(), int(x_user_id))
    return result


@router.post("/chat", response_model=dict)
def chat(
    message: dict,  # {text: "..."}
    x_user_id: Optional[int] = Header(None)
):
    """
    Endpoint chat tự động - sử dụng LLM để phân tích ý định.
    
    Request:
    {
        "text": "Hôm nay tôi có lịch gì?"
    }
    
    Response:
    {
        "ok": true,
        "action": "get_schedule",
        "result": {...},
        "messages": ["..."]
    }
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    
    text = message.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field")
    
    # Sử dụng LLM để phân tích
    parsed = llm.parse_question_to_json(text)
    
    # Xử lý kết quả
    result = agent_core.handle_parse(parsed, int(x_user_id))
    return result
