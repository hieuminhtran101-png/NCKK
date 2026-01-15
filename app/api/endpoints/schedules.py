"""
API endpoints cho lịch học cá nhân.
"""

from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional, List
from app.schemas.schedule import ScheduleEntryCreate, ScheduleEntryUpdate, ScheduleEntryOut
from app.core import schedules
from app.core.auth_mongo import get_current_user

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", status_code=201)
def create_schedule_entry(
    payload: ScheduleEntryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Tạo một bài học trong lịch cá nhân."""
    from bson import ObjectId
    from app.db.mongodb import get_db
    from datetime import datetime
    
    db = get_db()
    user_id = current_user.get('user_id')
    
    schedule_data = {
        "user_id": ObjectId(user_id),
        "subject": payload.subject,
        "day_of_week": payload.day_of_week,
        "start_time": payload.start_time,
        "end_time": payload.end_time,
        "room": payload.room,
        "teacher": getattr(payload, 'teacher', ''),
        "notes": getattr(payload, 'notes', ''),
        "created_at": datetime.utcnow()
    }
    
    result = db["schedules"].insert_one(schedule_data)
    schedule_data["id"] = str(result.inserted_id)
    schedule_data["user_id"] = str(schedule_data["user_id"])
    
    return {
        "id": schedule_data["id"],
        "subject": schedule_data["subject"],
        "day_of_week": schedule_data["day_of_week"],
        "start_time": schedule_data["start_time"],
        "end_time": schedule_data["end_time"],
        "room": schedule_data["room"]
    }


@router.get("", response_model=List[ScheduleEntryOut])
def list_schedule(
    day_of_week: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Lấy lịch học của sinh viên."""
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    entries = schedules.get_user_schedule(user_id, day_of_week)
    return [ScheduleEntryOut(**e) for e in entries]


@router.get("/{entry_id}", response_model=ScheduleEntryOut)
def get_schedule_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Lấy chi tiết một bài học."""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    entry = schedules.get_schedule_entry(user_id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    
    return ScheduleEntryOut(**entry)


@router.put("/{entry_id}", response_model=ScheduleEntryOut)
def update_schedule_entry(
    entry_id: str,
    payload: ScheduleEntryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Cập nhật một bài học."""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    entry = schedules.update_schedule_entry(
        user_id,
        entry_id,
        payload.model_dump(exclude_unset=True)
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    
    return ScheduleEntryOut(**entry)


@router.delete("/{entry_id}", status_code=204)
def delete_schedule_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Xóa một bài học."""
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    ok = schedules.delete_schedule_entry(user_id, entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    
    return
