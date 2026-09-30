from app.config import Settings, StorageBackend
from app.domain import Stage
from app.storage.measurements import InfluxRepository, InMemoryRepository, MeasurementRepository
from app.storage.trials import InMemoryTrialRepository, SqlTrialRepository, TrialRepository


def build_measurement_repository(settings: Settings) -> MeasurementRepository:
    match settings.storage_backend:
        case StorageBackend.MEMORY:
            return InMemoryRepository()
        case StorageBackend.DATABASE:
            return InfluxRepository(
                url=settings.influx_url,
                token=settings.influx_token.get_secret_value(),
                org=settings.influx_org,
                buckets={
                    Stage.RAW: settings.influx_raw_bucket,
                    Stage.PROCESSED: settings.influx_processed_bucket,
                },
            )


def build_trial_repository(settings: Settings) -> TrialRepository:
    match settings.storage_backend:
        case StorageBackend.MEMORY:
            return InMemoryTrialRepository()
        case StorageBackend.DATABASE:
            return SqlTrialRepository(settings.database_url)
