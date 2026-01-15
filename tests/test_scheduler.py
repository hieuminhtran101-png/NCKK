"""
Test bộ lập lịch gửi lời nhắc.
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core import scheduler
from app.core import events as events_core
from app.core import telegram as telegram_core
from app.core import auth as auth_core
from datetime import datetime, timedelta
import time

def test_scheduler_initialization():
    """Kiểm tra khởi tạo bộ lập lịch."""
    scheduler.init_scheduler()
    assert scheduler.scheduler is not None
    assert scheduler.scheduler.running
    scheduler.shutdown_scheduler()

def test_reminder_sent_on_time():
    """Kiểm tra lời nhắc được gửi đúng lúc."""
    # Xóa dữ liệu cũ
    auth_core._USERS.clear()
    events_core._EVENTS.clear()
    telegram_core.TELEGRAM_OUTBOX.clear()
    
    # Khởi tạo bộ lập lịch
    scheduler.init_scheduler()
    
    # Tạo người dùng
    user = auth_core.create_user('test@example.com', 'password123', 'Test User')
    user_id = int(user['id'])
    
    # Tạo sự kiện sắp tới 2 phút với nhắc 1 phút trước
    now = datetime.utcnow()
    event_time = now + timedelta(minutes=2)
    
    event_data = {
        'title': 'Học code',
        'description': 'Luyện tập Python',
        'start': event_time,
        'end': event_time + timedelta(minutes=60),
        'remind_before_minutes': 1,
        'notify_via': ['telegram']
    }
    
    event = events_core.create_event(user_id, event_data)
    
    # Đặt Telegram chat ID cho người dùng
    auth_core.set_user_telegram_chat(user_id, 'test_chat_123')
    
    # Gọi hàm kiểm tra lời nhắc trực tiếp
    scheduler.check_and_send_reminders()
    
    # Kiểm tra xem có tin nhắn được gửi không
    assert len(telegram_core.TELEGRAM_OUTBOX) > 0, "Không có tin nhắn nào được gửi"
    assert "Học code" in telegram_core.TELEGRAM_OUTBOX[0][1]
    
    scheduler.shutdown_scheduler()

def test_no_reminder_without_chat_id():
    """Kiểm tra không gửi lời nhắc nếu không có chat ID."""
    # Xóa dữ liệu cũ
    auth_core._USERS.clear()
    events_core._EVENTS.clear()
    telegram_core.TELEGRAM_OUTBOX.clear()
    
    scheduler.init_scheduler()
    
    # Tạo người dùng nhưng không đặt chat ID
    user = auth_core.create_user('noChat@example.com', 'password123', 'No Chat User')
    user_id = int(user['id'])
    
    # Tạo sự kiện sắp tới 2 phút
    now = datetime.utcnow()
    event_time = now + timedelta(minutes=2)
    
    event_data = {
        'title': 'Sự kiện kiểm tra',
        'start': event_time,
        'end': event_time + timedelta(minutes=60),
        'remind_before_minutes': 1,
        'notify_via': ['telegram']
    }
    
    event = events_core.create_event(user_id, event_data)
    
    # Gọi hàm kiểm tra (không có chat ID được đặt)
    scheduler.check_and_send_reminders()
    
    # Không nên có tin nhắn
    assert len(telegram_core.TELEGRAM_OUTBOX) == 0
    
    scheduler.shutdown_scheduler()

