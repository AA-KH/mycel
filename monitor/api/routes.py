"""
FastAPI REST API for the Mycel monitoring subsystem.

Endpoints:
- GET  /api/monitor/health    — System health
- GET  /api/monitor/status    — Monitor health + network condition (dual response)
- GET  /api/monitor/alerts    — Alert history with filtering
- GET  /api/monitor/alerts/latest — Most recent alert
- GET  /api/monitor/situations — Active situations
- POST /api/monitor/profile   — Load network architecture, compile profile
- POST /api/monitor/events/replay — Inject test events through full pipeline
- GET  /api/monitor/metrics   — Pipeline metrics
- GET  /api/monitor/entities  — Monitored entities with current state
- GET  /api/monitor/sources   — Source connector health
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from ..scheduling.orchestrator import Orchestrator

router = APIRouter(prefix="/api/monitor", tags=["monitor"])

# Module-level orchestrator reference (set by app factory)
_orchestrator: Optional[Orchestrator] = None


def set_orchestrator(orchestrator: Orchestrator) -> None:
    """Set the global orchestrator reference for route handlers."""
    global _orchestrator
    _orchestrator = orchestrator


def _get_orchestrator() -> Orchestrator:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    return _orchestrator


# ── Health ──

@router.get("/health")
async def health():
    """System health check."""
    orch = _get_orchestrator()
    return {
        "status": "healthy",
        "uptime_seconds": round(orch.metrics.uptime_seconds, 1),
        "profile_loaded": orch.profile is not None,
        "active_sources": len(orch.connectors.active_connectors()),
    }


# ── Status (dual response) ──

@router.get("/status")
async def status():
    """Monitor health + network condition as independent objects.

    Prevents confusing "the monitor is broken" with "the monitor found
    a supply-chain problem."
    """
    orch = _get_orchestrator()
    return orch.get_status()


# ── Alerts ──

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Alert history with optional filtering."""
    orch = _get_orchestrator()
    from ..models.state import AlertSeverity

    sev = None
    if severity:
        try:
            sev = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(400, f"Invalid severity: {severity}")

    alerts = orch.alert_manager.get_alerts(severity=sev, limit=limit, offset=offset)
    return {
        "alerts": [a.model_dump(mode="json") for a in alerts],
        "total": len(orch.alert_manager.all_alerts()),
        "limit": limit,
        "offset": offset,
    }


@router.get("/alerts/latest")
async def get_latest_alert():
    """Most recent alert."""
    orch = _get_orchestrator()
    alert = orch.alert_manager.latest_alert()
    if not alert:
        return {"alert": None}
    return {"alert": alert.model_dump(mode="json")}


# ── Situations ──

@router.get("/situations")
async def get_situations():
    """Active situations."""
    orch = _get_orchestrator()
    if not orch.correlation_engine:
        return {"situations": []}

    situations = orch.correlation_engine.active_situations()
    return {
        "situations": [s.model_dump(mode="json") for s in situations],
        "total_active": len(situations),
    }


# ── Profile ──

class ProfileLoadRequest(BaseModel):
    """Request body for loading a network architecture."""
    architecture: Optional[dict] = None
    architecture_file: Optional[str] = None


@router.post("/profile")
async def load_profile(request: ProfileLoadRequest):
    """Load a network architecture and compile a monitoring profile.

    Supply either an inline architecture dict or a path to a JSON file.
    """
    orch = _get_orchestrator()

    if request.architecture:
        arch_data = request.architecture
    elif request.architecture_file:
        try:
            arch_data = json.loads(Path(request.architecture_file).read_text())
        except Exception as e:
            raise HTTPException(400, f"Failed to read architecture file: {e}")
    else:
        raise HTTPException(400, "Provide either 'architecture' or 'architecture_file'")

    try:
        profile = await orch.load_profile_from_architecture(arch_data)
        return {
            "profile_id": profile.profile_id,
            "network_id": profile.network_id,
            "entities": profile.total_entities,
            "locations": profile.total_locations,
            "commodities": profile.total_commodities,
            "watch_targets": len(profile.watch_targets),
            "active_sources": profile.active_sources,
            "query_groups": len(profile.query_groups),
        }
    except Exception as e:
        logger.error(f"Profile compilation failed: {e}")
        raise HTTPException(500, f"Profile compilation failed: {e}")


# ── Event Replay ──

class ReplayRequest(BaseModel):
    """Request body for replaying test events."""
    events: Optional[list[dict]] = None
    events_file: Optional[str] = None


@router.post("/events/replay")
async def replay_events(request: ReplayRequest):
    """Inject test events through the full pipeline.

    Useful for testing and demo purposes.
    """
    orch = _get_orchestrator()

    if not orch.profile:
        raise HTTPException(400, "Load a profile first via POST /api/monitor/profile")

    if request.events:
        event_data = request.events
    elif request.events_file:
        try:
            event_data = json.loads(Path(request.events_file).read_text())
        except Exception as e:
            raise HTTPException(400, f"Failed to read events file: {e}")
    else:
        raise HTTPException(400, "Provide either 'events' or 'events_file'")

    from ..models.events import CanonicalEvent

    results = []
    for ed in event_data:
        try:
            event = CanonicalEvent(**ed)
            situation = await orch.process_event(event)
            results.append({
                "event_id": event.event_id,
                "title": event.title,
                "matched": situation is not None,
                "situation_id": situation.situation_id if situation else None,
                "severity": situation.severity.value if situation else None,
            })
        except Exception as e:
            results.append({"error": str(e), "event": ed.get("title", "unknown")})

    return {
        "processed": len(results),
        "results": results,
        "pipeline_summary": orch.metrics.summary(),
    }


# ── Metrics ──

@router.get("/metrics")
async def get_metrics():
    """Pipeline metrics — "of everything observed, how much actually mattered?" """
    orch = _get_orchestrator()
    return orch.metrics.to_dict()


# ── Entities ──

@router.get("/entities")
async def get_entities():
    """Monitored entities with current monitoring state."""
    orch = _get_orchestrator()
    states = orch.state_manager.all_states()
    return {
        "entities": [
            {
                "entity_id": s.entity_id,
                "entity_name": s.entity_name,
                "state": s.state.value,
                "previous_state": s.previous_state.value if s.previous_state else None,
                "state_changed_at": s.state_changed_at.isoformat() if s.state_changed_at else None,
                "reason": s.reason,
                "situation_id": s.situation_id,
            }
            for s in states.values()
        ],
        "total": len(states),
        "elevated": len(orch.state_manager.get_elevated_entities()),
    }


# ── Sources ──

@router.get("/sources")
async def get_sources():
    """Source connector health."""
    orch = _get_orchestrator()
    connectors = orch.connectors.active_connectors()
    return {
        "sources": [
            {
                "name": name,
                "state": conn.health.state.value,
                "signal_types": [s.value for s in conn.signal_types],
                "last_success": conn.health.last_success.isoformat() if conn.health.last_success else None,
                "last_failure": conn.health.last_failure.isoformat() if conn.health.last_failure else None,
                "total_requests": conn.health.total_requests,
                "total_failures": conn.health.total_failures,
                "consecutive_failures": conn.health.consecutive_failures,
            }
            for name, conn in connectors.items()
        ],
        "total_active": len(connectors),
    }


# ── Poll (manual trigger) ──

@router.post("/poll")
async def trigger_poll():
    """Manually trigger a polling cycle across all active sources."""
    orch = _get_orchestrator()
    if not orch.profile:
        raise HTTPException(400, "Load a profile first via POST /api/monitor/profile")

    results = await orch.run_poll_cycle()
    return results
