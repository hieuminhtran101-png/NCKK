# app/service/event_service.py
from app.core.database import event_collection
from datetime import datetime, timezone, timedelta, date as date_type
from app.utils.mongo import mongo_to_dict
from bson import ObjectId

WEEKDAY_MAP = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}

# Mapping tiết học sang thời gian
PERIOD_TIMES = {
    "sáng": {
        1: ("07:00", "07:50"),
        2: ("08:00", "08:50"),
        3: ("09:00", "09:50"),
        4: ("10:00", "10:50"),
        5: ("11:00", "11:50"),
    },
    "chiều": {
        6: ("12:30", "13:20"),
        7: ("13:30", "14:20"),
        8: ("14:30", "15:20"),
        9: ("15:30", "16:20"),
        10: ("16:30", "17:20"),
    },
    "tối": {
        11: ("18:00", "18:50"),
        12: ("19:00", "19:50"),
        13: ("20:00", "20:50"),
        14: ("21:00", "21:50"),
        15: ("22:00", "22:50"),
    }
}


def convert_period_to_time(session: str, period: int) -> tuple[str, str]:
    """Chuyển tiết học sang thời gian bắt đầu và kết thúc."""
    times = PERIOD_TIMES.get(session, {})
    return times.get(period, ("?", "?"))


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _to_dt(d) -> datetime:
    """Chuyển date object → datetime (không timezone) để so sánh với MongoDB."""
    if isinstance(d, datetime):
        return d.replace(tzinfo=None)
    return datetime.combine(d, datetime.min.time())


# ─────────────────────────────────────────
# Core logic: kiểm tra event có xảy ra vào ngày target không
# ─────────────────────────────────────────
def _event_occurs_on(doc: dict, target: datetime) -> bool:
    """
    Ưu tiên:
    1. extra_dates có target → CÓ học (dù là ngày bù)
    2. skip_dates có target  → KHÔNG học (nghỉ bất thường)
    3. day_of_week khớp + trong khoảng start–end → học bình thường
    """
    target_date = target.date() if isinstance(target, datetime) else target

    # Chuẩn hoá extra_dates và skip_dates từ DB (có thể là datetime hoặc date)
    def to_date(v):
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date_type):
            return v
        return None

    extra = [to_date(d) for d in doc.get("extra_dates", []) if d]
    skip  = [to_date(d) for d in doc.get("skip_dates", []) if d]

    # 1. Ưu tiên cao nhất: ngày học bù
    if target_date in extra:
        return True

    # 2. Ngày nghỉ
    if target_date in skip:
        return False

    # 3. Lịch thường: đúng thứ + trong khoảng
    start = doc["start_date"]
    end   = doc["end_date"]
    start_date = start.date() if isinstance(start, datetime) else start
    end_date   = end.date()   if isinstance(end, datetime)   else end

    if not (start_date <= target_date <= end_date):
        return False

    return WEEKDAY_MAP[target_date.weekday()] == doc.get("day_of_week", "")


# ─────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────

def create_events(events, creator_id):
    now  = datetime.now(timezone.utc)
    docs = []
    for e in events:
        # Kiểm tra trùng lặp
        existing = event_collection.find({
            "creator_id": creator_id,
            "day_of_week": e.day_of_week,
            "session": e.session,
            "$or": [
                {"period_start": {"$lte": e.period_end, "$gte": e.period_start}},
                {"period_end": {"$gte": e.period_start, "$lte": e.period_end}},
                {"$and": [
                    {"period_start": {"$lte": e.period_start}},
                    {"period_end": {"$gte": e.period_end}}
                ]}
            ],
            "start_date": {"$lte": _to_dt(e.end_date)},
            "end_date": {"$gte": _to_dt(e.start_date)}
        })
        if list(existing):
            raise ValueError(f"Trùng lịch: {e.title} vào {e.day_of_week} {e.session} tiết {e.period_start}-{e.period_end}")

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
            # ✅ lưu skip/extra dưới dạng datetime để nhất quán với MongoDB
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


def get_weekly_schedule(creator_id: str, week_start_date: date_type = None):
    """
    Trả về lịch trong tuần theo thời gian thực, từ T2 đến CN.
    Mỗi ngày chia thành sáng, chiều, tối.
    """
    if not week_start_date:
        today = datetime.now(timezone.utc).date()
        week_start_date = today - timedelta(days=today.weekday())  # T2

    week_end_date = week_start_date + timedelta(days=6)  # CN

    # Lấy tất cả events trong khoảng thời gian
    events = list(event_collection.find({
        "creator_id": creator_id,
        "start_date": {"$lte": _to_dt(week_end_date)},
        "end_date": {"$gte": _to_dt(week_start_date)}
    }))

    schedule = {}
    for i in range(7):  # T2 to CN
        day = week_start_date + timedelta(days=i)
        day_key = WEEKDAY_MAP[day.weekday()]
        schedule[day_key] = {"date": day.isoformat(), "sessions": {"sáng": [], "chiều": [], "tối": []}}

        for event in events:
            if _event_occurs_on(event, day):
                session = event["session"]
                start_time, end_time = convert_period_to_time(session, event["period_start"])
                schedule[day_key]["sessions"][session].append({
                    "id": str(event["_id"]),
                    "title": event["title"],
                    "room": event["room"],
                    "teacher": event["teacher"],
                    "period": f"{event['period_start']}-{event['period_end']}",
                    "time": f"{start_time}-{end_time}",
                    "event_type": event["event_type"]
                })

    return schedule


def get_event_by_id(event_id, creator_id):
    doc = event_collection.find_one({
        "_id": ObjectId(event_id),
        "creator_id": creator_id
    })
    return mongo_to_dict(doc) if doc else None


def update_event(event_id, data, creator_id):
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}

    for field in ("start_date", "end_date"):
        if field in update_fields:
            update_fields[field] = _to_dt(update_fields[field])

    if "event_type" in update_fields and hasattr(update_fields["event_type"], "value"):
        update_fields["event_type"] = update_fields["event_type"].value

    # Chuyển skip/extra sang datetime nếu có
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
    target = _parse_date(date)

    # Lấy rộng từ DB: events có thể xảy ra hôm đó
    # (trong khoảng start–end HOẶC có trong extra_dates)
    day_of_week = WEEKDAY_MAP[target.weekday()]
    candidates = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            {
                "start_date":  {"$lte": target},
                "end_date":    {"$gte": target},
                "day_of_week": day_of_week,
            },
            {"extra_dates": target},
        ]
    }))

    # Filter chính xác bằng logic ưu tiên
    result = [doc for doc in candidates if _event_occurs_on(doc, target)]
    return [mongo_to_dict(doc) for doc in result]


def get_events_by_range(creator_id: str, start_date: str, end_date: str):
    """Lấy event xảy ra trong khoảng ngày — tính cả skip/extra."""
    start = _parse_date(start_date)
    end   = _parse_date(end_date)

    # Tập hợp tất cả thứ trong khoảng
    days_in_range = set()
    cur = start
    while cur <= end:
        days_in_range.add(WEEKDAY_MAP[cur.weekday()])
        cur += timedelta(days=1)

    # Lấy rộng từ DB
    candidates = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            {
                "start_date":  {"$lte": end},
                "end_date":    {"$gte": start},
                "day_of_week": {"$in": list(days_in_range)},
            },
            {
                "extra_dates": {"$elemMatch": {"$gte": start, "$lte": end}}
            },
        ]
    }))

    # Filter từng ngày trong khoảng
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
    now   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    until = now + timedelta(days=days)

    days_in_range = set()
    cur = now
    while cur <= until:
        days_in_range.add(WEEKDAY_MAP[cur.weekday()])
        cur += timedelta(days=1)

    candidates = list(event_collection.find({
        "creator_id": creator_id,
        "$or": [
            {
                "start_date":  {"$lte": until},
                "end_date":    {"$gte": now},
                "day_of_week": {"$in": list(days_in_range)},
            },
            {
                "extra_dates": {"$elemMatch": {"$gte": now, "$lte": until}}
            },
        ]
    }).sort("start_date", 1))

    # Expand từng ngày để sort đúng theo ngày xảy ra
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