from fastapi.testclient import TestClient
from app.main import app
from app.core import auth as auth_core

client = TestClient(app)


def test_register_and_login():
    # register
    payload = {"email": "hieum@example.com", "password": "secret123", "full_name": "Hieu"}
    r = client.post('/auth/register', json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data['email'] == 'hieum@example.com'

    # login
    r2 = client.post('/auth/login', json={"email": "hieum@example.com", "password": "secret123"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert 'access_token' in d2
    # token should decode to contain email
    payload = auth_core.decode_access_token(d2['access_token'])
    assert payload['email'] == 'hieum@example.com'


def test_login_bad_credentials():
    r = client.post('/auth/login', json={"email": "noone@example.com", "password": "x"})
    assert r.status_code == 401
