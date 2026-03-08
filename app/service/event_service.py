from app.core.database import event_collection
from datetime import datetime, timezone
from app.utils.mongo import mongo_to_dict
from bson import ObjectId


def create_events(events, creator_id):

    now = datetime.now(timezone.utc)

    docs = []

    for e in events:
        doc = {
            "title": e.title,
            "room": e.room,
            "teacher": e.teacher,
            "day_of_week": e.day_of_week,
            "session": e.session,
            "period_start": e.period_start,
            "period_end": e.period_end,
            "start_date": datetime.combine(e.start_date, datetime.min.time()),
            "end_date": datetime.combine(e.end_date, datetime.min.time()),
            "creator_id": creator_id,
            "created_at": now
        }
        docs.append(doc)

    if len(docs) == 1:
        result = event_collection.insert_one(docs[0])  # ✅ insert docs[0]
        return [mongo_to_dict(docs[0])]                # ✅ dùng docs[0], wrap list

    result = event_collection.insert_many(docs)

    for doc in docs:
        mongo_to_dict(doc)                             # ✅ xóa _id, set id

    return docs            
def get_events(creator_id):
    docs = list(event_collection.find({"creator_id": creator_id}))
    return [mongo_to_dict(doc) for doc in docs]


def get_event_by_id(event_id, creator_id):
    doc = event_collection.find_one({
        "_id": ObjectId(event_id),
        "creator_id": creator_id     # ✅ chỉ lấy event của chính user
    })
    if not doc:
        return None
    return mongo_to_dict(doc)


def update_event(event_id, data, creator_id):
    # Chỉ lấy các field không phải None
    update_fields = {k: v for k, v in data.model_dump().items() if v is not None}

    # Convert date → datetime nếu có
    for field in ("start_date", "end_date"):
        if field in update_fields:
            update_fields[field] = datetime.combine(update_fields[field], datetime.min.time())

    if not update_fields:
        return None

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = event_collection.find_one_and_update(
        {"_id": ObjectId(event_id), "creator_id": creator_id},
        {"$set": update_fields},
        return_document=True   # trả về doc sau khi update
    )

    if not result:
        return None

    return mongo_to_dict(result)


def delete_event(event_id, creator_id):
    result = event_collection.delete_one({
        "_id": ObjectId(event_id),
        "creator_id": creator_id    # ✅ chỉ xóa event của chính user
    })
    return result.deleted_count > 0  # True nếu xóa thành công