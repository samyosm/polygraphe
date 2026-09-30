import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Path, WebSocket

from app.api.deps import ServicesDep, require_device_token
from app.api.schemas import DeviceOut
from app.ingestion.websocket import WebSocketSource

logger = logging.getLogger(__name__)

router = APIRouter(tags=["devices"])

DeviceId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


@router.websocket("/ws/devices/{device_id}", dependencies=[Depends(require_device_token)])
async def device_stream(websocket: WebSocket, device_id: DeviceId, services: ServicesDep) -> None:
    await websocket.accept()
    logger.info("Device %s connected", device_id)
    await services.ingestion.consume(WebSocketSource(websocket, device_id))


@router.get("/devices")
async def list_devices(services: ServicesDep) -> list[DeviceOut]:
    """Devices currently sending data."""
    return [DeviceOut.from_domain(d) for d in services.devices.all()]
