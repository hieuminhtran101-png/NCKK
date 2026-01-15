"""
Quản lý lịch học cá nhân của sinh viên.
Sinh viên tự nhập các môn học, giờ học, phòng học, v.v.
"""

from datetime import datetime, time
from typing import Dict, Any, List, Optional
from enum import Enum

# In-memory store
_SCHEDULES: Dict[int, Dict] = {}  # user_id -> {schedule_entries}
_next_id = 1


class DayOfWeek(str, Enum):
    """Các ngày trong tuần."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


def add_schedule_entry(
    user_id: int,
    subject: str,
    day_of_week: str,
    start_time: str,  # HH:MM format
    end_time: str,    # HH:MM format
    room: Optional[str] = None,
    teacher: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Thêm một bài học vào lịch cá nhân.
    
    Args:
        user_id: ID người dùng
        subject: Tên môn học (vd: "Toán", "Anh Văn")
        day_of_week: Ngày trong tuần (monday-sunday)
        start_time: Giờ bắt đầu (HH:MM)
        end_time: Giờ kết thúc (HH:MM)
        room: Phòng học (vd: "A101")
        teacher: Tên giáo viên
        notes: Ghi chú thêm
    """
    global _next_id
    
    if user_id not in _SCHEDULES:
        _SCHEDULES[user_id] = {}
    
    entry_id = str(_next_id)
    _next_id += 1
    
    entry = {
        'id': entry_id,
        'subject': subject,
        'day_of_week': day_of_week.lower(),
        'start_time': start_time,
        'end_time': end_time,
        'room': room,
        'teacher': teacher,
        'notes': notes,
        'created_at': datetime.utcnow()
    }
    
    _SCHEDULES[user_id][entry_id] = entry
    return entry


def get_user_schedule(user_id: int, day_of_week: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lấy lịch học của sinh viên.
    
    Args:
        user_id: ID người dùng
        day_of_week: Lọc theo ngày (nếu None thì trả về toàn bộ)
    
    Returns:
        Danh sách các bài học
    """
    if user_id not in _SCHEDULES:
        return []
    
    entries = list(_SCHEDULES[user_id].values())
    
    if day_of_week:
        entries = [e for e in entries if e['day_of_week'] == day_of_week.lower()]
    
    # Sắp xếp theo giờ bắt đầu
    entries.sort(key=lambda e: e['start_time'])
    return entries


def update_schedule_entry(user_id: int, entry_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Cập nhật một bài học.
    """
    if user_id not in _SCHEDULES or entry_id not in _SCHEDULES[user_id]:
        return None
    
    entry = _SCHEDULES[user_id][entry_id]
    
    # Cập nhật các trường được phép
    for key in ['subject', 'day_of_week', 'start_time', 'end_time', 'room', 'teacher', 'notes']:
        if key in data and data[key] is not None:
            entry[key] = data[key]
    
    entry['updated_at'] = datetime.utcnow()
    return entry


def delete_schedule_entry(user_id: int, entry_id: str) -> bool:
    """
    Xóa một bài học.
    """
    if user_id not in _SCHEDULES or entry_id not in _SCHEDULES[user_id]:
        return False
    
    del _SCHEDULES[user_id][entry_id]
    return True


def get_schedule_entry(user_id: int, entry_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin chi tiết một bài học.
    """
    if user_id not in _SCHEDULES or entry_id not in _SCHEDULES[user_id]:
        return None
    
    return _SCHEDULES[user_id][entry_id]
