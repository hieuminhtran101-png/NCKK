"""
Sự kiện công khai được admin tạo (lịch thi, lịch khai giảng, v.v.)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

# In-memory store
_PUBLIC_EVENTS: Dict[str, Dict] = {}  # event_id -> event_data
_next_id = 1


def create_public_event(
    title: str,
    description: str,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    event_type: str = "general",  # announcement, exam, registration, holiday, etc.
    target_groups: Optional[List[str]] = None,  # ["all", "year1", "year2", ...]
    created_by: Optional[int] = None  # admin user_id
) -> Dict[str, Any]:
    """
    Admin tạo một sự kiện công khai.
    
    Args:
        title: Tiêu đề sự kiện
        description: Mô tả chi tiết
        start_date: Ngày bắt đầu
        end_date: Ngày kết thúc (nếu có)
        event_type: Loại sự kiện
        target_groups: Nhóm sinh viên (nếu None = tất cả)
        created_by: ID admin tạo
    """
    global _next_id
    
    event_id = str(_next_id)
    _next_id += 1
    
    event = {
        'id': event_id,
        'title': title,
        'description': description,
        'start_date': start_date,
        'end_date': end_date,
        'event_type': event_type,
        'target_groups': target_groups or ['all'],
        'created_by': created_by,
        'created_at': datetime.utcnow(),
        'is_active': True
    }
    
    _PUBLIC_EVENTS[event_id] = event
    return event


def list_public_events(event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lấy danh sách sự kiện công khai.
    
    Args:
        event_type: Lọc theo loại sự kiện (nếu None thì trả về tất cả)
    """
    events = [e for e in _PUBLIC_EVENTS.values() if e['is_active']]
    
    if event_type:
        events = [e for e in events if e['event_type'] == event_type]
    
    # Sắp xếp theo ngày bắt đầu
    events.sort(key=lambda e: e['start_date'])
    return events


def get_public_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy chi tiết một sự kiện công khai.
    """
    event = _PUBLIC_EVENTS.get(event_id)
    if event and event['is_active']:
        return event
    return None


def update_public_event(event_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Admin cập nhật sự kiện công khai.
    """
    if event_id not in _PUBLIC_EVENTS:
        return None
    
    event = _PUBLIC_EVENTS[event_id]
    
    # Cập nhật các trường
    for key in ['title', 'description', 'start_date', 'end_date', 'event_type', 'target_groups']:
        if key in data and data[key] is not None:
            event[key] = data[key]
    
    event['updated_at'] = datetime.utcnow()
    return event


def delete_public_event(event_id: str) -> bool:
    """
    Admin xóa sự kiện (soft delete - đánh dấu is_active=False).
    """
    if event_id not in _PUBLIC_EVENTS:
        return False
    
    _PUBLIC_EVENTS[event_id]['is_active'] = False
    _PUBLIC_EVENTS[event_id]['deleted_at'] = datetime.utcnow()
    return True


def is_user_affected_by_event(user_id: int, event: Dict[str, Any]) -> bool:
    """
    Kiểm tra xem sự kiện có ảnh hưởng đến sinh viên không.
    Hiện tại: nếu target_groups chứa "all" thì ảnh hưởng tất cả.
    """
    if 'all' in event.get('target_groups', []):
        return True
    
    # TODO: Kiểm tra nhóm cụ thể (year, major, class, etc.)
    return True
