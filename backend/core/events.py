import time
import uuid
from typing import Any, Dict
from core.mongodb import mongodb_connection
from core.rabbitmq import rabbitmq_producer
from core.logger import logger

class EventPublisher:
    """
    Central event publisher for project-related events.
    Persists events to MongoDB and broadcasts them via RabbitMQ for realtime WebSockets.
    """
    
    @staticmethod
    async def publish(project_id: str, kind: str, data: Dict[str, Any]):
        """
        Publishes a standard EventEnvelope.
        `kind` maps to the frontend TimelineEvent kinds: 'log', 'hire', 'start', 'finish', 'complete'
        """
        event_doc = {
            "event_id": str(uuid.uuid4()),
            "project_id": project_id,
            "kind": kind,
            "at": int(time.time() * 1000),  # absolute timestamp in ms
            "data": data
        }
        
        try:
            db = mongodb_connection.db
            await db.project_events.insert_one(event_doc.copy())
            
            # Broadcast to WebSocket via a specific RabbitMQ topic
            await rabbitmq_producer.publish("realtime.project_event", event_doc)
            
            # Broadcast directly to WebSocket manager (fixes missing consumer)
            from api.v1.routes.realtime.router import manager
            await manager.broadcast(project_id, event_doc)
            
        except Exception as e:
            logger.error(f"Failed to publish event for project {project_id}: {str(e)}")

event_publisher = EventPublisher()
