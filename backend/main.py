"""
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from core.logger import logger
from core.rabbitmq import rabbitmq_connection
from core.mongodb import mongodb_connection
from core.middleware import RequestContextMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("Starting FastAPI application")
    try:
        await mongodb_connection.connect()
    except Exception as error:
        logger.error("Failed to initialize MongoDB", extra={"error": str(error)})

    try:
        await rabbitmq_connection.connect()
        logger.info("RabbitMQ connection established")
    except Exception as error:
        logger.error("Failed to initialize RabbitMQ", extra={"error": str(error)})

    yield

    logger.info("Shutting down FastAPI application")
    await mongodb_connection.close()
    await rabbitmq_connection.close()


app = FastAPI(
    title="Mycel",
    description="FastAPI backend with Auth0, RabbitMQ, MongoDB, and MCP server.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add Context Middleware first so it handles Request ID for all requests
app.add_middleware(RequestContextMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "https://mycel-final-git-main-kaushal-jindals-projects.vercel.app",
        "https://mycel.kaushaljindal.in"
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include new V1 routes (Health, Readiness)
app.include_router(v1_router, prefix="/api/v1")

# Mount output directory for generated files (PDF, Video, Excel, etc.)
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_dir), name="output")

# Include existing legacy modules to ensure backward compatibility
from api.v1.routes import data as api_router
app.include_router(api_router.router, prefix="/api/data", tags=["Data"])
from tasks import router as tasks_router
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
from api.memory_router import router as memory_router
app.include_router(memory_router, prefix="/api/memory", tags=["Memory"])
from api.evaluation_router import router as evaluation_router
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["Evaluation"])
from api.delivery_router import router as delivery_router
app.include_router(delivery_router, prefix="/api/delivery", tags=["Delivery"])
from api.talent_router import router as talent_router
app.include_router(talent_router, prefix="/api/talent", tags=["Talent Market"])
from api.autonomy_router import router as autonomy_router
app.include_router(autonomy_router, prefix="/api/autonomy", tags=["Autonomous Company"])
from api.wallet_router import router as wallet_router
app.include_router(wallet_router, prefix="/api/wallet", tags=["Wallet Cards"])
from api.v1.routes.auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Mount realtime WebSocket + broadcast at /api/realtime
from api.v1.routes.realtime import router as realtime_router
app.include_router(realtime_router, prefix="/api/realtime", tags=["Realtime"])


# Mount Company Builder Demo Domain
from domains.company_builder.router import router as company_builder_router
app.include_router(company_builder_router)

# Mount Real Estate Domain Demo (both v1 and legacy routes)
from domains.real_estate.api import router as real_estate_router, legacy_router as re_legacy_router, voicelink_stream_handler
app.include_router(real_estate_router)
app.include_router(re_legacy_router)
app.add_api_websocket_route("/ws/voicelink/stream", voicelink_stream_handler)

# Register Real Estate tools in the global ToolRegistry
try:
    from tools.registry.core import registry
    from domains.real_estate.tools.property_search import PropertySearchTool
    from domains.real_estate.tools.property_compare import PropertyCompareTool
    from domains.real_estate.tools.property_legal import PropertyLegalTool
    from domains.real_estate.tools.property_investment import PropertyInvestmentTool
    registry.register(PropertySearchTool())
    registry.register(PropertyCompareTool())
    registry.register(PropertyLegalTool())
    registry.register(PropertyInvestmentTool())
    logger.info("Real Estate tools registered in ToolRegistry")
except Exception as _re_err:
    logger.error(f"Failed to register Real Estate tools: {_re_err}")

@app.get("/", tags=["General"])
async def root():
    """Root endpoint providing a welcome message."""
    return {"message": "Mycel is running!"}


# Existing health check remains for legacy compatibility, but delegates to v1 concept
@app.get("/health", tags=["General"], deprecated=True)
async def health_check():
    """Legacy health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
