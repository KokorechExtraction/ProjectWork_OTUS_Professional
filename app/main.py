from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.api.v1 import admin, auth, chats, files, messages, posts, users, websocket
from app.core.config import settings
from app.core.log_config import logger, setup_logging
from app.core.redis import redis_runtime
from app.db.session import AsyncSessionLocal
from app.repositories.user import UserRepository
from app.services.admin import ensure_admin_user
from app.websocket.manager import manager


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await redis_runtime.connect()
    await manager.start()
    async with AsyncSessionLocal() as session:
        await ensure_admin_user(UserRepository(session))
    logger.info("application_start", app_name=settings.app_name, env=settings.app_env)
    yield
    await manager.stop()
    await redis_runtime.disconnect()
    logger.info("application_stop", app_name=settings.app_name)


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _duration_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    start = perf_counter()
    clear_contextvars()
    bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = _duration_ms(start)
        logger.exception("http_request_failed", duration_ms=duration_ms)
        clear_contextvars()
        raise

    duration_ms = _duration_ms(start)
    logger.info(
        "http_request",
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    clear_contextvars()
    return response


@app.get("/")
async def index(request: Request) -> Response:
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(chats.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
