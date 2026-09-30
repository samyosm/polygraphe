from collections.abc import AsyncIterator
from contextlib import aclosing
from datetime import datetime
from typing import Annotated

import anyio
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.deps import OperatorDep, ServicesDep
from app.api.schemas import MeasurementOut, StartRecording, TrialDetails, TrialOut
from app.domain import TrialStatus
from app.trials import TrialNotFoundError

router = APIRouter(prefix="/trials", tags=["trials"])


@router.get("")
async def list_trials(
    services: ServicesDep,
    q: Annotated[str | None, Query(max_length=200)] = None,
    status_filter: Annotated[TrialStatus | None, Query(alias="status")] = None,
) -> list[TrialOut]:
    return [TrialOut.from_domain(t) for t in await services.trials.find(q, status_filter)]


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[OperatorDep])
async def create_trial(body: TrialDetails, services: ServicesDep) -> TrialOut:
    trial = await services.trials.create(body.title, body.description, body.subject.to_domain())
    return TrialOut.from_domain(trial)


@router.get("/{trial_id}")
async def get_trial(trial_id: str, services: ServicesDep) -> TrialOut:
    return TrialOut.from_domain(await services.trials.get(trial_id))


@router.put("/{trial_id}", dependencies=[OperatorDep])
async def update_trial(trial_id: str, body: TrialDetails, services: ServicesDep) -> TrialOut:
    """Replace the trial's descriptive information (title, description, subject)."""
    trial = await services.trials.update_details(
        trial_id, body.title, body.description, body.subject.to_domain()
    )
    return TrialOut.from_domain(trial)


@router.post("/{trial_id}/start", dependencies=[OperatorDep])
async def start_recording(trial_id: str, body: StartRecording, services: ServicesDep) -> TrialOut:
    return TrialOut.from_domain(await services.trials.start_recording(trial_id, body.device_id))


@router.post("/{trial_id}/stop", dependencies=[OperatorDep])
async def stop_recording(trial_id: str, services: ServicesDep) -> TrialOut:
    return TrialOut.from_domain(await services.trials.stop_recording(trial_id))


@router.post("/{trial_id}/complete", dependencies=[OperatorDep])
async def complete_trial(trial_id: str, services: ServicesDep) -> TrialOut:
    return TrialOut.from_domain(await services.trials.complete(trial_id))


@router.get("/{trial_id}/measurements")
async def trial_measurements(
    trial_id: str, services: ServicesDep, since: datetime | None = None
) -> list[MeasurementOut]:
    trial = await services.trials.get(trial_id)
    items = await services.trials.measurements(trial, since)
    return [MeasurementOut.from_domain(stage, m) for stage, m in items]


@router.websocket("/events")
async def trial_events(websocket: WebSocket, services: ServicesDep) -> None:
    """Streams every trial (:class:`TrialOut`) each time it changes, for live interfaces."""
    await websocket.accept()

    async def messages() -> AsyncIterator[dict]:
        async for trial in services.trials.changes():
            yield TrialOut.from_domain(trial).model_dump(mode="json")

    await _send_until_disconnect(websocket, messages())


@router.websocket("/{trial_id}/live")
async def live(
    websocket: WebSocket, trial_id: str, services: ServicesDep, since: datetime | None = None
) -> None:
    """Streams :class:`MeasurementOut` messages: backfill from ``since``, then live data."""
    try:
        await services.trials.get(trial_id)
    except TrialNotFoundError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unknown trial")
        return
    await websocket.accept()

    async def messages() -> AsyncIterator[dict]:
        async for stage, measurement in services.trials.live(trial_id, since):
            yield MeasurementOut.from_domain(stage, measurement).model_dump(mode="json")

    await _send_until_disconnect(websocket, messages())


async def _send_until_disconnect(websocket: WebSocket, messages: AsyncIterator[dict]) -> None:
    """Forward ``messages``, stopping as soon as the client leaves.

    Without the receiving side, a disconnect would go unnoticed until the next send,
    which may never come if no data is flowing. anyio (what Starlette runs on) is used
    rather than raw asyncio tasks so cancellation composes with the server's own.
    """
    async with anyio.create_task_group() as tasks:

        async def send() -> None:
            # aclosing: the feed's bus subscription must end with the connection.
            async with aclosing(messages) as feed:
                try:
                    async for message in feed:
                        await websocket.send_json(message)
                except WebSocketDisconnect:
                    pass
            tasks.cancel_scope.cancel()

        async def wait_for_disconnect() -> None:
            while (await websocket.receive())["type"] != "websocket.disconnect":
                pass
            tasks.cancel_scope.cancel()

        tasks.start_soon(send)
        tasks.start_soon(wait_for_disconnect)
