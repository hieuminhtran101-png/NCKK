# app/service/ai_service.py
import os
import json
from google import genai
from app.service.event_service import (
    get_events_by_type,
    create_events,
    get_events,
    get_events_by_date,
    get_events_by_range,
    get_events_by_day_of_week,
    get_events_by_type,
    get_upcoming_events,
    update_event,
    delete_event
)
from app.schemas.events import EventCreate, EventUpdate
from app.utils.prompt_builder import build_chat_prompt

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

QUERY_ACTIONS = {
    "get_events",
    "get_events_by_date",
    "get_events_by_range",
    "get_events_by_day_of_week",
    "get_events_by_type",
    "get_upcoming_events",
}

# =============================================
# Dispatcher
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

    elif action == "get_events_by_date":
        return get_events_by_date(creator_id=student_id, date=params.get("date"))

    elif action == "get_events_by_range":
        return get_events_by_range(
            creator_id=student_id,
            start_date=params.get("start_date"),
            end_date=params.get("end_date")
        )

    elif action == "get_events_by_day_of_week":
        return get_events_by_day_of_week(
            creator_id=student_id,
            day_of_week=params.get("day_of_week")
        )

    elif action == "get_events_by_type":
        return get_events_by_type(
            creator_id=student_id,
            event_type=params.get("event_type")
        )

    elif action == "get_upcoming_events":
        return get_upcoming_events(
            creator_id=student_id,
            days=params.get("days", 7)
        )

    elif action == "get_events_by_type":
        return get_events_by_type(
            creator_id=student_id,
            event_type=params.get("event_type")
        )

    else:  # "answer"
        return None


# =============================================
# Hàm chính
# =============================================
def handle_chat(message: str, student_id: str) -> dict:
    current_events = get_events(creator_id=student_id)
    prompt = build_chat_prompt(message=message, events=current_events)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        raw_text = response.text.strip()
    except Exception as e:
        return {"reply": f"❌ Lỗi kết nối Gemini: {str(e)}", "action": None, "data": None}

    try:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return {"reply": "🤖 Mình chưa hiểu ý bạn lắm, thử nói lại nhé!", "action": None, "data": None}

    action = parsed.get("action", "answer")
    params = parsed.get("params", {})
    reply  = parsed.get("reply", "")

    try:
        data = _dispatch(action, params, student_id)
    except Exception as e:
        return {"reply": f"⚠️ Có lỗi khi thực hiện: {str(e)}", "action": action, "data": None}

    # Nếu là query → bơm data thật cho Gemini viết reply
    if data and action in QUERY_ACTIONS:
        reply = _generate_reply(message, data, reply)

    return {"reply": reply, "action": action, "data": data}


def _generate_reply(original_message: str, data: list, fallback_reply: str) -> str:
    if not data:
        return "📭 Không tìm thấy lịch học nào trong khoảng thời gian này nhé!"

    data_text = json.dumps(data, ensure_ascii=False, default=str)
    prompt = f"""
Sinh viên hỏi: "{original_message}"

Kết quả từ database:
{data_text}

Viết 1 câu trả lời thân thiện, tự nhiên bằng tiếng Việt dựa trên dữ liệu trên.
Dùng emoji phù hợp với event_type:
- buoi_hoc  → 📚
- thi       → 📝
- deadline  → ⏰
- hop_nhom  → 👥
- su_kien   → 🎉

KHÔNG trả về JSON, chỉ trả về text thuần.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return fallback_reply