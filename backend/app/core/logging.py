from __future__ import annotations

from typing import Any

from app.core.config import settings

try:
    import structlog

    _configured = True
except Exception:  # pragma: no cover
    _configured = False


def configure_logging() -> None:
    if not _configured:
        return
    import logging

    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


def get_logger(name: str) -> Any:
    if _configured:
        return structlog.get_logger(name)
    import logging

    return logging.getLogger(name)
