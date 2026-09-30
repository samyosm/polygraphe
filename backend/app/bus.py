"""Announcement of every stored measurement."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.broadcast import Broadcaster
from app.domain import Measurement, Stage

type StagedMeasurement = tuple[Stage, Measurement]


@dataclass(frozen=True, slots=True)
class StoredMeasurements:
    """Measurements that were just written to ``stage``."""

    stage: Stage
    measurements: Sequence[Measurement]


class MeasurementBus(Broadcaster[StoredMeasurements]):
    """Published to by :class:`~app.storage.measurements.PublishingRepository`."""
