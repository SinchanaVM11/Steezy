from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.wardrobe import router as wardrobe_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Steezy API",
        version="0.1.0",
        description="Foundation API for the Steezy fashion intelligence system.",
    )
    application.include_router(health_router)
    application.include_router(wardrobe_router)
    return application


app = create_app()
