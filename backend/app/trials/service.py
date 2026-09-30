import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timedelta

from app.broadcast import Broadcaster
from app.bus import MeasurementBus, StagedMeasurement
from app.domain import Stage, Subject, Trial
from app.domain.measurement import utc_now
from app.domain.trial import TrialStatus
from app.storage import MeasurementRepository, TrialRepository

# Device clocks may run slightly ahead of the server's: widen open segments by this much.
CLOCK_TOLERANCE = timedelta(seconds=30)


class TrialNotFoundError(Exception):
    pass


class DeviceBusyError(Exception):
    """The device is already being recorded by another trial."""


class TrialService:
    """Trial use cases, and access to the measurements recorded during a trial."""

    def __init__(
        self,
        trials: TrialRepository,
        measurements: MeasurementRepository,
        bus: MeasurementBus,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._trials = trials
        self._measurements = measurements
        self._bus = bus
        self._clock = clock
        self._lock = asyncio.Lock()
        # device_id -> id of the trial recording it. Kept in memory so the live feed
        # can filter measurements without hitting the database.
        self._recording: dict[str, str] = {}
        self._changes = Broadcaster[Trial]()

    async def start(self) -> None:
        for trial in await self._trials.find(status=TrialStatus.RECORDING):
            if device := trial.recording_device:
                self._recording[device] = trial.id

    # --- Use cases -------------------------------------------------------------------

    async def create(self, title: str, description: str | None, subject: Subject) -> Trial:
        trial = Trial(
            title=title, description=description, subject=subject, created_at=self._clock()
        )
        await self._save(trial)
        return trial

    async def update_details(
        self, trial_id: str, title: str, description: str | None, subject: Subject
    ) -> Trial:
        async with self._lock:
            trial = await self.get(trial_id)
            trial.update_details(title, description, subject)
            await self._save(trial)
            return trial

    async def get(self, trial_id: str) -> Trial:
        trial = await self._trials.get(trial_id)
        if trial is None:
            raise TrialNotFoundError(trial_id)
        return trial

    async def find(
        self, search: str | None = None, status: TrialStatus | None = None
    ) -> list[Trial]:
        return await self._trials.find(search=search, status=status)

    async def start_recording(self, trial_id: str, device_id: str) -> Trial:
        async with self._lock:
            trial = await self.get(trial_id)
            busy_with = self._recording.get(device_id)
            if busy_with is not None and busy_with != trial_id:
                raise DeviceBusyError(f"Device {device_id} is already recorded by another trial")
            trial.start(device_id, self._clock())
            await self._save(trial)
            self._recording[device_id] = trial.id
            return trial

    async def stop_recording(self, trial_id: str) -> Trial:
        return await self._end_recording(trial_id, Trial.stop)

    async def complete(self, trial_id: str) -> Trial:
        return await self._end_recording(trial_id, Trial.complete)

    async def _end_recording(
        self, trial_id: str, transition: Callable[[Trial, datetime], None]
    ) -> Trial:
        async with self._lock:
            trial = await self.get(trial_id)
            device = trial.recording_device
            transition(trial, self._clock())
            await self._save(trial)
            if device is not None:
                self._recording.pop(device, None)
            return trial

    async def _save(self, trial: Trial) -> None:
        """Every change goes through here, so :meth:`changes` never misses one."""
        await self._trials.save(trial)
        self._changes.publish(trial)

    # --- Data --------------------------------------------------------------------------

    async def measurements(
        self, trial: Trial, since: datetime | None = None
    ) -> list[StagedMeasurement]:
        """Every raw and processed measurement recorded during the trial's segments."""
        now = self._clock()
        found: list[StagedMeasurement] = []
        for segment in trial.segments:
            start = max(segment.started_at, since) if since else segment.started_at
            stop = segment.stopped_at or now + CLOCK_TOLERANCE
            if start >= stop:
                continue
            for stage in Stage:
                results = await self._measurements.query(
                    stage, segment.device_id, None, start, stop
                )
                found.extend((stage, m) for m in results)
        return sorted(found, key=lambda item: item[1].timestamp)

    async def live(
        self, trial_id: str, since: datetime | None = None
    ) -> AsyncIterator[StagedMeasurement]:
        """Measurements since ``since``, then new ones as they arrive while recording.

        The subscription starts before the backfill query so nothing falls in between;
        the price is possible duplicates, which consumers should ignore.
        """
        with self._bus.queue() as queue:
            trial = await self.get(trial_id)
            if since is not None:
                for item in await self.measurements(trial, since):
                    yield item
            while True:
                stored = await queue.get()
                for measurement in stored.measurements:
                    if self._recording.get(measurement.device_id) == trial_id:
                        yield stored.stage, measurement

    async def changes(self) -> AsyncIterator[Trial]:
        """Every trial as it is after each change (creation, edit, status), forever."""
        with self._changes.queue() as queue:
            while True:
                yield await queue.get()
