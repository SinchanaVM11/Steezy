import sqlite3

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import router as health_router
from app.api.feedback import router as feedback_router
from app.api.assets import router as assets_router
from app.api.analysis import router as analysis_router
from app.api.retrieval import router as retrieval_router
from app.api.inspiration import router as inspiration_router
from app.api.wardrobe import router as wardrobe_router
from app.core.errors import ApiError
from app.core.observability import correlation_id, valid_correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.correlation_id = valid_correlation_id(
            request.headers.get("X-Request-ID")
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id(request)
        return response


def create_app() -> FastAPI:
    application = FastAPI(
        title="Steezy API",
        version="0.1.0",
        description="Foundation API for the Steezy fashion intelligence system.",
    )
    application.include_router(health_router)
    application.include_router(wardrobe_router)
    application.include_router(feedback_router)
    application.include_router(assets_router)
    application.include_router(analysis_router)
    application.include_router(retrieval_router)
    application.include_router(inspiration_router)
    application.add_middleware(CorrelationMiddleware)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "correlation_id": correlation_id(request),
                    "details": error.errors(),
                }
            },
        )

    @application.exception_handler(ApiError)
    async def api_error_handler(request: Request, error: ApiError):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "correlation_id": correlation_id(request),
                    "details": error.details,
                }
            },
        )

    @application.exception_handler(sqlite3.Error)
    async def persistence_error_handler(request: Request, error: sqlite3.Error):
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "persistence_error",
                    "message": "Persistence operation failed.",
                    "correlation_id": correlation_id(request),
                    "details": None,
                }
            },
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, error: StarletteHTTPException):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(error.detail),
                    "correlation_id": correlation_id(request),
                    "details": None,
                }
            },
        )

    return application


app = create_app()
