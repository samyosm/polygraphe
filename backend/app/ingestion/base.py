from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import ClassVar

from app.domain import Measurement


class DataSource(ABC):
    """Something that produces measurements for one device: a real device, a simulator...

    Sources only produce data. Storing and processing it is the job of
    :class:`~app.ingestion.service.IngestionService`, so every source is handled the same way.
    """

    source_name: ClassVar[str]
    """Short name of the kind of source, stored as the ``source`` tag."""

    @property
    @abstractmethod
    def device_id(self) -> str: ...

    @abstractmethod
    def stream(self) -> AsyncIterator[Measurement]:
        """Yield measurements until the source is exhausted or disconnected."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(device_id={self.device_id!r})"
