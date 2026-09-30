from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import OperatorDep, ServicesDep
from app.api.schemas import OperatorSessionOut, OperatorSignIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/operator")
async def sign_in(body: OperatorSignIn, services: ServicesDep) -> OperatorSessionOut:
    """Exchange the operator password for a session token."""
    session = services.operator_auth.sign_in(body.password)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    return OperatorSessionOut(token=session.token, expires_at=session.expires_at)


@router.get("/operator", status_code=status.HTTP_204_NO_CONTENT, dependencies=[OperatorDep])
async def check_session() -> Response:
    """204 if the bearer token is a valid operator session, 401 otherwise."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
