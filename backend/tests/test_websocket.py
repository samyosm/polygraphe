import pytest
from starlette.websockets import WebSocketDisconnect

from app.domain import Stage
from tests.conftest import TOKEN


def raw(client):
    return client.app.state.services.measurements.inner.all(Stage.RAW)


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["processors"] == ["heart_rate_stats", "spo2_stats"]


@pytest.mark.parametrize("query", ["", "?token=wrong"])
def test_rejects_bad_token(client, query):
    with (
        pytest.raises(WebSocketDisconnect) as exc,
        client.websocket_connect(f"/ws/devices/esp32{query}"),
    ):
        pass
    assert exc.value.code == 1008


def test_accepts_bearer_header_and_stores_raw(client):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    with client.websocket_connect("/ws/devices/esp32", headers=headers) as ws:
        ws.send_text('[{"type": "heart_rate", "value": 71}, {"type": "sweat", "value": 0.4}]')
        ws.send_text('{"type": "heart_rate"}')
        assert ws.receive_json()["status"] == "error"  # also proves previous frame was handled

    stored = raw(client)
    assert [(m.kind, m.device_id) for m in stored] == [("heart_rate", "esp32"), ("sweat", "esp32")]
    assert stored[0].tags["source"] == "websocket"


def test_arbitrary_kinds_are_accepted(client):
    with client.websocket_connect(f"/ws/devices/esp32?token={TOKEN}") as ws:
        ws.send_text('{"type": "skin_temperature", "fields": {"celsius": 33.2}}')
        ws.send_text("garbage")
        ws.receive_json()
    assert raw(client)[0].kind == "skin_temperature"
