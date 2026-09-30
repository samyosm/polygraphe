import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.api.errors import install_error_handlers
from app.config import Settings, get_settings
from app.services import Services


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        services = Services.build(settings)
        await services.start()
        app.state.services = services
        try:
            yield
        finally:
            await services.stop()

    app = FastAPI(
        title="PolyGraphe processing server", root_path=settings.root_path, lifespan=lifespan
    )
    app.include_router(router)
    install_error_handlers(app)
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()
