"""
Health and Readiness endpoints for Mycel.
"""

from fastapi import APIRouter
from core.mongodb import mongodb_connection
from core.rabbitmq import rabbitmq_connection

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Basic liveness probe. 
    Indicates if the application container is running.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe.
    Verifies that critical backing services are connected.
    """
    status = {
        "status": "ok",
        "services": {
            "mongodb": "disconnected",
            "rabbitmq": "disconnected"
        }
    }
    
    is_ready = True
    
    # Check MongoDB
    try:
        if mongodb_connection.client:
            await mongodb_connection.client.admin.command('ping')
            status["services"]["mongodb"] = "connected"
        else:
            is_ready = False
    except Exception:
        is_ready = False

    # Check RabbitMQ
    try:
        if rabbitmq_connection.connection and not rabbitmq_connection.connection.is_closed:
            status["services"]["rabbitmq"] = "connected"
        else:
            is_ready = False
    except Exception:
        is_ready = False
        
    if not is_ready:
        status["status"] = "error"
        # Often readiness probes return 503 if not ready, but returning JSON is safer during transition
        
    return status
