"""
Event System Base Abstractions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from .schemas import EventEnvelope


class BaseEventPublisher(ABC):
    """
    Abstract base class for publishing events to a message broker.
    """
    
    @abstractmethod
    async def publish(self, event: EventEnvelope) -> None:
        """
        Publishes a standard event envelope to the message broker.
        """
        pass
