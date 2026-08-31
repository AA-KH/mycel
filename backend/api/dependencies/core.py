"""
Core dependencies for FastAPI routers.
Provides access to common services like context, logging, events, and database.
"""

from typing import Annotated, Any
from fastapi import Depends, Request
from core.context import AppContext
from core.logger import logger
from infrastructure.events.publisher import event_publisher
from infrastructure.events.base import BaseEventPublisher
from infrastructure.database.client import get_db

async def get_context(request: Request) -> AppContext:
    """Provides a fresh application context bound to the request."""
    # The middleware will have already injected the request_id context variable
    return AppContext(logger, event_publisher)

def get_event_publisher() -> BaseEventPublisher:
    """Provides the configured event publisher."""
    return event_publisher

# Type aliases for dependency injection in endpoints
ContextDep = Annotated[AppContext, Depends(get_context)]
EventPublisherDep = Annotated[BaseEventPublisher, Depends(get_event_publisher)]
DbDep = Annotated[Any, Depends(get_db)] # Any used here temporarily to avoid direct motor import coupling if possible
