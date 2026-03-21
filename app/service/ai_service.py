# app/service/ai_service.py
# Thay thế toàn bộ file bằng version này
# Thay đổi chính:
#   1. handle_chat() xử lý cả "action" đơn lẫn "actions" mảng
#   2. _dispatch_many() chạy nhiều action liên tiếp
#   3. Prompt cập nhật để AI biết trả về "actions" khi cần

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
    add_skip_date,
    add_extra_date,
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

PENDING_CONFIRM_ACTIONS = {"add_grade"}


# =============================================
# Dispatcher đơn
# =============================================
def _dispatch(action: str, params: dict, student_id: str):

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

    elif action == "add_skip_date":
        event_id  = params.get("event_id")
        skip_date = params.get("skip_date")
        success   = add_skip_date(event_id, skip_date, creator_id=student_id)
        return {"success": success, "skip_date": skip_date}

    elif action == "add_extra_date":
        event_id   = params.get("event_id")
        extra_date = params.get("extra_date")
        success    = add_extra_date(event_id, extra_date, creator_id=student_id)
        return {"success": success, "extra_date": extra_date}

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

    elif action == "add_grade":
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

    else:
        return None


# =============================================
# ✅ Dispatcher nhiều action cùng lúc
# =============================================
def _dispatch_many(actions: list, student_id: str) -> list:
    """
    Chạy lần lượt từng action trong mảng.
    Trả về list kết quả tương ứng.
    Nếu 1 action lỗi → ghi nhận lỗi, tiếp tục chạy action còn lại.
    """
    results = []
    for item in actions:
        action = item.get("action", "answer")
        params = item.get("params", {})
        try:
            data = _dispatch(action, params, student_id)
            results.append({
                "action":  action,
                "data":    data,
                "success": True,
            })
        except Exception as e:
            results.append({
                "action":  action,
                "data":    None,
                "success": False,
                "error":   str(e),
            })
    return results


# =============================================
# Hàm chính
# =============================================
def handle_chat(message: str, student_id: str) -> dict:
    current_events = get_events(creator_id=student_id)
    gpa_context    = get_gpa_context_for_ai(student_id)
    gpa_section    = build_gpa_section(gpa_context)
    gpa_actions    = build_gpa_actions_section(
        pending_courses=gpa_context.get("pending_courses", [])
    )

    prompt = build_chat_prompt(
        message=message,
        events=current_events,
        gpa_section=gpa_section,
        gpa_actions=gpa_actions,
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        raw_text = response.text.strip()
    except Exception as e:
        return {"reply": f"❌ Lỗi kết nối Gemini: {str(e)}", "action": None, "data": None}

    # Parse JSON
    try:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return {"reply": "🤖 Mình chưa hiểu ý bạn lắm, thử nói lại nhé!", "action": None, "data": None}

    # ── ✅ Phân biệt: AI trả về 1 action hay nhiều actions ──
    #
    # TH1 — action đơn (format cũ, giữ nguyên):
    # { "action": "add_skip_date", "params": {...}, "reply": "..." }
    #
    # TH2 — nhiều actions (format mới):
    # {
    #   "actions": [
    #     { "action": "add_skip_date",  "params": {...} },
    #     { "action": "add_extra_date", "params": {...} }
    #   ],
    #   "reply": "..."
    # }

    reply = parsed.get("reply", "")

    if "actions" in parsed:
        # ── Nhiều action ──────────────────────────────────
        actions_list = parsed.get("actions", [])
        try:
            multi_results = _dispatch_many(actions_list, student_id)
        except Exception as e:
            return {"reply": f"⚠️ Lỗi xử lý: {str(e)}", "action": "multi", "data": None}

        # Kiểm tra có action nào lỗi không
        errors = [r for r in multi_results if not r["success"]]
        if errors:
            error_msg = " | ".join(r["error"] for r in errors)
            return {
                "reply":   f"⚠️ Một số thao tác thất bại: {error_msg}",
                "action":  "multi",
                "data":    multi_results,
            }

        return {
            "reply":   reply or _build_multi_reply(actions_list, multi_results),
            "action":  "multi",
            "data":    multi_results,
        }

    else:
        # ── Action đơn (logic cũ giữ nguyên) ─────────────
        action = parsed.get("action", "answer")
        params = parsed.get("params", {})

        try:
            data = _dispatch(action, params, student_id)
        except Exception as e:
            return {"reply": f"⚠️ Có lỗi khi thực hiện: {str(e)}", "action": action, "data": None}

        if data and action in QUERY_ACTIONS:
            reply = _generate_reply(message, data, reply, action)

        return {"reply": reply, "action": action, "data": data}


# =============================================
# Auto-reply cho multi action nếu AI không tự viết
# =============================================
def _build_multi_reply(actions_list: list, results: list) -> str:
    """Tạo reply tóm tắt kết quả khi AI không cung cấp reply."""
    lines = []
    for item, result in zip(actions_list, results):
        action = item.get("action")
        params = item.get("params", {})
        if action == "add_skip_date":
            lines.append(f"✅ Đã thêm ngày nghỉ {params.get('skip_date')}")
        elif action == "add_extra_date":
            lines.append(f"✅ Đã thêm ngày học bù {params.get('extra_date')}")
        else:
            lines.append(f"✅ Đã thực hiện {action}")
    return "\n".join(lines) if lines else "✅ Đã thực hiện xong!"


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
Dùng emoji: GPA tốt → 🎉 | cần cải thiện → 💪 | đạt mục tiêu → ✅ | chưa đạt → ⚠️
"""
    else:
        extra = """
Dùng emoji: buoi_hoc → 📚 | thi → 📝 | deadline → ⏰ | hop_nhom → 👥 | su_kien → 🎉
"""

    prompt = f"""
Sinh viên hỏi: "{original_message}"
Dữ liệu: {data_text}
Viết 1-3 câu trả lời thân thiện tiếng Việt. {extra}
KHÔNG trả về JSON.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return fallback_reply