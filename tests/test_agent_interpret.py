from fastapi.testclient import TestClient
from app.main import app
from app.core import agent as agent_core
from datetime import datetime, timedelta

client = TestClient(app)

# prepare a user and some events
USER_ID = 42

# seed events
agent_core._EVENTS.clear()
now = datetime(2026, 1, 14, 9, 0)
agent_core.add_event(USER_ID, "Học toán", now.replace(hour=7), now.replace(hour=9))
agent_core.add_event(USER_ID, "Họp nhóm", now.replace(hour=14), now.replace(hour=15))


def test_get_schedule_success():
    payload = {
        "intent": "get_schedule",
        "confidence": 0.95,
        "raw_text": "Hôm nay tôi có lịch gì?",
        "date": "2026-01-14"
    }
    resp = client.post('/agent/interpret', json=payload, headers={"X-User-Id": str(USER_ID)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["action"] == "get_schedule"
    assert len(data["result"]["events"]) == 2


def test_get_free_time():
    payload = {
        "intent": "get_free_time",
        "confidence": 0.95,
        "raw_text": "Lịch trống hôm nay",
        "date": "2026-01-14",
        "working_hours": {"start": "08:00", "end": "18:00"}
    }
    resp = client.post('/agent/interpret', json=payload, headers={"X-User-Id": str(USER_ID)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["action"] == "get_free_time"
    assert isinstance(data["result"]["slots"], list)


def test_check_availability_true():
    payload = {
        "intent": "check_availability",
        "confidence": 0.95,
        "raw_text": "Chiều mai tôi rảnh không?",
        "date": "2026-01-15",
        "time_range": {"start": "13:00", "end": "18:00"}
    }
    resp = client.post('/agent/interpret', json=payload, headers={"X-User-Id": str(USER_ID)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["action"] == "check_availability"
    assert data["result"]["available"] is True


def test_low_confidence_requires_clarification():
    payload = {
        "intent": "get_schedule",
        "confidence": 0.3,  # Thấp hơn threshold 0.5
        "raw_text": "Mai tôi làm gì?",
        "date": "2026-01-15"
    }
    resp = client.post('/agent/interpret', json=payload, headers={"X-User-Id": str(USER_ID)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert data["needs_clarification"] is True
