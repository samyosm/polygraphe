from collections.abc import Collection, Sequence
from datetime import datetime

from app.bus import MeasurementBus, StoredMeasurements
from app.domain import Measurement, Stage
from app.storage.measurements.base import MeasurementRepository


class PublishingRepository(MeasurementRepository):
    """Decorator that announces every successful write on a :class:`MeasurementBus`.

    Whoever writes (ingestion, any processor) is thereby observable without knowing it.
    """

    def __init__(self, inner: MeasurementRepository, bus: MeasurementBus) -> None:
        self._inner = inner
        self._bus = bus

    @property
    def inner(self) -> MeasurementRepository:
        return self._inner

    async def start(self) -> None:
        await self._inner.start()

    async def close(self) -> None:
        await self._inner.close()

    async def write(self, stage: Stage, measurements: Sequence[Measurement]) -> None:
        await self._inner.write(stage, measurements)
        if measurements:
            self._bus.publish(StoredMeasurements(stage, measurements))

    async def query(
        self,
        stage: Stage,
        device_id: str,
        kinds: Collection[str] | None,
        start: datetime,
        stop: datetime,
    ) -> list[Measurement]:
        return await self._inner.query(stage, device_id, kinds, start, stop)
