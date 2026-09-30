from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConnectedDevice:
    id: str
    source: str


class DeviceRegistry:
    """Keeps track of the devices currently streaming data."""

    def __init__(self) -> None:
        self._connections: Counter[ConnectedDevice] = Counter()

    @contextmanager
    def connected(self, device: ConnectedDevice) -> Iterator[None]:
        self._connections[device] += 1
        try:
            yield
        finally:
            self._connections[device] -= 1
            if self._connections[device] <= 0:
                del self._connections[device]

    def all(self) -> list[ConnectedDevice]:
        return sorted(self._connections, key=lambda d: d.id)
