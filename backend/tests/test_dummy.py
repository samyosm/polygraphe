from app.bus import MeasurementBus
from app.domain import Stage, kinds
from app.ingestion import DeviceRegistry, IngestionService
from app.ingestion.dummy import DummySource, HeartRateGenerator, SpO2Generator
from app.storage.measurements import PublishingRepository


async def take(source, n):
    out = []
    async for m in source.stream():
        out.append(m)
        if len(out) == n:
            return out


async def test_generators_respect_their_rates():
    source = DummySource(
        "dummy",
        [HeartRateGenerator(rate_hz=2, seed=0), SpO2Generator(rate_hz=1, seed=0)],
        speed=1000,
    )
    measurements = await take(source, 30)
    counts = {k: sum(m.kind == k for m in measurements) for k in (kinds.HEART_RATE, kinds.SPO2)}
    assert counts[kinds.HEART_RATE] == 2 * counts[kinds.SPO2]
    assert all(m.value <= 100 for m in measurements if m.kind == kinds.SPO2)
    assert all(40 < m.value < 110 for m in measurements if m.kind == kinds.HEART_RATE)
    timestamps = [m.timestamp for m in measurements]
    assert timestamps == sorted(timestamps)


async def test_ingestion_stores_raw_then_publishes(repository):
    bus, seen = MeasurementBus(), []

    def listener(stored):
        # Raw data must already be stored when subscribers are notified.
        assert all(m in repository.all(Stage.RAW) for m in stored.measurements)
        seen.extend(stored.measurements)

    bus.subscribe(listener)
    ingestion = IngestionService(PublishingRepository(repository, bus), DeviceRegistry())
    for m in await take(DummySource("dummy", [HeartRateGenerator()], speed=1000), 5):
        await ingestion.ingest(m)
    assert len(seen) == 5


async def test_consume_registers_device_while_streaming(repository):
    devices = DeviceRegistry()
    ingestion = IngestionService(repository, devices)

    class OneShot(DummySource):
        async def stream(self):
            assert [d.id for d in devices.all()] == ["dummy"]
            yield await anext(super().stream())

    await ingestion.consume(OneShot("dummy", [HeartRateGenerator()]))
    assert devices.all() == []
