# app/utils/prompt_builder.py  (UPDATED — thêm gpa_section + gpa_actions)
#
# Thay thế file prompt_builder.py cũ bằng file này.
# Thay đổi duy nhất: build_chat_prompt() nhận thêm 2 tham số optional.

from datetime import datetime, timezone, timedelta
from typing import List, Optional

WEEKDAY_MAP = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}


def build_chat_prompt(
    message: str,
    events: List[dict],
    gpa_section: Optional[str] = "",
    gpa_actions: Optional[str] = "",
) -> str:
    now             = datetime.now(timezone.utc) + timedelta(hours=7)
    today           = now.date()
    tomorrow        = today + timedelta(days=1)
    day_after       = today + timedelta(days=2)
    week_start      = today - timedelta(days=today.weekday())
    week_end        = week_start + timedelta(days=6)
    next_week_start = week_start + timedelta(days=7)
    next_week_end   = next_week_start + timedelta(days=6)

    time_context = f"""
=== THỜI GIAN HIỆN TẠI (giờ Việt Nam) ===
- Hôm nay  : {WEEKDAY_MAP[today.weekday()]}, {today.isoformat()}
- Ngày mai : {WEEKDAY_MAP[tomorrow.weekday()]}, {tomorrow.isoformat()}
- Ngày kia : {WEEKDAY_MAP[day_after.weekday()]}, {day_after.isoformat()}
- Tuần này : {week_start.isoformat()} → {week_end.isoformat()}
- Tuần sau : {next_week_start.isoformat()} → {next_week_end.isoformat()}
- Giờ hiện tại: {now.strftime('%H:%M')}
=========================================="""

    events_text = ""
    if events:
        for e in events:
            etype = e.get("event_type", "buoi_hoc")
            EMOJI = {
                "buoi_hoc": "📚", "thi": "📝", "deadline": "⏰",
                "hop_nhom": "👥", "su_kien": "🎉"
            }.get(etype, "📌")
            events_text += (
                f"- ID: {e.get('id')} | {EMOJI} [{etype}] {e.get('title')} | "
                f"Thứ: {e.get('day_of_week')} | Tiết: {e.get('period_start')}-{e.get('period_end')} | "
                f"Phòng: {e.get('room')} | GV: {e.get('teacher')} | "
                f"Từ: {e.get('start_date')} → {e.get('end_date')}\n"
            )
    else:
        events_text = "Chưa có sự kiện nào.\n"

    prompt = f"""
Bạn là MindBot — trợ lý học tập AI, thân thiện, nói tiếng Việt.
{time_context}

=== TOÀN BỘ LỊCH HỌC CỦA SINH VIÊN ===
{events_text}
========================================

{gpa_section}

Nhiệm vụ: phân tích tin nhắn → trả về JSON duy nhất. KHÔNG markdown, KHÔNG giải thích.

{{
  "action": "<action>",
  "params": {{ ... }},
  "reply": "<trả lời thân thiện>"
}}

=== DANH SÁCH ACTION ===

[CRUD SỰ KIỆN]
- "create_event"  → thêm lịch
- "update_event"  → sửa lịch (cần event_id)
- "delete_event"  → xóa lịch (cần event_id)

[QUERY SỰ KIỆN]
- "get_events_by_date"         → hôm nay / ngày mai / ngày X
- "get_events_by_range"        → tuần này / tuần sau / từ A đến B
- "get_events_by_day_of_week"  → mỗi thứ mấy
- "get_upcoming_events"        → sắp tới / deadline gần
- "get_events_by_type"         → theo loại sự kiện
- "get_events"                 → tất cả

{gpa_actions}

[HỎI ĐÁP]
- "answer" → không cần query DB, params = {{}}

=== PARAMS SỰ KIỆN ===

create_event:
{{ "events": [{{
    "title", "room", "teacher",
    "day_of_week": "T2|T3|T4|T5|T6|T7|CN",
    "session": "sáng|chiều|tối",
    "period_start": int, "period_end": int,
    "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
    "event_type": "buoi_hoc|thi|deadline|hop_nhom|su_kien"
}}] }}

update_event:   {{ "event_id": "...", ...fields... }}
delete_event:   {{ "event_id": "..." }}
get_events_by_date:        {{ "date": "YYYY-MM-DD" }}
get_events_by_range:       {{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}
get_events_by_day_of_week: {{ "day_of_week": "T2|T3|..." }}
get_upcoming_events:       {{ "days": 7 }}
get_events_by_type:        {{ "event_type": "buoi_hoc|thi|deadline|hop_nhom|su_kien" }}
get_events:                {{}}

=== PHÂN LOẠI event_type ===
- "buoi_hoc" → lịch học thường | "thi" → thi/kiểm tra
- "deadline" → nộp bài | "hop_nhom" → họp nhóm | "su_kien" → sự kiện trường

=== QUY TẮC THỜI GIAN ===
- "hôm nay"  → {today.isoformat()}
- "ngày mai" → {tomorrow.isoformat()}
- "ngày kia" → {day_after.isoformat()}
- "tuần này" → {week_start.isoformat()} → {week_end.isoformat()}
- "tuần sau" → {next_week_start.isoformat()} → {next_week_end.isoformat()}

=== LƯU Ý ===
- Thiếu thông tin → action="answer", hỏi lại
- add_grade → reply phải hỏi xác nhận: "Bạn có muốn lưu điểm X cho môn Y không?"
- Không rõ event/grade nào để xoá/sửa → action="answer", hỏi lại

=== TIN NHẮN ===
{message}
"""
    return prompt.strip()