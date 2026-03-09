# app/service/ai_service.py
import os
import json
from google import genai
from app.service.event_service import (
    create_events,
    get_events,
    update_event,
    delete_event
)
from app.schemas.events import EventCreate, EventUpdate
from app.utils.prompt_builder import build_chat_prompt

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# =============================================
# Dispatcher: action → service có sẵn
# =============================================
def _dispatch(action: str, params: dict, student_id: str):
    if action == "create_event":
        raw_events = params.get("events", [])
        event_objects = [EventCreate(**e) for e in raw_events]
        return create_events(event_objects, creator_id=student_id)

    elif action == "update_event":
        event_id = params.pop("event_id")
        update_data = EventUpdate(**params)
        return update_event(event_id, update_data, creator_id=student_id)

    elif action == "delete_event":
        event_id = params.get("event_id")
        success = delete_event(event_id, creator_id=student_id)
        return {"deleted": success}

    elif action == "get_events":
        return get_events(creator_id=student_id)

    else:  # "answer" hoặc không xác định
        return None


# =============================================
# Hàm chính
# =============================================
def handle_chat(message: str, student_id: str) -> dict:
    # 1. Lấy lịch hiện tại của user
    current_events = get_events(creator_id=student_id)

    # 2. Build prompt
    prompt = build_chat_prompt(message=message, events=current_events)

    # 3. Gọi Gemini (SDK mới: google-genai)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        raw_text = response.text.strip()
    except Exception as e:
        return {
            "reply": f"❌ Lỗi kết nối Gemini: {str(e)}",
            "action": None,
            "data": None
        }

    # 4. Parse JSON — strip ```json nếu Gemini bọc markdown
    try:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "reply": "🤖 Mình chưa hiểu ý bạn lắm, thử nói lại theo cách khác nhé!",
            "action": None,
            "data": None
        }

    action = parsed.get("action", "answer")
    params = parsed.get("params", {})
    reply  = parsed.get("reply", "")

    # 5. Dispatch → gọi service
    try:
        data = _dispatch(action, params, student_id)
    except Exception as e:
        return {
            "reply": f"⚠️ Có lỗi khi thực hiện: {str(e)}",
            "action": action,
            "data": None
        }

    return {
        "reply": reply,
        "action": action,
        "data": data
    }