from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain import TrialStateError
from app.trials import DeviceBusyError, TrialNotFoundError

# Domain exceptions -> HTTP status. Routes just let them propagate.
_STATUS_BY_ERROR: dict[type[Exception], int] = {
    TrialNotFoundError: status.HTTP_404_NOT_FOUND,
    TrialStateError: status.HTTP_409_CONFLICT,
    DeviceBusyError: status.HTTP_409_CONFLICT,
}


def install_error_handlers(app: FastAPI) -> None:
    for error, code in _STATUS_BY_ERROR.items():

        async def handler(_: Request, exc: Exception, code: int = code) -> JSONResponse:
            return JSONResponse(status_code=code, content={"detail": str(exc)})

        app.add_exception_handler(error, handler)
