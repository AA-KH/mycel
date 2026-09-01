"""
Mycel Monitor — Entry Point.

Starts the FastAPI server for the monitoring subsystem.

Usage:
    cd monitor
    python main.py

Or:
    cd monitor
    uvicorn main:app --host 0.0.0.0 --port 8100 --reload
"""

from __future__ import annotations

import uvicorn

from monitor.api.app import create_app
from monitor.config import load_config

config = load_config()
app = create_app(config)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
