import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from requests import RequestException
from sqlalchemy.exc import SQLAlchemyError

from src.config import settings

from .routers import health, auth as auth_router, api_jobs as api_jobs_router
from .routers import tc_projects as tc_projects_router
from .routers import jr_projects as jr_projects_router
from .routers import sync_status as sync_status_router
from .routers import sync_triggers as sync_triggers_router


log = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings.require_api_ready()
    if "*" in settings.api.cors_origins and settings.api.host not in {"127.0.0.1", "localhost"}:
        log.warning(
            "CORS is wide open (*) on a non-local host (%s). "
            "Set APP__API__CORS_ORIGINS for production.",
            settings.api.host,
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sync Work Calendar API",
        description=(
            "REST API навколо TimeCamp → Jira/Tempo синку. "
            "Single-user JWT auth (multi-user-ready схема), журнал `api_jobs` "
            "із кроком `needs_verification`."
        ),
        version="0.1.0",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(SQLAlchemyError)
    async def _sqlalchemy_handler(request: Request, exc: SQLAlchemyError):
        log.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "database error"})

    @app.exception_handler(RequestException)
    async def _requests_handler(request: Request, exc: RequestException):
        log.exception("Upstream HTTP error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=502, content={"detail": "upstream service error"})

    app.include_router(health.router)
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(api_jobs_router.router, prefix="/api-jobs", tags=["api-jobs"])
    app.include_router(tc_projects_router.router, prefix="/tc-projects", tags=["tc-projects"])
    app.include_router(jr_projects_router.router, prefix="/jr-projects", tags=["jr-projects"])
    app.include_router(sync_status_router.router, tags=["sync-status"])
    app.include_router(sync_triggers_router.router, prefix="/sync", tags=["sync-triggers"])

    return app


app = create_app()
