"""Wire format between the device and the server.

Each websocket text frame is JSON, either a single message or a list of messages::

    {"type": "heart_rate", "value": 72.5}
    {"type": "gsr", "fields": {"conductance": 3.1, "raw": 512}, "timestamp": 1727600000123}
    [{"type": "spo2", "value": 98}, {"type": "heart_rate", "value": 71}]

``timestamp`` is optional (defaults to reception time) and may be ISO 8601 or a Unix
epoch in seconds or milliseconds. Timestamps without a timezone are taken as UTC.
"""

from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from app.domain import FieldValue, Measurement
from app.domain.measurement import DEFAULT_FIELD, utc_now

Name = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")]


class ProtocolError(ValueError):
    """The device sent something that does not follow the protocol."""


class MeasurementMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Name
    value: FieldValue | None = None
    fields: dict[Name, FieldValue] | None = None
    timestamp: datetime | None = None
    tags: dict[Name, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _exactly_one_payload(self) -> Self:
        if (self.value is None) == (self.fields is None):
            raise ValueError("exactly one of 'value' or 'fields' must be given")
        if self.fields is not None and not self.fields:
            raise ValueError("'fields' must not be empty")
        return self

    def to_measurement(self, device_id: str, extra_tags: dict[str, str]) -> Measurement:
        timestamp = self.timestamp or utc_now()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return Measurement(
            kind=self.type,
            device_id=device_id,
            fields=self.fields if self.fields is not None else {DEFAULT_FIELD: self.value},
            timestamp=timestamp,
            tags={**self.tags, **extra_tags},
        )


_Payload = TypeAdapter(MeasurementMessage | list[MeasurementMessage])


def parse_frame(
    frame: str | bytes, device_id: str, extra_tags: dict[str, str] | None = None
) -> list[Measurement]:
    try:
        payload = _Payload.validate_json(frame)
    except ValidationError as exc:
        raise ProtocolError(str(exc)) from exc
    messages = payload if isinstance(payload, list) else [payload]
    return [m.to_measurement(device_id, extra_tags or {}) for m in messages]
