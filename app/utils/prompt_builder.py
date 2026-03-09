# app/utils/prompt_builder.py
from datetime import datetime, timezone
from typing import List

def build_chat_prompt(message: str, events: List[dict]) -> str:
    today = datetime.now(timezone.utc).strftime("%A, %d/%m/%Y")

    # Format danh sách events thành text dễ đọc cho Gemini
    if events:
        events_text = ""
        for e in events:
            events_text += (
                f"- ID: {e.get('id')}\n"
                f"  Môn: {e.get('title')}\n"
                f"  Phòng: {e.get('room')}\n"
                f"  Giáo viên: {e.get('teacher')}\n"
                f"  Thứ: {e.get('day_of_week')}\n"
                f"  Buổi: {e.get('session')}\n"
                f"  Tiết: {e.get('period_start')} - {e.get('period_end')}\n"
                f"  Từ ngày: {e.get('start_date')}\n"
                f"  Đến ngày: {e.get('end_date')}\n\n"
            )
    else:
        events_text = "Hiện chưa có sự kiện nào.\n"

    prompt = f"""
Bạn là MindBot — trợ lý học tập AI thông minh, thân thiện, nói tiếng Việt.
Hôm nay là: {today}

=== LỊCH HỌC HIỆN TẠI CỦA SINH VIÊN ===
{events_text}
=========================================

Nhiệm vụ của bạn: đọc tin nhắn của sinh viên và trả về JSON theo đúng cấu trúc sau.
KHÔNG được trả về bất cứ thứ gì ngoài JSON. Không markdown, không giải thích.

Cấu trúc JSON bắt buộc:
{{
  "action": "<action>",
  "params": {{ ... }},
  "reply": "<câu trả lời thân thiện cho sinh viên>"
}}

Các action hợp lệ:
- "answer"       : chỉ hỏi đáp, không thay đổi dữ liệu → params = {{}}
- "create_event" : thêm sự kiện/lịch học mới
- "update_event" : cập nhật sự kiện đã có (bắt buộc có event_id)
- "delete_event" : xóa sự kiện (bắt buộc có event_id)
- "get_events"   : lấy danh sách lịch (thường dùng khi hỏi tổng quan)

Cấu trúc params cho từng action:

create_event:
{{
  "events": [
    {{
      "title": "string",
      "room": "string",
      "teacher": "string",
      "day_of_week": "string",  // ví dụ: "T2", "T3", ... "T7", "CN"
      "session": "string",      // "sáng" | "chiều" | "tối"
      "period_start": int,
      "period_end": int,
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD"
    }}
  ]
}}

update_event:
{{
  "event_id": "string",   // ID của event cần sửa
  "title": "string",      // chỉ điền field nào cần thay đổi
  "room": "string",
  "teacher": "string",
  "day_of_week": "string",
  "session": "string",
  "period_start": int,
  "period_end": int,
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}}

delete_event:
{{
  "event_id": "string"
}}

get_events:
{{}}

Lưu ý quan trọng:
- Nếu thiếu thông tin để tạo event (ví dụ không có ngày), hãy đặt action = "answer" và hỏi lại user trong reply.
- Nếu user muốn xóa/sửa nhưng không rõ event nào, hãy action = "answer" và hỏi lại.
- reply luôn phải thân thiện, dùng emoji phù hợp.
- Ngày tháng luôn định dạng YYYY-MM-DD.
- Nếu user chỉ nói "thứ 3" mà không nói ngày cụ thể, hãy suy luận dựa vào hôm nay là {today}.

=== TIN NHẮN CỦA SINH VIÊN ===
{message}
"""
    return prompt.strip()