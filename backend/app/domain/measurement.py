from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType

type FieldValue = float | int | bool | str

DEFAULT_FIELD = "value"


class Stage(StrEnum):
    """Where a measurement sits in the pipeline."""

    RAW = "raw"
    """Exactly what the device sent, stored before any processing."""
    PROCESSED = "processed"
    """Output of processors."""


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Measurement:
    """A single timestamped sample coming from (or derived from) a device.

    ``kind`` identifies what was measured (see :mod:`app.domain.kinds`), ``fields``
    holds one or more values. Single-valued measurements use the ``"value"`` field.
    """

    kind: str
    device_id: str
    fields: Mapping[str, FieldValue]
    timestamp: datetime = field(default_factory=utc_now)
    tags: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.kind:
            raise ValueError("Measurement kind must not be empty")
        if not self.fields:
            raise ValueError("Measurement must have at least one field")
        if self.timestamp.tzinfo is None:
            raise ValueError("Measurement timestamp must be timezone-aware")
        # Freeze the mappings so a measurement can safely be shared between consumers.
        object.__setattr__(self, "fields", MappingProxyType(dict(self.fields)))
        object.__setattr__(self, "tags", MappingProxyType(dict(self.tags)))

    @classmethod
    def single(
        cls,
        kind: str,
        device_id: str,
        value: FieldValue,
        timestamp: datetime | None = None,
        **tags: str,
    ) -> "Measurement":
        return cls(
            kind=kind,
            device_id=device_id,
            fields={DEFAULT_FIELD: value},
            timestamp=timestamp or utc_now(),
            tags=tags,
        )

    @property
    def value(self) -> FieldValue:
        """The ``"value"`` field of single-valued measurements."""
        return self.fields[DEFAULT_FIELD]
