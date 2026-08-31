"""
Structured logging with Loguru.

All major actions are traceable with reason codes:
REJECTED, ENTITY_MATCH, GEO_MATCH, DUPLICATE, STATE_TRANSITION,
LLM_ANALYSIS, ALERT_CREATED, etc.
"""

from __future__ import annotations

import sys

from loguru import logger


def configure_logging(debug: bool = False) -> None:
    """Configure structured logging for the monitor."""
    # Remove default handler
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    level = "DEBUG" if debug else "INFO"

    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True,
    )

    # File handler
    logger.add(
        "monitor.log",
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="3 days",
        compression="gz",
    )

    logger.info(f"Monitor logging configured (level={level})")
