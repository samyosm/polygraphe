from fastapi import APIRouter

from app.api import auth, devices, health, trials

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(devices.router)
router.include_router(trials.router)

__all__ = ["router"]
