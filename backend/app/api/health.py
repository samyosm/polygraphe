from fastapi import APIRouter

from app.api.deps import ServicesDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(services: ServicesDep) -> dict:
    return {
        "status": "ok",
        "storage": services.settings.storage_backend,
        "processors": [p.name for p in services.engine.processors],
    }
