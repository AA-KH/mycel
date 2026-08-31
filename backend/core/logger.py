"""
Logger for the application.

This module configures a Loguru logger for structured, colorized logging,
and automatically injects execution context (request_id, etc.).
"""

import sys
from typing import Any, Dict

from loguru import logger as loguru_logger

from core.config import settings
from core.context import request_id_var, task_id_var, employee_id_var


def _context_filter(record: Dict[str, Any]) -> bool:
    """Injects current context variables into the log record."""
    request_id = request_id_var.get()
    task_id = task_id_var.get()
    employee_id = employee_id_var.get()

    if request_id:
        record["extra"]["request_id"] = request_id
    if task_id:
        record["extra"]["task_id"] = task_id
    if employee_id:
        record["extra"]["employee_id"] = employee_id
        
    return True


class AppLogger:
    """A logger that provides a consistent interface for logging."""

    def __init__(self, name: str = "app"):
        loguru_logger.remove()
        
        is_production = settings.app_env.lower() == "production"
        
        loguru_logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | {extra}",
            level="DEBUG" if settings.debug else "INFO",
            colorize=not is_production,
            serialize=is_production,  # JSON output in production
            filter=_context_filter
        )
        self.logger = loguru_logger.bind()

    def info(self, message: str, extra: Dict[str, Any] | None = None) -> None:
        """Logs an info-level message."""
        self._log("info", message, extra)

    def error(self, message: str, extra: Dict[str, Any] | None = None) -> None:
        """Logs an error-level message."""
        self._log("error", message, extra)

    def warning(self, message: str, extra: Dict[str, Any] | None = None) -> None:
        """Logs a warning-level message."""
        self._log("warning", message, extra)

    def debug(self, message: str, extra: Dict[str, Any] | None = None) -> None:
        """Logs a debug-level message."""
        self._log("debug", message, extra)
        
    def exception(self, message: str, extra: Dict[str, Any] | None = None) -> None:
        """Logs an exception-level message with stack trace."""
        self._log("exception", message, extra)

    def _log(self, level: str, message: str, extra: Dict[str, Any] | None) -> None:
        """Helper method to perform logging."""
        logger_method = getattr(self.logger, level)
        if extra:
            logger_method(message, **extra)
        else:
            logger_method(message)


# Global logger instance
logger = AppLogger()
