from datetime import datetime
from typing import Dict, Any, List, Optional
import itertools

# In-memory event store for demo
_EVENTS: Dict[int, List[Dict[str, Any]]] = {}
_id_counter = itertools.count(1)


def create_event(user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    eid = str(next(_id_counter))
    ev = {
        "id": eid,
        "title": payload["title"],
        "description": payload.get("description"),
        "start": datetime.fromisoformat(payload["start"]) if isinstance(payload["start"], str) else payload["start"],
        "end": datetime.fromisoformat(payload["end"]) if isinstance(payload["end"], str) else payload["end"],
        "remind_before_minutes": payload.get("remind_before_minutes", 30),
        "notify_via": payload.get("notify_via", ["telegram"]),
    }
    _EVENTS.setdefault(user_id, []).append(ev)
    return ev


def list_events(user_id: int) -> List[Dict[str, Any]]:
    return _EVENTS.get(user_id, [])


def get_event(user_id: int, event_id: str) -> Optional[Dict[str, Any]]:
    for e in _EVENTS.get(user_id, []):
        if e["id"] == event_id:
            return e
    return None


def update_event(user_id: int, event_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    e = get_event(user_id, event_id)
    if not e:
        return None
    for k, v in payload.items():
        if k in e and v is not None:
            if k in ("start", "end") and isinstance(v, str):
                e[k] = datetime.fromisoformat(v)
            else:
                e[k] = v
    return e


def delete_event(user_id: int, event_id: str) -> bool:
    lst = _EVENTS.get(user_id, [])
    for i, e in enumerate(lst):
        if e["id"] == event_id:
            lst.pop(i)
            return True
    return False
