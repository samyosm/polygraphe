from tests.conftest import TOKEN


def test_trial_flow(client):
    assert client.get("/trials").json() == []

    created = client.post(
        "/trials",
        json={"title": "  First  ", "subject": {"name": "Ada", "age": 30, "sex": "female"}},
    )
    assert created.status_code == 201
    trial = created.json()
    assert (trial["title"], trial["status"]) == ("First", "created")

    trial_id = trial["id"]
    started = client.post(f"/trials/{trial_id}/start", json={"device_id": "esp32"}).json()
    assert (started["status"], started["recording_device"]) == ("recording", "esp32")

    with client.websocket_connect(f"/ws/devices/esp32?token={TOKEN}") as ws:
        ws.send_text('{"type": "heart_rate", "value": 71}')
        ws.send_text("{}")
        ws.receive_json()  # error reply: the valid frame before it has been handled

    [measurement] = client.get(f"/trials/{trial_id}/measurements").json()
    assert (measurement["stage"], measurement["kind"]) == ("raw", "heart_rate")

    assert client.post(f"/trials/{trial_id}/stop").json()["status"] == "paused"
    assert client.post(f"/trials/{trial_id}/stop").status_code == 409
    assert client.post(f"/trials/{trial_id}/complete").json()["status"] == "completed"

    assert [t["id"] for t in client.get("/trials", params={"q": "ada"}).json()] == [trial_id]
    assert client.get("/trials", params={"q": "nobody"}).json() == []


def test_validation_and_not_found(client):
    assert client.post("/trials", json={"title": ""}).status_code == 422
    assert client.post("/trials", json={"title": "x", "subject": {"age": -1}}).status_code == 422
    assert client.get("/trials/missing").status_code == 404
    assert client.post("/trials/missing/start", json={"device_id": "a"}).status_code == 404


def test_devices_lists_connected_devices(client):
    assert client.get("/devices").json() == []
    with client.websocket_connect(f"/ws/devices/esp32?token={TOKEN}") as ws:
        ws.send_text("{}")
        ws.receive_json()
        assert client.get("/devices").json() == [{"id": "esp32", "source": "websocket"}]


def test_live_feed_streams_only_while_recording(client):
    trial_id = client.post("/trials", json={"title": "Live"}).json()["id"]

    with (
        client.websocket_connect(f"/trials/{trial_id}/live") as live,
        client.websocket_connect(f"/ws/devices/esp32?token={TOKEN}") as device,
    ):
        device.send_text('{"type": "ignored", "value": 1}')  # not recording yet
        client.post(f"/trials/{trial_id}/start", json={"device_id": "esp32"})
        device.send_text('{"type": "heart_rate", "value": 72}')
        message = live.receive_json()
        assert (message["kind"], message["fields"]) == ("heart_rate", {"value": 72})


def test_live_backfills_since(client):
    trial_id = client.post("/trials", json={"title": "Live"}).json()["id"]
    client.post(f"/trials/{trial_id}/start", json={"device_id": "esp32"})
    with client.websocket_connect(f"/ws/devices/esp32?token={TOKEN}") as device:
        device.send_text('{"type": "heart_rate", "value": 60, "timestamp": "2020-01-01T00:00:00Z"}')
        device.send_text('{"type": "heart_rate", "value": 61}')
        device.send_text("{}")
        device.receive_json()

    started = client.get(f"/trials/{trial_id}").json()["segments"][0]["started_at"]
    with client.websocket_connect(f"/trials/{trial_id}/live?since={started}") as live:
        assert live.receive_json()["fields"] == {"value": 61}


def test_details_can_be_edited_after_completion(client):
    trial_id = client.post("/trials", json={"title": "Draft", "subject": {"age": 3}}).json()["id"]
    client.post(f"/trials/{trial_id}/complete")

    body = {"title": "Final", "description": "Notes", "subject": {"name": "Bob", "sex": "male"}}
    updated = client.put(f"/trials/{trial_id}", json=body).json()
    assert (updated["title"], updated["description"], updated["status"]) == (
        "Final",
        "Notes",
        "completed",
    )
    assert updated["subject"] == {"name": "Bob", "age": None, "sex": "male", "culture": None}
    assert client.put(f"/trials/{trial_id}", json={"title": " "}).status_code == 422
    assert client.put("/trials/missing", json={"title": "x"}).status_code == 404


def test_closing_live_feed_releases_its_subscription(client):
    bus = client.app.state.services.bus
    baseline = bus.subscriber_count
    trial_id = client.post("/trials", json={"title": "Live"}).json()["id"]
    client.post(f"/trials/{trial_id}/start", json={"device_id": "esp32"})

    with (
        client.websocket_connect(f"/trials/{trial_id}/live") as live,
        client.websocket_connect(f"/ws/devices/esp32?token={TOKEN}") as device,
    ):
        device.send_text('{"type": "heart_rate", "value": 72}')
        live.receive_json()
        assert bus.subscriber_count == baseline + 1
    assert bus.subscriber_count == baseline


def test_status_filter(client):
    recording = client.post("/trials", json={"title": "A"}).json()["id"]
    client.post("/trials", json={"title": "B"})
    client.post(f"/trials/{recording}/start", json={"device_id": "esp32"})
    assert [t["id"] for t in client.get("/trials?status=recording").json()] == [recording]


def test_events_announce_every_change(client):
    with client.websocket_connect("/trials/events") as events:
        trial_id = client.post("/trials", json={"title": "A"}).json()["id"]
        client.post(f"/trials/{trial_id}/start", json={"device_id": "esp32"})
        client.put(f"/trials/{trial_id}", json={"title": "B"})
        seen = [events.receive_json() for _ in range(3)]
    assert [(t["id"], t["title"], t["status"]) for t in seen] == [
        (trial_id, "A", "created"),
        (trial_id, "A", "recording"),
        (trial_id, "B", "recording"),
    ]
