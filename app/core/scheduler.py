"""
Bộ lập lịch toàn cầu để quản lý các tác vụ nền.
- Gửi lời nhắc cho các sự kiện sắp tới
- Xử lý các tác vụ định kỳ khác
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
from typing import Optional

logger = logging.getLogger(__name__)

scheduler: Optional[BackgroundScheduler] = None


def init_scheduler():
    """Khởi tạo bộ lập lịch."""
    global scheduler
    if scheduler is not None:
        return
    
    scheduler = BackgroundScheduler()
    
    # Thêm công việc kiểm tra lời nhắc mỗi 1 phút
    scheduler.add_job(
        check_and_send_reminders,
        IntervalTrigger(minutes=1),
        id='check_reminders',
        name='Kiểm tra và gửi lời nhắc',
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )
    
    logger.info("Khởi tạo bộ lập lịch thành công")
    scheduler.start()


def shutdown_scheduler():
    """Tắt bộ lập lịch."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Tắt bộ lập lịch")
        scheduler = None


def check_and_send_reminders():
    """
    Kiểm tra tất cả các sự kiện sắp tới và gửi lời nhắc nếu cần.
    Được gọi định kỳ bởi bộ lập lịch.
    """
    from app.core import events as events_core
    from app.core import telegram as telegram_core
    from app.core import auth as auth_core
    
    try:
        now = datetime.utcnow()
        # Kiểm tra trong 24 giờ tới
        future = now + timedelta(hours=24)
        
        # Lặp qua tất cả các người dùng
        for user_id, user_data in auth_core._USERS.items():
            events = events_core.list_events(user_id)
            
            for event in events:
                event_time = event['start']
                remind_before = event.get('remind_before_minutes', 30)
                notification_types = event.get('notify_via', ['telegram'])
                
                # Kiểm tra xem đã đến thời gian gửi lời nhắc chưa
                reminder_time = event_time - timedelta(minutes=remind_before)
                time_until_reminder = (reminder_time - now).total_seconds() / 60
                
                # Gửi nhắc nếu thời gian gửi trong phạm vi 1 phút (vì công việc chạy mỗi 1 phút)
                # Cộng thêm buffer 2 phút để đảm bảo bắt được
                if -2 <= time_until_reminder <= 1:
                    title = event.get('title', 'Sự kiện')
                    time_str = event_time.strftime('%H:%M')
                    msg = f"📋 Lời nhắc: {title} vào lúc {time_str}"
                    
                    if 'telegram' in notification_types:
                        chat_id = user_data.get('telegram_chat_id')
                        if chat_id:
                            telegram_core.send_message(chat_id, msg)
                            logger.info(f"Đã gửi lời nhắc cho user {user_id}: {msg}")
    
    except Exception as e:
        logger.error(f"Lỗi khi gửi lời nhắc: {e}", exc_info=True)
