from fastapi.testclient import TestClient
from app.main import app
from app.core import events as events_core
from datetime import datetime, timedelta

client = TestClient(app)
USER_ID = 100

# ensure clean state
events_core._EVENTS.clear()


def test_create_event_and_get_list():
    payload = {
        "title": "Học Python",
        "description": "Buổi học cơ bản",
        "start": "2026-01-20T10:00:00",
        "end": "2026-01-20T12:00:00",
        "remind_before_minutes": 30,
        "notify_via": ["telegram"]
    }
    r = client.post('/events', json=payload, headers={"X-User-Id": str(USER_ID)})
    assert r.status_code == 201
    data = r.json()
    assert data['title'] == 'Học Python'

    r2 = client.get('/events', headers={"X-User-Id": str(USER_ID)})
    assert r2.status_code == 200
    lst = r2.json()
    assert len(lst) == 1


def test_get_event_by_id_update_delete():
    # create event
    payload = {
        "title": "Học CSDL",
        "description": "Buổi lab",
        "start": "2026-01-21T14:00:00",
        "end": "2026-01-21T16:00:00",
        "remind_before_minutes": 30,
        "notify_via": ["telegram"]
    }
    r = client.post('/events', json=payload, headers={"X-User-Id": str(USER_ID)})
    event = r.json()
    eid = event['id']

    # get by id
    r2 = client.get(f'/events/{eid}', headers={"X-User-Id": str(USER_ID)})
    assert r2.status_code == 200
    assert r2.json()['title'] == 'Học CSDL'

    # update
    r3 = client.put(f'/events/{eid}', json={"title": "Học CSDL - updated"}, headers={"X-User-Id": str(USER_ID)})
    assert r3.status_code == 200
    assert r3.json()['title'] == 'Học CSDL - updated'

    # delete
    r4 = client.delete(f'/events/{eid}', headers={"X-User-Id": str(USER_ID)})
    assert r4.status_code == 204

    # ensure gone
    r5 = client.get(f'/events/{eid}', headers={"X-User-Id": str(USER_ID)})
    assert r5.status_code == 404


def test_access_control_between_users():
    # user A create
    r = client.post('/events', json={"title":"A","start":"2026-01-22T09:00:00","end":"2026-01-22T10:00:00"}, headers={"X-User-Id": "200"})
    assert r.status_code == 201
    eid = r.json()['id']

    # user B cannot access
    r2 = client.get(f'/events/{eid}', headers={"X-User-Id": "201"})
    assert r2.status_code == 404
