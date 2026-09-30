from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import ClassVar

from app.domain import Measurement
from app.storage import MeasurementRepository, Stage


@dataclass(frozen=True, slots=True)
class ProcessingContext:
    """Everything a processor needs to know about the run it is part of."""

    device_id: str
    repository: MeasurementRepository
    now: datetime


class Processor[InputT, OutputT](ABC):
    """Turns stored data into derived data, following three overridable steps.

    :meth:`run` is a template method: ``fetch`` → ``process`` → ``store``. Override
    ``fetch`` to choose what data to read, ``process`` for the computation itself (pure,
    no I/O, so it is trivially testable) and ``store`` to decide what to do with the result.

    Class attributes configure how the :class:`~app.processing.engine.ProcessingEngine`
    schedules the processor.
    """

    name: ClassVar[str]
    """Unique identifier, used in logs."""
    input_kinds: ClassVar[frozenset[str]]
    """Raw kinds whose arrival makes this processor run for the sending device."""
    interval: ClassVar[timedelta] = timedelta(seconds=5)
    """Minimum delay between two runs for a given device."""

    async def run(self, context: ProcessingContext) -> OutputT:
        data = await self.fetch(context)
        result = self.process(data)
        await self.store(result, context)
        return result

    @abstractmethod
    async def fetch(self, context: ProcessingContext) -> InputT: ...

    @abstractmethod
    def process(self, data: InputT) -> OutputT: ...

    @abstractmethod
    async def store(self, result: OutputT, context: ProcessingContext) -> None: ...


class WindowedProcessor(Processor[list[Measurement], Sequence[Measurement]]):
    """Common case: read the last ``window`` of raw data, write measurements to the
    processed stage. Subclasses only implement :meth:`process`.
    """

    window: ClassVar[timedelta] = timedelta(seconds=30)

    async def fetch(self, context: ProcessingContext) -> list[Measurement]:
        return await context.repository.query(
            Stage.RAW,
            device_id=context.device_id,
            kinds=self.input_kinds,
            start=context.now - self.window,
            stop=context.now,
        )

    async def store(self, result: Sequence[Measurement], context: ProcessingContext) -> None:
        await context.repository.write(Stage.PROCESSED, result)
