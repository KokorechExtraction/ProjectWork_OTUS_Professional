import logging
import os
import sys

from logging.handlers import RotatingFileHandler
from typing import cast

import structlog

from app.core.config import settings


def _resolve_log_level(level: str) -> int:
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    return level_map.get(level.lower(), logging.INFO)


def setup_logging() -> None:
    log_level = _resolve_log_level(settings.log_level)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    handler: logging.Handler
    if settings.log_path:
        os.makedirs(settings.log_path, exist_ok=True)
        handler = RotatingFileHandler(
            filename=os.path.join(settings.log_path, "app.log.json"),
            maxBytes=10_000_000,
            backupCount=3,
            encoding="utf-8",
        )
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


logger = get_logger()
