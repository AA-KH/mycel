"""
FastAPI Dependencies

This module provides dependency injection for the application.
"""

from typing import Annotated

from fastapi import Depends

from .context import AppContext
from .logger import logger
from .rabbitmq import rabbitmq_producer


async def get_context() -> AppContext:
    """Provides an application context as a dependency."""
    return AppContext(logger, rabbitmq_producer)


# Type alias for the application context dependency
ContextDep = Annotated[AppContext, Depends(get_context)]
