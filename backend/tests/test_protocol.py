from datetime import UTC, datetime

import pytest

from app.ingestion.protocol import ProtocolError, parse_frame


def test_single_value_message():
    [m] = parse_frame('{"type": "heart_rate", "value": 72.5}', "dev")
    assert (m.kind, m.device_id, m.value) == ("heart_rate", "dev", 72.5)
    assert m.timestamp.tzinfo is not None


def test_multi_field_message_with_epoch_ms_timestamp():
    frame = (
        '{"type": "gsr", "fields": {"conductance": 3.1, "raw": 512}, "timestamp": 1727600000123}'
    )
    [m] = parse_frame(frame, "dev", {"source": "websocket"})
    assert dict(m.fields) == {"conductance": 3.1, "raw": 512}
    assert m.timestamp == datetime(2024, 9, 29, 8, 53, 20, 123000, tzinfo=UTC)
    assert m.tags["source"] == "websocket"


def test_batch_message():
    frame = '[{"type": "spo2", "value": 98}, {"type": "heart_rate", "value": 71}]'
    assert [m.kind for m in parse_frame(frame, "dev")] == ["spo2", "heart_rate"]


@pytest.mark.parametrize(
    "frame",
    [
        "not json",
        '{"type": "spo2"}',
        '{"type": "spo2", "value": 1, "fields": {"a": 1}}',
        '{"type": "", "value": 1}',
        '{"type": "spo2", "fields": {}}',
        '{"type": "spo2", "value": 1, "unexpected": true}',
    ],
)
def test_invalid_frames(frame):
    with pytest.raises(ProtocolError):
        parse_frame(frame, "dev")
