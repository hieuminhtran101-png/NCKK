"""
API endpoints cho sự kiện công khai (admin).
"""

from fastapi import APIRouter, Header, HTTPException
from typing import Optional, List
from app.schemas.schedule import PublicEventCreate, PublicEventUpdate, PublicEventOut
from app.core import public_events

router = APIRouter(prefix="/public-events", tags=["public_events"])


@router.post("", response_model=PublicEventOut, status_code=201)
def create_public_event(
    payload: PublicEventCreate,
    x_user_id: Optional[int] = Header(None)
):
    """
    Admin tạo sự kiện công khai.
    (Hiện tại: bất kỳ người dùng nào cũng có thể tạo, sau này cần xác thực admin)
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    
    # TODO: Kiểm tra xem x_user_id có phải admin không
    
    event = public_events.create_public_event(
        title=payload.title,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        event_type=payload.event_type,
        target_groups=payload.target_groups,
        created_by=x_user_id
    )
    return PublicEventOut(**event)


@router.get("", response_model=List[PublicEventOut])
def list_public_events(
    event_type: Optional[str] = None
):
    """
    Lấy danh sách sự kiện công khai.
    (Bất kỳ ai cũng có thể xem)
    """
    events = public_events.list_public_events(event_type)
    return [PublicEventOut(**e) for e in events]


@router.get("/{event_id}", response_model=PublicEventOut)
def get_public_event(event_id: str):
    """Lấy chi tiết một sự kiện công khai."""
    event = public_events.get_public_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Not found")
    
    return PublicEventOut(**event)


@router.put("/{event_id}", response_model=PublicEventOut)
def update_public_event(
    event_id: str,
    payload: PublicEventUpdate,
    x_user_id: Optional[int] = Header(None)
):
    """
    Admin cập nhật sự kiện công khai.
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    
    # TODO: Kiểm tra xem x_user_id có phải admin hoặc người tạo sự kiện không
    
    event = public_events.update_public_event(
        event_id,
        payload.model_dump(exclude_unset=True)
    )
    if not event:
        raise HTTPException(status_code=404, detail="Not found")
    
    return PublicEventOut(**event)


@router.delete("/{event_id}", status_code=204)
def delete_public_event(
    event_id: str,
    x_user_id: Optional[int] = Header(None)
):
    """Admin xóa sự kiện công khai."""
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    
    # TODO: Kiểm tra xem x_user_id có phải admin hoặc người tạo sự kiện không
    
    ok = public_events.delete_public_event(event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    
    return
