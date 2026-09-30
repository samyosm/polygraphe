"""In-process publish/subscribe."""

import asyncio
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Broadcaster[T]:
    """Fans out every published event to subscribers.

    Listeners run synchronously inside :meth:`publish` and must return quickly. Async
    consumers (e.g. websockets) should use :meth:`queue` instead.
    """

    def __init__(self) -> None:
        self._listeners: list[Callable[[T], None]] = []

    @property
    def subscriber_count(self) -> int:
        return len(self._listeners)

    def subscribe(self, listener: Callable[[T], None]) -> Callable[[], None]:
        """Register ``listener``; returns a function that unregisters it."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def publish(self, event: T) -> None:
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception:
                logger.exception("Listener %r failed", listener)

    @contextmanager
    def queue(self, maxsize: int = 10_000) -> Iterator[asyncio.Queue[T]]:
        """Buffer published events in a queue for as long as the context is open.

        When the consumer is too slow and the queue is full, new events are dropped.
        """
        queue: asyncio.Queue[T] = asyncio.Queue(maxsize)

        def enqueue(event: T) -> None:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Queue full, dropping %r", type(event).__name__)

        unsubscribe = self.subscribe(enqueue)
        try:
            yield queue
        finally:
            unsubscribe()
