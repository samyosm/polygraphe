from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from datetime import datetime

from app.domain import Measurement, Stage


class MeasurementRepository(ABC):
    """Persistence port for measurements. Everything else depends on this, never on a DB."""

    async def start(self) -> None:  # noqa: B027 - optional hook
        """Open connections / prepare the storage. Called once at startup."""

    async def close(self) -> None:  # noqa: B027 - optional hook
        """Release resources. Called once at shutdown."""

    @abstractmethod
    async def write(self, stage: Stage, measurements: Sequence[Measurement]) -> None: ...

    @abstractmethod
    async def query(
        self,
        stage: Stage,
        device_id: str,
        kinds: Collection[str] | None,
        start: datetime,
        stop: datetime,
    ) -> list[Measurement]:
        """Return measurements with ``start <= timestamp < stop``, oldest first.

        ``kinds=None`` means every kind.
        """
