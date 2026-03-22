# app/utils/prompt_builder.py
from datetime import datetime, timezone, timedelta
from typing import List, Optional

WEEKDAY_MAP = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}

# ✅ Tách ra ngoài f-string để tránh lỗi Python 3.10
MULTI_ACTION_EXAMPLE = """{
  "actions": [
    { "action": "add_skip_date",  "params": { "event_id": "...", "skip_date": "YYYY-MM-DD" } },
    { "action": "add_extra_date", "params": { "event_id": "...", "extra_date": "YYYY-MM-DD" } }
  ],
  "reply": "Đã ghi nhận nghỉ T2 và học bù T4 tuần này!"
}"""


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

    time_context = (
        "=== THỜI GIAN HIỆN TẠI (giờ Việt Nam) ===\n"
        f"- Hôm nay  : {WEEKDAY_MAP[today.weekday()]}, {today.isoformat()}\n"
        f"- Ngày mai : {WEEKDAY_MAP[tomorrow.weekday()]}, {tomorrow.isoformat()}\n"
        f"- Ngày kia : {WEEKDAY_MAP[day_after.weekday()]}, {day_after.isoformat()}\n"
        f"- Tuần này : {week_start.isoformat()} → {week_end.isoformat()}\n"
        f"- Tuần sau : {next_week_start.isoformat()} → {next_week_end.isoformat()}\n"
        f"- Giờ hiện tại: {now.strftime('%H:%M')}\n"
        "=========================================="
    )

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

    prompt = (
        "Bạn là MindBot — trợ lý học tập AI, thân thiện, nói tiếng Việt.\n"
        f"{time_context}\n\n"
        "=== TOÀN BỘ LỊCH HỌC CỦA SINH VIÊN ===\n"
        f"{events_text}"
        "========================================\n\n"
        f"{gpa_section}\n\n"
        "Nhiệm vụ: phân tích tin nhắn → trả về JSON duy nhất. KHÔNG markdown, KHÔNG giải thích.\n\n"
        "{\n"
        '  "action": "<action>",\n'
        '  "params": { ... },\n'
        '  "reply": "<trả lời thân thiện>"\n'
        "}\n\n"
        "=== DANH SÁCH ACTION ===\n\n"
        "[CRUD SỰ KIỆN]\n"
        '- "create_event"  → thêm lịch\n'
        '- "update_event"  → sửa lịch (cần event_id)\n'
        '- "delete_event"  → xóa lịch (cần event_id)\n'
        '- "add_skip_date"   → thêm ngày nghỉ bất thường\n'
        '- "add_extra_date"  → thêm ngày học bù\n\n'
        "[QUERY SỰ KIỆN]\n"
        '- "get_events_by_date"         → hôm nay / ngày mai / ngày X\n'
        '- "get_events_by_range"        → tuần này / tuần sau / từ A đến B\n'
        '- "get_events_by_day_of_week"  → mỗi thứ mấy\n'
        '- "get_upcoming_events"        → sắp tới / deadline gần\n'
        '- "get_events_by_type"         → theo loại sự kiện\n'
        '- "get_events"                 → tất cả\n\n'
        f"{gpa_actions}\n\n"
        "[HỎI ĐÁP]\n"
        '- "answer" → không cần query DB, params = {}\n\n'
        "=== PARAMS SỰ KIỆN ===\n\n"
        "create_event:\n"
        '{ "events": [{\n'
        '    "title", "room", "teacher",\n'
        '    "day_of_week": "T2|T3|T4|T5|T6|T7|CN",\n'
        '    "session": "sáng|chiều|tối",\n'
        '    "period_start": int, "period_end": int,\n'
        '    "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",\n'
        '    "event_type": "buoi_hoc|thi|deadline|hop_nhom|su_kien"\n'
        "}] }\n\n"
        'update_event:   { "event_id": "...", ...fields... }\n'
        'delete_event:   { "event_id": "..." }\n'
        'add_skip_date:  { "event_id": "...", "skip_date": "YYYY-MM-DD" }\n'
        'add_extra_date: { "event_id": "...", "extra_date": "YYYY-MM-DD" }\n'
        'get_events_by_date:        { "date": "YYYY-MM-DD" }\n'
        'get_events_by_range:       { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }\n'
        'get_events_by_day_of_week: { "day_of_week": "T2|T3|..." }\n'
        'get_upcoming_events:       { "days": 7 }\n'
        'get_events_by_type:        { "event_type": "buoi_hoc|thi|deadline|hop_nhom|su_kien" }\n'
        "get_events:                {}\n\n"
        "=== PHÂN LOẠI event_type ===\n"
        '- "buoi_hoc" → lịch học thường | "thi" → thi/kiểm tra\n'
        '- "deadline" → nộp bài | "hop_nhom" → họp nhóm | "su_kien" → sự kiện trường\n\n'
        "=== QUY TẮC THỜI GIAN ===\n"
        f'- "hôm nay"  → {today.isoformat()}\n'
        f'- "ngày mai" → {tomorrow.isoformat()}\n'
        f'- "ngày kia" → {day_after.isoformat()}\n'
        f'- "tuần này" → {week_start.isoformat()} → {week_end.isoformat()}\n'
        f'- "tuần sau" → {next_week_start.isoformat()} → {next_week_end.isoformat()}\n\n'
        "=== MULTI ACTION (khi cần làm 2 việc cùng lúc) ===\n\n"
        'Thay vì trả về 1 action, trả về mảng "actions":\n\n'
        f"{MULTI_ACTION_EXAMPLE}\n\n"
        "DÙNG KHI:\n"
        '- SV nói "thầy dời lịch T2 sang T4" → skip T2 + extra T4 cùng lúc\n'
        '- SV nói "tuần này nghỉ T2, học bù T4" → skip T2 + extra T4 cùng lúc\n\n'
        "KHÔNG dùng khi:\n"
        '- SV chỉ nói "thầy báo nghỉ T2 tuần này" mà không đề cập bù\n'
        '  → action="answer", hỏi lại: "Buổi này có học bù không?"\n'
        "- Chỉ có 1 việc cần làm → dùng format action đơn như bình thường\n\n"
        "=== LƯU Ý ===\n"
        "- Thiếu thông tin → action=\"answer\", hỏi lại\n"
        "- add_grade → reply phải hỏi xác nhận: \"Bạn có muốn lưu điểm X cho môn Y không?\"\n"
        "- Không rõ event/grade nào để xoá/sửa → action=\"answer\", hỏi lại\n\n"
        "=== TIN NHẮN ===\n"
        f"{message}"
    )

    return prompt.strip()