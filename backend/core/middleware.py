import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.context import request_id_var
from core.errors import AppException
from core.logger import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that establishes execution context (e.g. correlation IDs)
    for every incoming API request and handles global application errors.
    """

    async def dispatch(self, request: Request, call_next):
        # WebSocket upgrade requests must bypass BaseHTTPMiddleware —
        # call_next() cannot handle WebSocket protocol upgrades.
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        # Generate or preserve correlation ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Set the context var for this asynchronous execution flow
        token = request_id_var.set(request_id)
        
        try:
            # Execute the request
            response = await call_next(request)
            # Ensure the response has the request ID
            response.headers["X-Request-ID"] = request_id
            return response
            
        except AppException as e:
            # Handle standardized application exceptions
            logger.warning(
                f"Application Exception: {e.message}",
                extra={"error_code": e.code, "request_id": request_id, "details": e.details}
            )
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_dict(request_id=request_id)
            )
            
        except Exception as e:
            # Handle unhandled/unexpected exceptions
            logger.exception(
                f"Unhandled Exception: {str(e)}",
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                        "details": {}
                    },
                    "request_id": request_id
                }
            )
            
        finally:
            # Reset the context var to prevent leakage in shared threads
            request_id_var.reset(token)
