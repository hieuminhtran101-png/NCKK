from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from app.core import llm
import logging

logger = logging.getLogger(__name__)

# Simple in-memory mock event store for demo/tests
_EVENTS: Dict[int, List[Dict[str, Any]]] = {}


def add_event(user_id: int, title: str, start: datetime, end: datetime):
    _EVENTS.setdefault(user_id, []).append({
        "title": title,
        "start": start,
        "end": end,
    })


def get_events_by_date(user_id: int, target_date: date) -> List[Dict[str, Any]]:
    events = _EVENTS.get(user_id, [])
    out = []
    for e in events:
        if e["start"].date() == target_date:
            out.append(e)
    return out


def calculate_free_slots(events: List[Dict[str, Any]], working_start: time, working_end: time) -> List[Dict[str, str]]:
    # events assumed sorted by start
    if not events:
        return [{"from": working_start.strftime("%H:%M"), "to": working_end.strftime("%H:%M")}]

    slots: List[Dict[str, str]] = []
    sorted_ev = sorted(events, key=lambda x: x["start"])
    cur = datetime.combine(sorted_ev[0]["start"].date(), working_start)
    day = sorted_ev[0]["start"].date()
    day_end = datetime.combine(day, working_end)

    for ev in sorted_ev:
        if ev["start"] > cur:
            # gap
            slots.append({"from": cur.strftime("%H:%M"), "to": ev["start"].strftime("%H:%M")})
        cur = max(cur, ev["end"])
    if cur < day_end:
        slots.append({"from": cur.strftime("%H:%M"), "to": day_end.strftime("%H:%M")})
    return slots


def has_free_slot(user_id: int, target_date: date, time_range: Dict[str, str]) -> bool:
    start_t = datetime.combine(target_date, datetime.strptime(time_range["start"], "%H:%M").time())
    end_t = datetime.combine(target_date, datetime.strptime(time_range["end"], "%H:%M").time())
    events = get_events_by_date(user_id, target_date)
    for ev in events:
        if not (ev["end"] <= start_t or ev["start"] >= end_t):
            return False
    return True


def handle_parse(payload: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Xử lý payload từ LLM.
    Payload có thể từ LLM thực hoặc từ endpoint /agent/interpret.
    """
    intent = payload.get("intent")
    conf = payload.get("confidence", 0.0)
    raw_text = payload.get("raw_text", "")
    
    # Nếu confidence thấp, yêu cầu xác nhận
    if conf < 0.5:
        return {
            "ok": False,
            "needs_clarification": True,
            "messages": ["Xin lỗi, tôi không hiểu rõ. Bạn muốn hỏi gì vậy?"]
        }
    
    # Intent: chat - trả lời tự nhiên (không liên quan lịch học)
    if intent == "chat":
        response = llm.get_chat_response(raw_text)
        return {
            "ok": True,
            "action": "chat",
            "result": {"response": response},
            "messages": [response]
        }
    
    # Intent: get_schedule - lấy lịch học
    if intent == "get_schedule":
        target_date = payload.get("date")
        if isinstance(target_date, str):
            target_date = datetime.fromisoformat(target_date).date()
        events = get_events_by_date(user_id, target_date)
        result = [{"title": e["title"], "time": f"{e['start'].strftime('%H:%M')} - {e['end'].strftime('%H:%M')}"} for e in events]
        return {
            "ok": True,
            "action": "get_schedule",
            "result": {"events": result},
            "messages": [f"Bạn có {len(result)} buổi học trong ngày."]
        }

    # Intent: get_free_time - lấy thời gian rảnh
    if intent == "get_free_time":
        target_date = payload.get("date")
        if isinstance(target_date, str):
            target_date = datetime.fromisoformat(target_date).date()
        wh = payload.get("working_hours", {"start": "08:00", "end": "22:00"})
        events = get_events_by_date(user_id, target_date)
        slots = calculate_free_slots(events, datetime.strptime(wh["start"], "%H:%M").time(), datetime.strptime(wh["end"], "%H:%M").time())
        return {
            "ok": True,
            "action": "get_free_time",
            "result": {"slots": slots},
            "messages": [f"Bạn có {len(slots)} khoảng thời gian rảnh trong ngày."]
        }

    # Intent: check_availability - kiểm tra có rảnh vào lúc cụ thể
    if intent == "check_availability":
        target_date = payload.get("date")
        if isinstance(target_date, str):
            target_date = datetime.fromisoformat(target_date).date()
        time_range = payload.get("time_range")
        available = has_free_slot(user_id, target_date, time_range)
        msg = "Bạn còn rảnh lúc đó." if available else "Bạn bận lúc đó."
        return {
            "ok": True,
            "action": "check_availability",
            "result": {"available": available},
            "messages": [msg]
        }

    return {
        "ok": False,
        "messages": ["Intent không được hỗ trợ"]
    }
