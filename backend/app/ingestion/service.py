import logging

from app.domain import Measurement, Stage
from app.ingestion.base import DataSource
from app.ingestion.devices import ConnectedDevice, DeviceRegistry
from app.storage import MeasurementRepository

logger = logging.getLogger(__name__)


class IngestionService:
    """Single entry point for incoming data: every measurement is stored raw, as received.

    Whoever needs to react to new data subscribes to the
    :class:`~app.bus.MeasurementBus` the repository publishes to.
    """

    def __init__(self, repository: MeasurementRepository, devices: DeviceRegistry) -> None:
        self._repository = repository
        self._devices = devices

    async def ingest(self, measurement: Measurement) -> None:
        await self._repository.write(Stage.RAW, [measurement])

    async def consume(self, source: DataSource) -> None:
        """Ingest everything a source yields. A failed write is logged, not fatal."""
        with self._devices.connected(ConnectedDevice(source.device_id, source.source_name)):
            async for measurement in source.stream():
                try:
                    await self.ingest(measurement)
                except Exception:
                    logger.exception("Failed to store %s from %r", measurement.kind, source)
