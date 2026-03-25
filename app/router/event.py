# app/router/event.py
from fastapi import APIRouter, HTTPException, Depends
from app.core.deps import get_current_user
from app.schemas.events import (
    EventBulkCreate, EventUpdate,
    EventAddSkip, EventAddExtra,
)
from app.service.event_service import (
    create_events, get_events, get_event_by_id,
    update_event, delete_event,
    add_skip_date, remove_skip_date,
    add_extra_date, remove_extra_date,
)

router = APIRouter(prefix="/api/events", tags=["events"])


# ── CRUD cơ bản ──────────────────────────────────────────────────────
@router.post("/")
def create_event(
    data: EventBulkCreate,
    student_id: str = Depends(get_current_user),
):
    events = create_events(data.events, creator_id=student_id)
    return {"message": "Tạo sự kiện thành công", "data": events}


@router.get("/")
def list_events(student_id: str = Depends(get_current_user)):
    return {"message": "OK", "data": get_events(creator_id=student_id)}


@router.get("/{event_id}")
def get_event(
    event_id: str,
    student_id: str = Depends(get_current_user),
):
    event = get_event_by_id(event_id, creator_id=student_id)
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": "OK", "data": event}


@router.patch("/{event_id}")
def update_event_route(
    event_id: str,
    data: EventUpdate,
    student_id: str = Depends(get_current_user),
):
    event = update_event(event_id, data, creator_id=student_id)
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": "Cập nhật thành công", "data": event}


@router.delete("/{event_id}")
def delete_event_route(
    event_id: str,
    student_id: str = Depends(get_current_user),
):
    if not delete_event(event_id, creator_id=student_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": "Xóa sự kiện thành công"}


# ── Skip dates ───────────────────────────────────────────────────────
@router.post("/{event_id}/skip")
def add_skip(
    event_id: str,
    data: EventAddSkip,
    student_id: str = Depends(get_current_user),
):
    if not add_skip_date(event_id, data.skip_date, student_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": f"Đã thêm ngày nghỉ {data.skip_date}"}


@router.delete("/{event_id}/skip")
def remove_skip(
    event_id: str,
    data: EventAddSkip,
    student_id: str = Depends(get_current_user),
):
    if not remove_skip_date(event_id, data.skip_date, student_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": f"Đã xoá ngày nghỉ {data.skip_date}"}


# ── Extra dates ──────────────────────────────────────────────────────
@router.post("/{event_id}/extra")
def add_extra(
    event_id: str,
    data: EventAddExtra,
    student_id: str = Depends(get_current_user),
):
    if not add_extra_date(event_id, data.extra_date, student_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": f"Đã thêm ngày học bù {data.extra_date}"}


@router.delete("/{event_id}/extra")
def remove_extra(
    event_id: str,
    data: EventAddExtra,
    student_id: str = Depends(get_current_user),
):
    if not remove_extra_date(event_id, data.extra_date, student_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": f"Đã xoá ngày học bù {data.extra_date}"}