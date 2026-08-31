"""
RabbitMQ Event Publisher Implementation.
"""

from core.rabbitmq import rabbitmq_producer
from core.logger import logger
from .base import BaseEventPublisher
from .schemas import EventEnvelope


class RabbitMQEventPublisher(BaseEventPublisher):
    """
    Publishes events to RabbitMQ using the existing producer.
    """
    
    def __init__(self, producer=rabbitmq_producer):
        self.producer = producer

    async def publish(self, event: EventEnvelope) -> None:
        """
        Publishes the event. The topic is derived from the event_type.
        """
        topic = event.event_type
        # We serialize the Pydantic model to a dict using model_dump
        data = event.model_dump(mode="json")
        
        try:
            await self.producer.publish(topic, data)
            logger.debug(
                "Successfully published event", 
                extra={"event_id": event.event_id, "event_type": event.event_type}
            )
        except Exception as e:
            logger.error(
                "Failed to publish event", 
                extra={"event_id": event.event_id, "event_type": event.event_type, "error": str(e)}
            )
            raise


# Global default publisher instance for dependency injection
event_publisher = RabbitMQEventPublisher()
