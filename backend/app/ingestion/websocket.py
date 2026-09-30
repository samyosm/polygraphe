import logging
from collections.abc import AsyncIterator

from fastapi import WebSocket, WebSocketDisconnect

from app.domain import Measurement
from app.ingestion.base import DataSource
from app.ingestion.protocol import ProtocolError, parse_frame

logger = logging.getLogger(__name__)


class WebSocketSource(DataSource):
    """Measurements sent by a physical device over an (already accepted) websocket.

    Malformed frames are reported back to the device and skipped; they never end the stream.
    """

    source_name = "websocket"

    def __init__(self, websocket: WebSocket, device_id: str) -> None:
        self._websocket = websocket
        self._device_id = device_id

    @property
    def device_id(self) -> str:
        return self._device_id

    async def stream(self) -> AsyncIterator[Measurement]:
        while True:
            try:
                frame = await self._websocket.receive_text()
            except WebSocketDisconnect:
                logger.info("Device %s disconnected", self._device_id)
                return
            try:
                measurements = parse_frame(frame, self._device_id, {"source": self.source_name})
            except ProtocolError as exc:
                logger.warning("Invalid frame from %s: %s", self._device_id, exc)
                await self._websocket.send_json({"status": "error", "detail": str(exc)})
                continue
            for measurement in measurements:
                yield measurement
