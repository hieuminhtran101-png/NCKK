from fastapi.testclient import TestClient
from app.main import app
from app.core import telegram as tg_core
from app.core import auth as auth_core
from app.core import events as events_core

client = TestClient(app)


def test_connect_and_today_webhook():
    # create user
    user = auth_core.create_user('tguser@example.com', 'pass')
    uid = int(user['id'])
    # create an event for today
    events_core.create_event(uid, {"title":"Buổi sáng","start":"2026-01-15T09:00:00","end":"2026-01-15T10:00:00"})

    # connect chat
    r = client.post('/telegram/connect', json={"chat_id": "chat-123"}, headers={"X-User-Id": str(uid)})
    assert r.status_code == 200
    assert auth_core.find_user_by_telegram_chat('chat-123') is not None

    # simulate webhook /today
    payload = {"message": {"chat": {"id": "chat-123"}, "text": "/today"}}
    r2 = client.post('/telegram/webhook', json=payload)
    assert r2.status_code == 200
    # check outbox
    assert len(tg_core.TELEGRAM_OUTBOX) >= 1
    assert any('Buổi sáng' in msg for (_chat, msg) in tg_core.TELEGRAM_OUTBOX)
