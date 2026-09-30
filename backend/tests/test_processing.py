from datetime import timedelta

from app.bus import StoredMeasurements
from app.domain import Measurement, Stage, kinds
from app.domain.measurement import utc_now
from app.processing import ProcessingContext, ProcessingEngine
from app.processing.processors import HeartRateStatsProcessor, SpO2StatsProcessor


def samples(kind, values, device="dev", end=None):
    end = end or utc_now()
    return [
        Measurement.single(kind, device, v, end - timedelta(seconds=len(values) - i))
        for i, v in enumerate(values)
    ]


def test_heart_rate_stats_drop_outliers():
    [result] = HeartRateStatsProcessor().process(samples(kinds.HEART_RATE, [60, 70, 80, 500]))
    assert result.kind == kinds.HEART_RATE_STATS
    assert result.fields["mean"] == 70
    assert result.fields["count"] == 3
    assert result.fields["rejected"] == 1


def test_processors_return_nothing_without_data():
    assert HeartRateStatsProcessor().process([]) == []
    assert SpO2StatsProcessor().process([]) == []


def test_spo2_desaturation_flag():
    [ok] = SpO2StatsProcessor().process(samples(kinds.SPO2, [97, 98, 96]))
    [low] = SpO2StatsProcessor().process(samples(kinds.SPO2, [97, 88, 96]))
    assert ok.fields["desaturation"] is False
    assert low.fields["desaturation"] is True


async def test_run_fetches_window_and_stores_processed(repository):
    now = utc_now()
    old = samples(kinds.HEART_RATE, [200], end=now - timedelta(minutes=5))
    recent = samples(kinds.HEART_RATE, [70, 72, 74], end=now)
    other_device = samples(kinds.HEART_RATE, [150], device="other", end=now)
    await repository.write(Stage.RAW, old + recent + other_device)

    await HeartRateStatsProcessor().run(ProcessingContext("dev", repository, now))

    [stored] = repository.all(Stage.PROCESSED)
    assert stored.fields["mean"] == 72
    assert stored.device_id == "dev"


async def test_engine_only_runs_for_devices_with_new_data(repository):
    now = utc_now()
    await repository.write(Stage.RAW, samples(kinds.HEART_RATE, [70], end=now))
    processor = HeartRateStatsProcessor()
    engine = ProcessingEngine(repository, [processor], clock=lambda: now)

    await engine.run_pending(processor)
    assert repository.all(Stage.PROCESSED) == []

    # Irrelevant kind.
    engine.on_measurements(StoredMeasurements(Stage.RAW, samples(kinds.SPO2, [98])))
    await engine.run_pending(processor)
    assert repository.all(Stage.PROCESSED) == []

    engine.on_measurements(StoredMeasurements(Stage.PROCESSED, samples(kinds.HEART_RATE, [70])))
    await engine.run_pending(processor)
    assert repository.all(Stage.PROCESSED) == []

    engine.on_measurements(StoredMeasurements(Stage.RAW, samples(kinds.HEART_RATE, [70])))
    await engine.run_pending(processor)
    assert len(repository.all(Stage.PROCESSED)) == 1
