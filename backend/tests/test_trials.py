from datetime import timedelta

import pytest

from app.bus import MeasurementBus
from app.domain import Measurement, Stage, Subject, Trial, TrialStateError, TrialStatus
from app.domain.measurement import utc_now
from app.storage.measurements import InMemoryRepository
from app.storage.trials import InMemoryTrialRepository, SqlTrialRepository
from app.trials import DeviceBusyError, TrialService

T0 = utc_now()


def at(seconds: float):
    return T0 + timedelta(seconds=seconds)


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


# --- Domain ------------------------------------------------------------------------------


def test_trial_life_cycle():
    trial = Trial(title="T", created_at=at(0))
    trial.start("dev", at(1))
    assert trial.recording_device == "dev"
    trial.stop(at(2))
    assert (trial.status, trial.recording_device) == (TrialStatus.PAUSED, None)
    trial.start("dev", at(3))
    trial.complete(at(4))
    assert trial.status is TrialStatus.COMPLETED
    assert [(s.started_at, s.stopped_at) for s in trial.segments] == [
        (at(1), at(2)),
        (at(3), at(4)),
    ]
    with pytest.raises(TrialStateError):
        trial.start("dev", at(5))


def test_cannot_stop_when_not_recording():
    with pytest.raises(TrialStateError):
        Trial(title="T", created_at=at(0)).stop(at(1))


def test_title_is_required():
    with pytest.raises(ValueError):
        Trial(title="  ", created_at=at(0))


# --- Repositories ------------------------------------------------------------------------


@pytest.fixture(params=["memory", "sql"])
async def trial_repository(request, tmp_path):
    if request.param == "memory":
        yield InMemoryTrialRepository()
        return
    repository = SqlTrialRepository(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await repository.start()
    yield repository
    await repository.close()


async def test_repository_round_trip_and_search(trial_repository):
    first = Trial(title="Baseline", created_at=at(0), subject=Subject(name="Ada", age=30))
    second = Trial(title="Questions", created_at=at(1), description="Round 2")
    first.start("dev", at(2))
    first.stop(at(3))
    for trial in (first, second):
        await trial_repository.save(trial)

    assert await trial_repository.get(first.id) == first
    assert await trial_repository.get("missing") is None
    assert [t.id for t in await trial_repository.find()] == [second.id, first.id]
    assert [t.id for t in await trial_repository.find(search="ada")] == [first.id]
    assert [t.id for t in await trial_repository.find(search="QUEST")] == [second.id]
    assert [t.id for t in await trial_repository.find(status=TrialStatus.PAUSED)] == [first.id]

    first.complete(at(4))
    await trial_repository.save(first)
    assert (await trial_repository.get(first.id)).status is TrialStatus.COMPLETED


# --- Service -----------------------------------------------------------------------------


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def measurements():
    return InMemoryRepository()


@pytest.fixture
def service(measurements, clock):
    return TrialService(InMemoryTrialRepository(), measurements, MeasurementBus(), clock)


async def test_device_can_only_be_recorded_by_one_trial(service):
    a = await service.create("A", None, Subject())
    b = await service.create("B", None, Subject())
    await service.start_recording(a.id, "dev")
    with pytest.raises(DeviceBusyError):
        await service.start_recording(b.id, "dev")
    await service.stop_recording(a.id)
    await service.start_recording(b.id, "dev")


async def test_measurements_are_scoped_to_segments(service, measurements, clock):
    trial = await service.create("T", None, Subject())

    def hr(t):
        return Measurement.single("heart_rate", "dev", 70, at(t))

    clock.now = at(10)
    await service.start_recording(trial.id, "dev")
    clock.now = at(20)
    await service.stop_recording(trial.id)
    clock.now = at(30)
    await service.start_recording(trial.id, "dev")
    clock.now = at(40)
    await measurements.write(Stage.RAW, [hr(t) for t in (5, 15, 25, 35)])
    await measurements.write(Stage.PROCESSED, [Measurement.single("hr_stats", "dev", 1, at(16))])

    items = await service.measurements(await service.get(trial.id))
    assert [(s, m.timestamp) for s, m in items] == [
        (Stage.RAW, at(15)),
        (Stage.PROCESSED, at(16)),
        (Stage.RAW, at(35)),
    ]
    since = await service.measurements(await service.get(trial.id), since=at(16))
    assert [m.timestamp for _, m in since] == [at(16), at(35)]
