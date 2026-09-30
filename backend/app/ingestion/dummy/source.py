import asyncio
import heapq
from collections.abc import AsyncIterator, Sequence
from datetime import timedelta

from app.domain import Measurement
from app.domain.measurement import utc_now
from app.ingestion.base import DataSource
from app.ingestion.dummy.generators import SignalGenerator


class DummySource(DataSource):
    """Simulated device: emits every generator at its own rate, in real time, forever.

    ``speed`` > 1 runs the simulation faster than real time (handy in tests).
    """

    source_name = "dummy"

    def __init__(
        self,
        device_id: str,
        generators: Sequence[SignalGenerator],
        speed: float = 1.0,
    ) -> None:
        if not generators:
            raise ValueError("DummySource needs at least one generator")
        self._device_id = device_id
        self._generators = list(generators)
        self._speed = speed

    @property
    def device_id(self) -> str:
        return self._device_id

    async def stream(self) -> AsyncIterator[Measurement]:
        loop = asyncio.get_running_loop()
        started_at, wall_start = loop.time(), utc_now()
        # Heap of (simulation time of next sample, generator index).
        schedule = [(0.0, i) for i in range(len(self._generators))]

        while True:
            t, index = heapq.heappop(schedule)
            generator = self._generators[index]
            await asyncio.sleep(max(0.0, started_at + t / self._speed - loop.time()))
            yield Measurement(
                kind=generator.kind,
                device_id=self._device_id,
                fields=generator.sample(t),
                timestamp=wall_start + timedelta(seconds=t / self._speed),
                tags={"source": self.source_name},
            )
            heapq.heappush(schedule, (t + generator.period_s, index))
