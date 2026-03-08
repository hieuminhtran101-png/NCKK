# app/router/events.py
from fastapi import APIRouter, Header, HTTPException
from app.schemas.events import EventBulkCreate, EventUpdate
from app.service.event_service import (
    create_events,
    get_events,
    get_event_by_id,
    update_event,
    delete_event
)

router = APIRouter(
    prefix="/events",
    tags=["events"]
)


@router.post("/")
def create_event(data: EventBulkCreate, student_id: str = Header()):
    events = create_events(data.events, creator_id=student_id)
    return {"message": "Tạo sự kiện thành công", "data": events}


@router.get("/")
def list_events(student_id: str = Header()):
    events = get_events(creator_id=student_id)
    return {"message": "Lấy danh sách sự kiện thành công", "data": events}


@router.get("/{event_id}")
def get_event(event_id: str, student_id: str = Header()):
    event = get_event_by_id(event_id, creator_id=student_id)
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": "Lấy thông tin sự kiện thành công", "data": event}


@router.patch("/{event_id}")
def update_event_route(event_id: str, data: EventUpdate, user_id: str = Header()):
    event = update_event(event_id, data, creator_id=user_id)
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện hoặc không có dữ liệu để cập nhật")
    return {"message": "Cập nhật sự kiện thành công", "data": event}


@router.delete("/{event_id}")
def delete_event_route(event_id: str, user_id: str = Header()):
    success = delete_event(event_id, creator_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return {"message": "Xóa sự kiện thành công"}