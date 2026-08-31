import asyncio
from typing import Callable, Any
from .errors import ExecutionTimeoutError, ExecutionCancelledError
from core.logger import logger

class Executor:
    """
    Handles common execution concerns like bounded loops, timeouts, and cancellation.
    """
    
    @staticmethod
    async def with_timeout(coro: Callable, timeout_seconds: int, error_message: str = "Execution timed out") -> Any:
        try:
            return await asyncio.wait_for(coro(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise ExecutionTimeoutError(error_message)
        except asyncio.CancelledError:
            raise ExecutionCancelledError("Execution was cancelled cooperatively")

    @staticmethod
    async def with_retries(coro: Callable, max_retries: int = 3, retryable_exceptions: tuple = (Exception,)) -> Any:
        attempts = 0
        while attempts < max_retries:
            try:
                return await coro()
            except retryable_exceptions as e:
                attempts += 1
                if attempts >= max_retries:
                    raise e
                logger.warning(f"Retryable failure (attempt {attempts}/{max_retries}): {e}")
                await asyncio.sleep(2 ** attempts) # Exponential backoff
