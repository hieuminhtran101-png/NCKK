# app/service/ai_service.py  (UPDATED — thêm GPA module)
#
# Thay thế file ai_service.py cũ bằng file này.
# Các thay đổi chính:
#   1. Import thêm gpa_service
#   2. QUERY_ACTIONS thêm các GPA actions
#   3. _dispatch() xử lý GPA actions
#   4. handle_chat() inject GPA context vào prompt

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
    get_upcoming_events,
    update_event,
    delete_event,
)
from app.service.gpa_service import (
    add_grade,
    get_grades,
    get_gpa_summary,
    set_target_gpa,
    delete_grade,
    get_gpa_context_for_ai,
)
from app.schemas.events import EventCreate, EventUpdate
from app.schemas.gpa import StudentCourseCreate, GpaPreset
from app.utils.prompt_builder import build_chat_prompt
from app.utils.prompt_builder_gpa import build_gpa_section, build_gpa_actions_section

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Actions cần fetch data thật → Gemini viết reply
QUERY_ACTIONS = {
    "get_events",
    "get_events_by_date",
    "get_events_by_range",
    "get_events_by_day_of_week",
    "get_events_by_type",
    "get_upcoming_events",
    "get_grades",
    "get_gpa_summary",
}

# Actions GPA chờ xác nhận FE — KHÔNG tự lưu
PENDING_CONFIRM_ACTIONS = {"add_grade"}


# =============================================
# Dispatcher
# =============================================
def _dispatch(action: str, params: dict, student_id: str):

    # ── Event actions ──────────────────────────────────────
    if action == "create_event":
        raw_events = params.get("events", [])
        event_objects = [EventCreate(**e) for e in raw_events]
        return create_events(event_objects, creator_id=student_id)

    elif action == "update_event":
        event_id = params.pop("event_id")
        return update_event(event_id, EventUpdate(**params), creator_id=student_id)

    elif action == "delete_event":
        success = delete_event(params.get("event_id"), creator_id=student_id)
        return {"deleted": success}

    elif action == "get_events":
        return get_events(creator_id=student_id)

    elif action == "get_events_by_date":
        return get_events_by_date(creator_id=student_id, date=params.get("date"))

    elif action == "get_events_by_range":
        return get_events_by_range(
            creator_id=student_id,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
        )

    elif action == "get_events_by_day_of_week":
        return get_events_by_day_of_week(
            creator_id=student_id, day_of_week=params.get("day_of_week")
        )

    elif action == "get_events_by_type":
        return get_events_by_type(
            creator_id=student_id, event_type=params.get("event_type")
        )

    elif action == "get_upcoming_events":
        return get_upcoming_events(creator_id=student_id, days=params.get("days", 7))

    # ── GPA actions ────────────────────────────────────────
    elif action == "add_grade":
        # KHÔNG lưu tại đây — trả về data để FE hiển thị confirm
        # FE sẽ gọi POST /api/gpa/grades/confirm sau khi SV xác nhận
        return {
            "pending_confirm": True,
            "course_code":     params.get("course_code"),
            "score_10":        params.get("score_10"),
            "semester":        params.get("semester"),
        }

    elif action == "get_grades":
        return get_grades(student_id, params.get("semester"))

    elif action == "get_gpa_summary":
        summary = get_gpa_summary(student_id)
        return summary.model_dump() if summary else {}

    elif action == "set_target_gpa":
        preset_raw = params.get("preset")
        preset     = GpaPreset(preset_raw) if preset_raw else None
        new_target = set_target_gpa(
            student_id,
            target_gpa=params.get("target_gpa"),
            preset=preset,
        )
        return {"target_gpa": new_target}

    elif action == "delete_grade":
        success = delete_grade(student_id, params.get("grade_id"))
        return {"deleted": success}

    elif action == "gpa_advice":
        return get_gpa_context_for_ai(student_id)

    else:  # "answer"
        return None


# =============================================
# Hàm chính
# =============================================
def handle_chat(message: str, student_id: str) -> dict:
    # Lấy dữ liệu song song
    current_events  = get_events(creator_id=student_id)
    gpa_context     = get_gpa_context_for_ai(student_id)
    gpa_section     = build_gpa_section(gpa_context)
    gpa_actions     = build_gpa_actions_section()

    prompt = build_chat_prompt(
        message=message,
        events=current_events,
        gpa_section=gpa_section,       # ← inject vào prompt
        gpa_actions=gpa_actions,
    )

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
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

    # Query actions → Gemini viết reply thân thiện
    if data and action in QUERY_ACTIONS:
        reply = _generate_reply(message, data, reply, action)

    return {"reply": reply, "action": action, "data": data}


# =============================================
# Generate reply từ data thật
# =============================================
def _generate_reply(original_message: str, data, fallback_reply: str, action: str) -> str:
    if not data:
        if "gpa" in action:
            return "📊 Chưa có dữ liệu GPA nào. Hãy nhập điểm để bắt đầu nhé!"
        return "📭 Không tìm thấy dữ liệu trong khoảng thời gian này nhé!"

    data_text = json.dumps(data, ensure_ascii=False, default=str)

    if "gpa" in action or action == "get_grades":
        extra = """
Dùng emoji phù hợp:
- GPA tốt → 🎉
- GPA cần cải thiện → 💪
- Đạt mục tiêu → ✅
- Chưa đạt mục tiêu → ⚠️
- Bảng điểm → 📊
"""
    else:
        extra = """
Dùng emoji phù hợp với event_type:
- buoi_hoc → 📚 | thi → 📝 | deadline → ⏰ | hop_nhom → 👥 | su_kien → 🎉
"""

    prompt = f"""
Sinh viên hỏi: "{original_message}"

Dữ liệu từ hệ thống:
{data_text}

Viết 1-3 câu trả lời thân thiện, tự nhiên bằng tiếng Việt dựa trên dữ liệu trên.
{extra}
KHÔNG trả về JSON, chỉ trả về text thuần.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return fallback_reply