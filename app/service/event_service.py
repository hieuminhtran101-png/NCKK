# app/service/event_service.py
from app.core.database import event_collection
from datetime import datetime, timezone, timedelta, date as date_type
from app.utils.mongo import mongo_to_dict
from bson import ObjectId

WEEKDAY_MAP = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}

PERIOD_TIME_MAP = {
    1:  "07:00",
    2:  "07:50",
    3:  "08:40",
    4:  "09:30",
    5:  "10:20",
    6:  "11:10",
    7:  "12:30",
    8:  "13:20",
    9:  "14:10",
    10: "15:00",
    11: "15:50",
    12: "16:40",
    13: "18:00",
    14: "18:50",
    15: "19:40",
}


def convert_period_to_time(session: str, period_start: int, period_end: int) -> tuple[str, str]:
    """Chuyển tiết bắt đầu/kết thúc → giờ thực."""
    start = PERIOD_TIME_MAP.get(period_start, "??:??")
    end   = PERIOD_TIME_MAP.get(period_end,   "??:??")
    return start, end


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _to_dt(d) -> datetime:
    """Chuyển date object → datetime (không timezone) để so sánh với MongoDB."""
    if isinstance(d, datetime):
        return d.replace(tzinfo=None)
    return datetime.combine(d, datetime.min.time())


def _now_vn():
    """Trả về datetime hiện tại theo giờ Việt Nam (UTC+7)."""
    return datetime.now(timezone.utc) + timedelta(hours=7)


# ─────────────────────────────────────────
# Core logic: kiểm tra event có xảy ra vào ngày target không
# ─────────────────────────────────────────
def _event_occurs_on(doc: dict, target) -> bool:
    """
    Ưu tiên:
    1. extra_dates có target → CÓ xảy ra
    2. skip_dates có target  → KHÔNG xảy ra
    3a. ONE-TIME (thi, deadline, su_kien): nằm trong start–end là đủ
    3b. RECURRING (buoi_hoc, hop_nhom): đúng thứ + trong khoảng start–end
    """
    ONE_TIME_TYPES = {"thi", "deadline", "su_kien"}

    target_date = target.date() if isinstance(target, datetime) else target

    def to_date(v):
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date_type):
            return v
        return None

    extra = [to_date(d) for d in doc.get("extra_dates", []) if d]
    skip  = [to_date(d) for d in doc.get("skip_dates", []) if d]

    if target_date in extra:
        return True
    if target_date in skip:
        return False

    start = doc["start_date"]
    end   = doc["end_date"]
    start_date = start.date() if isinstance(start, datetime) else start
    end_date   = end.date()   if isinstance(end, datetime)   else end

    if not (start_date <= target_date <= end_date):
        return False

    event_type = doc.get("event_type", "buoi_hoc")
    if event_type in ONE_TIME_TYPES:
        return True

    return WEEKDAY_MAP[target_date.weekday()] == doc.get("day_of_week", "")


# ─────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────

def create_events(events, creator_id):
    now  = datetime.now(timezone.utc)
    docs = []
    for e in events:
        doc = {
            "title":        e.title,
            "room":         e.room,
            "teacher":      e.teacher,
            "day_of_week":  e.day_of_week,
            "session":      e.session,
            "period_start": e.period_start,
            "period_end":   e.period_end,
            "start_date":   _to_dt(e.start_date),
            "end_date":     _to_dt(e.end_date),
            "event_type":   e.event_type.value,
            "skip_dates":   [_to_dt(d) for d in (e.skip_dates or [])],
            "extra_dates":  [_to_dt(d) for d in (e.extra_dates or [])],
            "creator_id":   creator_id,
            "created_at":   now,
        }
        docs.append(doc)

    if len(docs) == 1:
        event_collection.insert_one(docs[0])
        return [mongo_to_dict(docs[0])]

    event_collection.insert_many(docs)
    for doc in docs:
        mongo_to_dict(doc)
    return docs


def get_events(creator_id):
    docs = list(event_collection.find({"creator_id": creator_id}))
    return [mongo_to_dict(doc) for doc in docs]


def get_event_by_id(event_id, creator_id):
    doc = event_collection.find_one({
        "_id": ObjectId(event_id),
        "creator_id": creator_id
    })
    return mongo_to_dict(doc) if doc else None


def get_weekly_schedule(creator_id: str, week_offset: int = 0):
    """
    Trả về lịch học theo tuần.

    Args:
        creator_id:  ID người dùng
        week_offset: 0 = tuần này (default), 1 = tuần sau, -1 = tuần trước, ...
    """
    today           = _now_vn().date()
    week_start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end_date   = week_start_date + timedelta(days=6)

    events = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            {
                "start_date": {"$lte": _to_dt(week_end_date)},
                "end_date":   {"$gte": _to_dt(week_start_date)},
            },
            {
                "extra_dates": {"$elemMatch": {
                    "$gte": _to_dt(week_start_date),
                    "$lte": _to_dt(week_end_date),
                }}
            },
        ]
    }))

    schedule = {}
    for i in range(7):  # T2 → CN
        day     = week_start_date + timedelta(days=i)
        day_key = WEEKDAY_MAP[day.weekday()]
        schedule[day_key] = {
            "date":     day.isoformat(),
            "is_today": day == today,
            "sessions": {"sáng": [], "chiều": [], "tối": []},
        }

        for event in events:
            if not _event_occurs_on(event, day):
                continue

            session = str(event.get("session", "")).strip().lower()
            session_map = {
                "sang": "sáng", "sáng": "sáng",
                "chieu": "chiều", "chiều": "chiều",
                "toi": "tối", "tối": "tối",
            }
            session_normalized = session_map.get(session)
            if not session_normalized:
                continue

            start_time, end_time = convert_period_to_time(
                session_normalized,
                event.get("period_start"),
                event.get("period_end"),
            )
            schedule[day_key]["sessions"][session_normalized].append({
                "id":         str(event.get("_id")),
                "title":      event.get("title"),
                "room":       event.get("room"),
                "teacher":    event.get("teacher"),
                "period":     f"{event.get('period_start')}-{event.get('period_end')}",
                "time":       f"{start_time}-{end_time}",
                "event_type": event.get("event_type"),
            })

    return {
        "week_offset":  week_offset,
        "week_start":   week_start_date.isoformat(),
        "week_end":     week_end_date.isoformat(),
        "today":        today.isoformat(),
        "schedule":     schedule,
    }


def update_event(event_id, data, creator_id):
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}

    for field in ("start_date", "end_date"):
        if field in update_fields:
            update_fields[field] = _to_dt(update_fields[field])

    if "event_type" in update_fields and hasattr(update_fields["event_type"], "value"):
        update_fields["event_type"] = update_fields["event_type"].value

    for field in ("skip_dates", "extra_dates"):
        if field in update_fields and update_fields[field]:
            update_fields[field] = [_to_dt(d) for d in update_fields[field]]

    if not update_fields:
        return None

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = event_collection.find_one_and_update(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$set": update_fields},
        return_document=True
    )
    return mongo_to_dict(result) if result else None


def delete_event(event_id, creator_id):
    result = event_collection.delete_one({
        "_id": ObjectId(event_id),
        "creator_id": creator_id
    })
    return result.deleted_count > 0


# ─────────────────────────────────────────
# Thêm / bớt ngày skip/extra (thao tác 1 ngày lẻ)
# ─────────────────────────────────────────

def add_skip_date(event_id: str, skip_date, creator_id: str) -> bool:
    """Thêm 1 ngày nghỉ vào skip_dates."""
    dt = _to_dt(skip_date)
    result = event_collection.update_one(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$addToSet": {"skip_dates": dt}}
    )
    return result.modified_count > 0


def remove_skip_date(event_id: str, skip_date, creator_id: str) -> bool:
    """Xoá 1 ngày nghỉ khỏi skip_dates."""
    dt = _to_dt(skip_date)
    result = event_collection.update_one(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$pull": {"skip_dates": dt}}
    )
    return result.modified_count > 0


def add_extra_date(event_id: str, extra_date, creator_id: str) -> bool:
    """Thêm 1 ngày học bù vào extra_dates."""
    dt = _to_dt(extra_date)
    result = event_collection.update_one(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$addToSet": {"extra_dates": dt}}
    )
    return result.modified_count > 0


def remove_extra_date(event_id: str, extra_date, creator_id: str) -> bool:
    """Xoá 1 ngày học bù khỏi extra_dates."""
    dt = _to_dt(extra_date)
    result = event_collection.update_one(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$pull": {"extra_dates": dt}}
    )
    return result.modified_count > 0


# ─────────────────────────────────────────
# QUERY — dùng _event_occurs_on để filter đúng
# ─────────────────────────────────────────

def get_events_by_date(creator_id: str, date: str):
    """Lấy event xảy ra vào ngày cụ thể — tính cả skip/extra."""
    target      = _parse_date(date)
    day_of_week = WEEKDAY_MAP[target.weekday()]
    candidates  = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            # RECURRING: phải đúng thứ
            {
                "start_date":  {"$lte": target},
                "end_date":    {"$gte": target},
                "day_of_week": day_of_week,
                "event_type":  {"$in": ["buoi_hoc", "hop_nhom"]},
            },
            # ONE-TIME: chỉ cần nằm trong khoảng ngày
            {
                "start_date": {"$lte": target},
                "end_date":   {"$gte": target},
                "event_type": {"$in": ["thi", "deadline", "su_kien"]},
            },
            # Extra dates: ưu tiên cao nhất, áp dụng mọi loại
            {"extra_dates": target},
        ]
    }))

    result = [doc for doc in candidates if _event_occurs_on(doc, target)]
    return [mongo_to_dict(doc) for doc in result]


def get_events_by_range(creator_id: str, start_date: str, end_date: str):
    """Lấy event xảy ra trong khoảng ngày — tính cả skip/extra."""
    start = _parse_date(start_date)
    end   = _parse_date(end_date)

    days_in_range = set()
    cur = start
    while cur <= end:
        days_in_range.add(WEEKDAY_MAP[cur.weekday()])
        cur += timedelta(days=1)

    candidates = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            # RECURRING: phải đúng thứ nằm trong range
            {
                "start_date":  {"$lte": end},
                "end_date":    {"$gte": start},
                "day_of_week": {"$in": list(days_in_range)},
                "event_type":  {"$in": ["buoi_hoc", "hop_nhom"]},
            },
            # ONE-TIME: chỉ cần overlap khoảng ngày
            {
                "start_date": {"$lte": end},
                "end_date":   {"$gte": start},
                "event_type": {"$in": ["thi", "deadline", "su_kien"]},
            },
            # Extra dates
            {
                "extra_dates": {"$elemMatch": {"$gte": start, "$lte": end}}
            },
        ]
    }))

    result_set = set()
    result     = []
    cur = start
    while cur <= end:
        for doc in candidates:
            doc_id = str(doc["_id"])
            if _event_occurs_on(doc, cur) and doc_id not in result_set:
                result_set.add(doc_id)
                result.append(mongo_to_dict(dict(doc)))
        cur += timedelta(days=1)

    return result


def get_events_by_day_of_week(creator_id: str, day_of_week: str):
    docs = list(event_collection.find({
        "creator_id":  creator_id,
        "day_of_week": day_of_week
    }))
    return [mongo_to_dict(doc) for doc in docs]


def get_upcoming_events(creator_id: str, days: int = 7):
    """Lấy event sắp tới — tính cả skip/extra."""
    # ✅ Fix: dùng UTC+7 thay vì giờ máy chủ
    now   = _now_vn().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    until = now + timedelta(days=days)

    days_in_range = set()
    cur = now
    while cur <= until:
        days_in_range.add(WEEKDAY_MAP[cur.weekday()])
        cur += timedelta(days=1)

    candidates = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            # RECURRING: phải đúng thứ
            {
                "start_date":  {"$lte": until},
                "end_date":    {"$gte": now},
                "day_of_week": {"$in": list(days_in_range)},
                "event_type":  {"$in": ["buoi_hoc", "hop_nhom"]},
            },
            # ONE-TIME: chỉ cần overlap khoảng ngày
            {
                "start_date": {"$lte": until},
                "end_date":   {"$gte": now},
                "event_type": {"$in": ["thi", "deadline", "su_kien"]},
            },
            # Extra dates
            {
                "extra_dates": {"$elemMatch": {"$gte": now, "$lte": until}}
            },
        ]
    }).sort("start_date", 1))

    occurrences = []
    cur = now
    while cur <= until:
        for doc in candidates:
            if _event_occurs_on(doc, cur):
                d = mongo_to_dict(dict(doc))
                d["occurs_on"] = cur.strftime("%Y-%m-%d")
                occurrences.append(d)
        cur += timedelta(days=1)

    return occurrences


def get_events_by_type(creator_id: str, event_type: str):
    docs = list(event_collection.find({
        "creator_id": creator_id,
        "event_type": event_type
    }))
    return [mongo_to_dict(doc) for doc in docs]