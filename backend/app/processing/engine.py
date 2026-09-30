import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime

from app.bus import StoredMeasurements
from app.domain import Stage
from app.domain.measurement import utc_now
from app.processing.base import ProcessingContext, Processor
from app.storage import MeasurementRepository

logger = logging.getLogger(__name__)


class ProcessingEngine:
    """Runs processors periodically, only for devices that sent relevant new data.

    Subscribed to the :class:`~app.bus.MeasurementBus`, it marks ``(processor, device)``
    pairs as pending when raw data arrives, and each processor has its own loop that
    wakes up every ``processor.interval`` to handle pending devices.
    """

    def __init__(
        self,
        repository: MeasurementRepository,
        processors: Iterable[Processor],
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._processors = list(processors)
        self._clock = clock
        self._pending: dict[str, set[str]] = defaultdict(set)
        self._tasks: list[asyncio.Task] = []

        names = [p.name for p in self._processors]
        if len(names) != len(set(names)):
            raise ValueError(f"Processor names must be unique, got {names}")

    @property
    def processors(self) -> list[Processor]:
        return list(self._processors)

    def on_measurements(self, stored: StoredMeasurements) -> None:
        if stored.stage is not Stage.RAW:
            return
        for measurement in stored.measurements:
            for processor in self._processors:
                if measurement.kind in processor.input_kinds:
                    self._pending[processor.name].add(measurement.device_id)

    async def run_pending(self, processor: Processor) -> None:
        """Run ``processor`` once for every device that has pending data."""
        devices, self._pending[processor.name] = self._pending[processor.name], set()
        for device_id in devices:
            context = ProcessingContext(device_id, self._repository, self._clock())
            try:
                await processor.run(context)
            except Exception:
                logger.exception("Processor %s failed for device %s", processor.name, device_id)

    async def start(self) -> None:
        for processor in self._processors:
            task = asyncio.create_task(self._loop(processor), name=f"processor:{processor.name}")
            self._tasks.append(task)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _loop(self, processor: Processor) -> None:
        period = processor.interval.total_seconds()
        while True:
            await asyncio.sleep(period)
            await self.run_pending(processor)
