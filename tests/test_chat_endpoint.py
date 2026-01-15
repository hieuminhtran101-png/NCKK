"""
Test endpoint /chat (LLM tự động).
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.core import auth as auth_core
from datetime import datetime, timedelta

client = TestClient(app)

def test_chat_endpoint_schedule():
    """Test /chat endpoint với câu hỏi lịch học."""
    auth_core._USERS.clear()
    user = auth_core.create_user('chat_test@example.com', 'pass123', 'Student')
    user_id = int(user['id'])
    
    payload = {"text": "Hôm nay tôi có lịch gì?"}
    resp = client.post('/chat', json=payload, headers={'X-User-Id': str(user_id)})
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True
    assert "action" in data
    assert "messages" in data
    print(f"✓ Chat schedule: action={data['action']}")

def test_chat_endpoint_natural():
    """Test /chat endpoint với chat tự nhiên."""
    auth_core._USERS.clear()
    user = auth_core.create_user('chat_test2@example.com', 'pass123', 'Student')
    user_id = int(user['id'])
    
    payload = {"text": "Xin chào, bạn tên gì?"}
    resp = client.post('/chat', json=payload, headers={'X-User-Id': str(user_id)})
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] == True
    assert data["action"] == "chat"
    assert len(data["messages"]) > 0
    print(f"✓ Chat natural: {data['messages'][0][:30]}...")

def test_chat_endpoint_missing_user():
    """Test /chat endpoint không có X-User-Id."""
    payload = {"text": "Hỏi gì đó"}
    resp = client.post('/chat', json=payload)
    
    assert resp.status_code == 401
    print("✓ Chat missing X-User-Id returns 401")

def test_chat_endpoint_missing_text():
    """Test /chat endpoint không có text."""
    auth_core._USERS.clear()
    user = auth_core.create_user('chat_test3@example.com', 'pass123', 'Student')
    user_id = int(user['id'])
    
    payload = {}
    resp = client.post('/chat', json=payload, headers={'X-User-Id': str(user_id)})
    
    assert resp.status_code == 400
    print("✓ Chat missing text returns 400")

if __name__ == '__main__':
    print("Testing /chat endpoint...\n")
    
    test_chat_endpoint_schedule()
    test_chat_endpoint_natural()
    test_chat_endpoint_missing_user()
    test_chat_endpoint_missing_text()
    
    print("\n✅ Tất cả test /chat endpoint qua!")
