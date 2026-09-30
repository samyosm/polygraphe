from datetime import timedelta

from app.auth import OperatorAuth
from app.domain.measurement import utc_now
from tests.conftest import OPERATOR_PASSWORD


class Clock:
    def __init__(self):
        self.now = utc_now()

    def __call__(self):
        return self.now


def make_auth(clock=None, key="key"):
    return OperatorAuth("secret", key, timedelta(hours=1), clock or utc_now)


def test_sign_in_and_verify():
    auth = make_auth()
    assert auth.sign_in("wrong") is None
    session = auth.sign_in("secret")
    assert auth.verify(session.token)


def test_tampered_foreign_and_garbage_tokens_are_rejected():
    auth = make_auth()
    expiry, _, signature = auth.sign_in("secret").token.partition(".")
    assert not auth.verify(f"{int(expiry) + 3600}.{signature}")
    assert not auth.verify(make_auth(key="other").sign_in("secret").token)
    for garbage in ("", ".", "abc", "123.", "x.y"):
        assert not auth.verify(garbage)


def test_sessions_expire():
    clock = Clock()
    auth = make_auth(clock)
    token = auth.sign_in("secret").token
    clock.now += timedelta(minutes=59)
    assert auth.verify(token)
    clock.now += timedelta(minutes=2)
    assert not auth.verify(token)


def test_operator_endpoints(anonymous):
    assert anonymous.post("/auth/operator", json={"password": "nope"}).status_code == 401
    token = anonymous.post("/auth/operator", json={"password": OPERATOR_PASSWORD}).json()["token"]
    assert anonymous.get("/auth/operator").status_code == 401
    headers = {"Authorization": f"Bearer {token}"}
    assert anonymous.get("/auth/operator", headers=headers).status_code == 204


def test_watching_is_open_but_controlling_is_not(anonymous, client):
    trial_id = client.post("/trials", json={"title": "T"}).json()["id"]
    no_auth = {"Authorization": ""}

    assert anonymous.get("/trials", headers=no_auth).status_code == 200
    assert anonymous.get(f"/trials/{trial_id}", headers=no_auth).status_code == 200
    assert anonymous.get(f"/trials/{trial_id}/measurements", headers=no_auth).status_code == 200
    for method, path, body in [
        ("POST", "/trials", {"title": "x"}),
        ("PUT", f"/trials/{trial_id}", {"title": "x"}),
        ("POST", f"/trials/{trial_id}/start", {"device_id": "d"}),
        ("POST", f"/trials/{trial_id}/stop", None),
        ("POST", f"/trials/{trial_id}/complete", None),
    ]:
        response = anonymous.request(method, path, json=body, headers=no_auth)
        assert response.status_code == 401, (method, path)
