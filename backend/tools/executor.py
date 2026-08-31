import asyncio
from datetime import datetime, timezone
import time
from typing import Dict, Any

from .base import BaseTool
from .context import ToolExecutionContext
from .models import ToolError, ToolExecutionError, ToolTimeoutError
from agents.runtime.result import ToolResult
from core.logger import logger

class ToolExecutor:
    """
    Handles the execution lifecycle of a single tool.
    Enforces timeouts, boundaries, and normalizes errors.
    """
    
    @staticmethod
    async def execute(tool: BaseTool, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        definition = tool.definition
        start_time = time.time()
        
        # Enforce max retries from definition
        max_attempts = max(1, definition.max_retries + 1)
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Executing tool {definition.id} for {context.execution_id} (Attempt {attempt+1})")
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    tool.execute(arguments, context),
                    timeout=definition.timeout_seconds
                )
                
                # Record metrics
                result.duration_ms = int((time.time() - start_time) * 1000)
                
                # Emit event (mocked here, should use RuntimeEventPublisher)
                logger.info(f"Tool {definition.id} completed in {result.duration_ms}ms")
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Tool {definition.id} timed out after {definition.timeout_seconds}s"
                logger.warning(last_error)
                if not definition.idempotent:
                    break # Do not retry non-idempotent tools on timeout
            except ToolError as e:
                # Custom tool errors (like validation or permission) shouldn't be retried
                last_error = str(e)
                logger.warning(f"Tool {definition.id} failed: {last_error}")
                break 
            except Exception as e:
                # Unexpected exceptions might be transient
                last_error = f"Tool {definition.id} encountered unexpected error: {str(e)}"
                logger.error(last_error)
                if not definition.idempotent:
                    break
                    
        # If we exhausted attempts or broke out early
        duration = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_name=definition.id,
            status="error",
            output={},
            error=last_error,
            duration_ms=duration
        )
