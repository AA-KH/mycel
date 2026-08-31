"""
FastAPI application factory.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from ..config import MonitorConfig, load_config
from ..observability.log import configure_logging
from ..scheduling.orchestrator import Orchestrator
from .routes import router, set_orchestrator


def create_app(config: MonitorConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = load_config()

    configure_logging(debug=config.debug)

    # Create orchestrator
    orchestrator = Orchestrator(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifecycle."""
        orchestrator.initialize()
        set_orchestrator(orchestrator)
        logger.info(f"Mycel Monitor started on {config.host}:{config.port}")
        yield
        await orchestrator.shutdown()
        logger.info("Mycel Monitor stopped")

    app = FastAPI(
        title="Mycel Monitor",
        description="Real-time supply-network monitoring subsystem",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(router)

    # Store orchestrator reference on the app for access
    app.state.orchestrator = orchestrator

    return app
