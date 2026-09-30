from collections import defaultdict
from collections.abc import Collection, Sequence
from datetime import datetime

from app.domain import Measurement, Stage
from app.storage.measurements.base import MeasurementRepository


class InMemoryRepository(MeasurementRepository):
    """Non-persistent repository, for tests and for running without a database."""

    def __init__(self) -> None:
        self._data: dict[Stage, list[Measurement]] = defaultdict(list)

    async def write(self, stage: Stage, measurements: Sequence[Measurement]) -> None:
        self._data[stage].extend(measurements)

    async def query(
        self,
        stage: Stage,
        device_id: str,
        kinds: Collection[str] | None,
        start: datetime,
        stop: datetime,
    ) -> list[Measurement]:
        matches = (
            m
            for m in self._data[stage]
            if m.device_id == device_id
            and (kinds is None or m.kind in kinds)
            and start <= m.timestamp < stop
        )
        return sorted(matches, key=lambda m: m.timestamp)

    def all(self, stage: Stage) -> list[Measurement]:
        return list(self._data[stage])
