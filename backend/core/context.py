"""
Application Context

Provides a context class for sharing resources and maintaining execution context.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
import contextvars

if TYPE_CHECKING:
    from .logger import AppLogger
    from .rabbitmq import RabbitMQProducer

# Global context variables for tracing
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
task_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("task_id", default="")
employee_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("employee_id", default="")


class AppContext:
    """Application context that can be used across the application."""

    def __init__(self, logger: 'AppLogger', rabbitmq_producer: 'RabbitMQProducer'):
        self.logger = logger
        self._rabbitmq_producer = rabbitmq_producer

    @property
    def request_id(self) -> str:
        return request_id_var.get()

    @property
    def task_id(self) -> str:
        return task_id_var.get()

    @property
    def employee_id(self) -> str:
        return employee_id_var.get()

    def set_execution_context(
        self,
        request_id: Optional[str] = None,
        task_id: Optional[str] = None,
        employee_id: Optional[str] = None,
    ):
        """Update context variables for the current execution flow."""
        if request_id is not None:
            request_id_var.set(request_id)
        if task_id is not None:
            task_id_var.set(task_id)
        if employee_id is not None:
            employee_id_var.set(employee_id)

    def get_context_dict(self) -> Dict[str, str]:
        """Return the current context as a dictionary (e.g. for logging)."""
        ctx = {}
        if self.request_id:
            ctx["request_id"] = self.request_id
        if self.task_id:
            ctx["task_id"] = self.task_id
        if self.employee_id:
            ctx["employee_id"] = self.employee_id
        return ctx

    async def emit(self, event: Dict[str, Any]) -> None:
        """
        Emits an event to RabbitMQ.

        Args:
            event: A dictionary containing 'topic' and 'data' keys.
        """
        topic = event.get("topic")
        data = event.get("data")

        if not topic:
            self.logger.error("Event topic is required", extra={"event": event})
            return

        try:
            await self._rabbitmq_producer.publish(topic, data)
            self.logger.debug(
                "Event emitted successfully",
                extra={"topic": topic, "data_type": type(data).__name__, **self.get_context_dict()},
            )
        except Exception as error:
            self.logger.error(
                "Failed to emit event", extra={"topic": topic, "error": str(error), **self.get_context_dict()}
            )
            raise
