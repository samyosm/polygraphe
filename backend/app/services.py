"""Composition root: the only place that knows which concrete classes are used."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta

from app.auth import OperatorAuth
from app.bus import MeasurementBus
from app.config import Settings
from app.ingestion import DataSource, DeviceRegistry, IngestionService
from app.ingestion.dummy import DummySource, default_generators
from app.processing import ProcessingEngine, default_processors
from app.storage import (
    MeasurementRepository,
    TrialRepository,
    build_measurement_repository,
    build_trial_repository,
)
from app.storage.measurements import PublishingRepository
from app.trials import TrialService

logger = logging.getLogger(__name__)


@dataclass
class Services:
    settings: Settings
    bus: MeasurementBus
    measurements: MeasurementRepository
    trial_repository: TrialRepository
    devices: DeviceRegistry
    ingestion: IngestionService
    engine: ProcessingEngine
    trials: TrialService
    operator_auth: OperatorAuth
    _background: list[asyncio.Task] = field(default_factory=list)

    @classmethod
    def build(cls, settings: Settings) -> "Services":
        bus = MeasurementBus()
        measurements = PublishingRepository(build_measurement_repository(settings), bus)
        trial_repository = build_trial_repository(settings)
        devices = DeviceRegistry()
        engine = ProcessingEngine(measurements, default_processors())
        bus.subscribe(engine.on_measurements)
        return cls(
            settings=settings,
            bus=bus,
            measurements=measurements,
            trial_repository=trial_repository,
            devices=devices,
            ingestion=IngestionService(measurements, devices),
            engine=engine,
            trials=TrialService(trial_repository, measurements, bus),
            operator_auth=OperatorAuth(
                password=settings.operator_password.get_secret_value(),
                secret_key=settings.secret_key.get_secret_value(),
                lifetime=timedelta(hours=settings.operator_session_hours),
            ),
        )

    def background_sources(self) -> list[DataSource]:
        """Sources that run for the whole app lifetime (as opposed to websocket connections)."""
        sources: list[DataSource] = []
        if self.settings.dummy_enabled:
            sources.append(DummySource(self.settings.dummy_device_id, default_generators()))
        return sources

    async def start(self) -> None:
        await self.measurements.start()
        await self.trial_repository.start()
        await self.trials.start()
        await self.engine.start()
        for source in self.background_sources():
            logger.info("Starting background source %r", source)
            self._background.append(asyncio.create_task(self.ingestion.consume(source)))

    async def stop(self) -> None:
        for task in self._background:
            task.cancel()
        await asyncio.gather(*self._background, return_exceptions=True)
        self._background.clear()
        await self.engine.stop()
        await self.trial_repository.close()
        await self.measurements.close()
