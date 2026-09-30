import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, WebSocketException, status
from starlette.requests import HTTPConnection

from app.services import Services


def get_services(connection: HTTPConnection) -> Services:
    return connection.app.state.services


ServicesDep = Annotated[Services, Depends(get_services)]


def require_device_token(
    services: ServicesDep,
    token: Annotated[str | None, Query()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Accept the token as ``?token=...`` or as an ``Authorization: Bearer ...`` header."""
    provided = token if token is not None else _bearer(authorization)
    expected = services.settings.device_token.get_secret_value()
    if provided is None or not secrets.compare_digest(provided.encode(), expected.encode()):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[len("bearer ") :]
    return None


def require_operator(
    services: ServicesDep, authorization: Annotated[str | None, Header()] = None
) -> None:
    """Operator session token, as ``Authorization: Bearer ...`` (see ``POST /auth/operator``)."""
    token = _bearer(authorization)
    if token is None or not services.operator_auth.verify(token):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Operator session required",
            headers={"WWW-Authenticate": "Bearer"},
        )


OperatorDep = Depends(require_operator)
