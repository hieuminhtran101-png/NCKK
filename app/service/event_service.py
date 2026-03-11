# app/service/event_service.py
from app.core.database import event_collection
from datetime import datetime, timezone, timedelta
from app.utils.mongo import mongo_to_dict
from bson import ObjectId

WEEKDAY_MAP = {0: "T2", 1: "T3", 2: "T4", 3: "T5", 4: "T6", 5: "T7", 6: "CN"}

def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


# =============================================
# CRUD
# =============================================

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
            "start_date":   datetime.combine(e.start_date, datetime.min.time()),
            "end_date":     datetime.combine(e.end_date,   datetime.min.time()),
            "event_type":   e.event_type.value,   # ✅ lưu string vào DB
            "creator_id":   creator_id,
            "created_at":   now
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
    if not doc:
        return None
    return mongo_to_dict(doc)


def update_event(event_id, data, creator_id):
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}

    for field in ("start_date", "end_date"):
        if field in update_fields:
            update_fields[field] = datetime.combine(update_fields[field], datetime.min.time())

    # ✅ convert EventType enum → string nếu có
    if "event_type" in update_fields and hasattr(update_fields["event_type"], "value"):
        update_fields["event_type"] = update_fields["event_type"].value

    if not update_fields:
        return None

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = event_collection.find_one_and_update(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$set": update_fields},
        return_document=True
    )
    if not result:
        return None
    return mongo_to_dict(result)


def delete_event(event_id, creator_id):
    result = event_collection.delete_one({
        "_id": ObjectId(event_id),
        "creator_id": creator_id
    })
    return result.deleted_count > 0


# =============================================
# QUERY CHO AI AGENT
# =============================================

def get_events_by_date(creator_id: str, date: str):
    target      = _parse_date(date)
    day_of_week = WEEKDAY_MAP[target.weekday()]
    docs = list(event_collection.find({
        "creator_id":  creator_id,
        "start_date":  {"$lte": target},
        "end_date":    {"$gte": target},
        "day_of_week": day_of_week
    }))
    return [mongo_to_dict(doc) for doc in docs]


def get_events_by_range(creator_id: str, start_date: str, end_date: str):
    start = _parse_date(start_date)
    end   = _parse_date(end_date)
    days_in_range = set()
    cur = start
    while cur <= end:
        days_in_range.add(WEEKDAY_MAP[cur.weekday()])
        cur += timedelta(days=1)
    docs = list(event_collection.find({
        "creator_id":  creator_id,
        "start_date":  {"$lte": end},
        "end_date":    {"$gte": start},
        "day_of_week": {"$in": list(days_in_range)}
    }))
    return [mongo_to_dict(doc) for doc in docs]


def get_events_by_day_of_week(creator_id: str, day_of_week: str):
    docs = list(event_collection.find({
        "creator_id":  creator_id,
        "day_of_week": day_of_week
    }))
    return [mongo_to_dict(doc) for doc in docs]


def get_upcoming_events(creator_id: str, days: int = 7):
    now   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    until = now + timedelta(days=days)
    days_in_range = set()
    cur = now
    while cur <= until:
        days_in_range.add(WEEKDAY_MAP[cur.weekday()])
        cur += timedelta(days=1)
    docs = list(event_collection.find({
        "creator_id":  creator_id,
        "start_date":  {"$lte": until},
        "end_date":    {"$gte": now},
        "day_of_week": {"$in": list(days_in_range)}
    }).sort("start_date", 1))
    return [mongo_to_dict(doc) for doc in docs]


# ✅ HÀM MỚI — lọc theo event_type
def get_events_by_type(creator_id: str, event_type: str):
    """Lấy tất cả events theo loại: buoi_hoc / thi / deadline / hop_nhom / su_kien"""
    docs = list(event_collection.find({
        "creator_id": creator_id,
        "event_type": event_type
    }))
    return [mongo_to_dict(doc) for doc in docs]