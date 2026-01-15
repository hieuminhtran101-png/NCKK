"""
Test lịch học cá nhân và sự kiện công khai.
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.core import auth as auth_core
from app.core import schedules as schedules_core
from app.core import public_events as public_events_core
from datetime import datetime, timedelta

client = TestClient(app)

def setup_user():
    """Tạo user test."""
    auth_core._USERS.clear()
    schedules_core._SCHEDULES.clear()
    public_events_core._PUBLIC_EVENTS.clear()
    user = auth_core.create_user('schedule_test@example.com', 'password123', 'Student')
    return int(user['id'])

# ============ Test Lịch học ============

def test_create_schedule_entry():
    """Test tạo bài học."""
    user_id = setup_user()
    
    payload = {
        'subject': 'Toán cao cấp',
        'day_of_week': 'monday',
        'start_time': '08:00',
        'end_time': '09:30',
        'room': 'A101',
        'teacher': 'Th.S Nguyễn Văn A'
    }
    
    resp = client.post('/schedules', json=payload, headers={'X-User-Id': str(user_id)})
    assert resp.status_code == 201
    data = resp.json()
    assert data['subject'] == 'Toán cao cấp'
    assert data['day_of_week'] == 'monday'

def test_list_schedule():
    """Test lấy lịch học."""
    user_id = setup_user()
    
    # Tạo 3 bài học
    for i, day in enumerate(['monday', 'tuesday', 'wednesday']):
        payload = {
            'subject': f'Môn học {i+1}',
            'day_of_week': day,
            'start_time': '08:00',
            'end_time': '09:30'
        }
        client.post('/schedules', json=payload, headers={'X-User-Id': str(user_id)})
    
    # Lấy tất cả
    resp = client.get('/schedules', headers={'X-User-Id': str(user_id)})
    assert resp.status_code == 200
    assert len(resp.json()) == 3
    
    # Lọc theo ngày
    resp = client.get('/schedules?day_of_week=monday', headers={'X-User-Id': str(user_id)})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]['subject'] == 'Môn học 1'

def test_update_schedule_entry():
    """Test cập nhật bài học."""
    user_id = setup_user()
    
    # Tạo
    payload = {
        'subject': 'Vật lý',
        'day_of_week': 'monday',
        'start_time': '10:00',
        'end_time': '11:30'
    }
    r1 = client.post('/schedules', json=payload, headers={'X-User-Id': str(user_id)})
    entry_id = r1.json()['id']
    
    # Cập nhật
    update_payload = {'subject': 'Vật lý - Cập nhật', 'room': 'B202'}
    r2 = client.put(f'/schedules/{entry_id}', json=update_payload, headers={'X-User-Id': str(user_id)})
    assert r2.status_code == 200
    assert r2.json()['subject'] == 'Vật lý - Cập nhật'
    assert r2.json()['room'] == 'B202'

def test_delete_schedule_entry():
    """Test xóa bài học."""
    user_id = setup_user()
    
    payload = {
        'subject': 'Hóa học',
        'day_of_week': 'friday',
        'start_time': '14:00',
        'end_time': '15:30'
    }
    r1 = client.post('/schedules', json=payload, headers={'X-User-Id': str(user_id)})
    entry_id = r1.json()['id']
    
    # Xóa
    r2 = client.delete(f'/schedules/{entry_id}', headers={'X-User-Id': str(user_id)})
    assert r2.status_code == 204
    
    # Xác nhận đã xóa
    r3 = client.get(f'/schedules/{entry_id}', headers={'X-User-Id': str(user_id)})
    assert r3.status_code == 404

# ============ Test Sự kiện công khai ============

def test_create_public_event():
    """Test admin tạo sự kiện công khai."""
    user_id = setup_user()
    
    now = datetime.utcnow()
    payload = {
        'title': 'Lịch thi cuối kỳ',
        'description': 'Thi tất cả các môn học',
        'start_date': (now + timedelta(days=5)).isoformat(),
        'end_date': (now + timedelta(days=15)).isoformat(),
        'event_type': 'exam',
        'target_groups': ['all']
    }
    
    resp = client.post('/public-events', json=payload, headers={'X-User-Id': str(user_id)})
    assert resp.status_code == 201
    data = resp.json()
    assert data['title'] == 'Lịch thi cuối kỳ'
    assert data['event_type'] == 'exam'

def test_list_public_events():
    """Test lấy danh sách sự kiện công khai."""
    user_id = setup_user()
    
    # Tạo sự kiện
    now = datetime.utcnow()
    for event_type in ['exam', 'announcement', 'holiday']:
        payload = {
            'title': f'Sự kiện {event_type}',
            'description': 'Mô tả',
            'start_date': now.isoformat(),
            'event_type': event_type
        }
        client.post('/public-events', json=payload, headers={'X-User-Id': str(user_id)})
    
    # Lấy tất cả
    resp = client.get('/public-events')
    assert resp.status_code == 200
    assert len(resp.json()) == 3
    
    # Lọc theo loại
    resp = client.get('/public-events?event_type=exam')
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]['event_type'] == 'exam'

def test_update_public_event():
    """Test cập nhật sự kiện công khai."""
    user_id = setup_user()
    
    # Tạo
    now = datetime.utcnow()
    payload = {
        'title': 'Kỳ đăng ký lớp',
        'description': 'Mô tả',
        'start_date': now.isoformat(),
        'event_type': 'registration'
    }
    r1 = client.post('/public-events', json=payload, headers={'X-User-Id': str(user_id)})
    event_id = r1.json()['id']
    
    # Cập nhật
    update_payload = {'title': 'Kỳ đăng ký lớp - Lần 2'}
    r2 = client.put(f'/public-events/{event_id}', json=update_payload, headers={'X-User-Id': str(user_id)})
    assert r2.status_code == 200
    assert r2.json()['title'] == 'Kỳ đăng ký lớp - Lần 2'

def test_delete_public_event():
    """Test xóa sự kiện công khai."""
    user_id = setup_user()
    
    # Tạo
    now = datetime.utcnow()
    payload = {
        'title': 'Lễ khai giảng',
        'description': 'Mô tả',
        'start_date': now.isoformat(),
        'event_type': 'announcement'
    }
    r1 = client.post('/public-events', json=payload, headers={'X-User-Id': str(user_id)})
    event_id = r1.json()['id']
    
    # Xóa
    r2 = client.delete(f'/public-events/{event_id}', headers={'X-User-Id': str(user_id)})
    assert r2.status_code == 204
    
    # Xác nhận đã xóa (soft delete)
    r3 = client.get(f'/public-events/{event_id}')
    assert r3.status_code == 404
