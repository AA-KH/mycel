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
- POST /api/monitor/tradewatch/webhook — Push a tariff event through the pipeline
- POST /api/monitor/alerts/forward     — Forward a pre-formed alert to the main backend
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
        "alert_webhook_url": orch.dispatcher.webhook_url,
        "alert_webhook_configured": orch.dispatcher.is_configured,
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


# ── Webhook Receiver (Push) ──

def _alert_dispatch_summary(orch: Orchestrator, situation) -> dict:
    """Describe what happened to the alert for a situation (if any)."""
    if situation is None:
        return {"alert_id": None, "dispatched": False, "reason": "event not relevant to network"}

    alert = orch.alert_manager._find_active_alert(situation.situation_id)
    if alert is None:
        return {
            "alert_id": None,
            "dispatched": False,
            "reason": (
                f"severity '{situation.severity.value}' below alert threshold "
                "or suppressed by cooldown"
            ),
        }
    return {
        "alert_id": alert.alert_id,
        "dispatched": alert.dispatched,
        "dispatch_attempts": alert.dispatch_attempts,
        "webhook_url": orch.dispatcher.webhook_url,
        "reason": None if alert.dispatched else "webhook dispatch failed — see monitor logs",
    }


async def _force_forward_event(
    orch: Orchestrator,
    event,
    project_id: Optional[str],
    reason: str,
) -> dict:
    """Forward a pushed event straight to the main backend as a CRITICAL alert.

    Used when the normal pipeline cannot or will not produce an alert for an
    explicitly pushed event (no profile loaded, relevance gate rejected it,
    severity below threshold, or cooldown suppression). A pushed tariff event
    is an explicit signal from an upstream system — it must never be dropped
    silently, otherwise the main backend never re-architects around it.
    """
    from uuid import uuid4
    from ..models.situations import Alert
    from ..models.state import AlertSeverity

    alert_id = f"ALT-PUSH-{uuid4().hex[:8].upper()}"
    network_id = orch.profile.network_id if orch.profile else "unprofiled"

    affected_entities: list[dict] = []
    seen: set[str] = set()
    for name in list(event.raw_entities) + list(event.countries) + list(event.commodities):
        if name and str(name) not in seen:
            seen.add(str(name))
            affected_entities.append({"entity_id": str(name), "entity_name": str(name)})

    meta = event.source_metadata or {}
    why: list[str] = [f"Pushed directly by upstream source '{event.source}' ({reason})."]
    if meta.get("new_value") is not None or meta.get("delta") is not None:
        why.append(
            "Tariff change: "
            f"{meta.get('old_value', '?')}% -> {meta.get('new_value', '?')}% "
            f"(delta {meta.get('delta', '?')}) on sector {meta.get('sector') or ', '.join(event.commodities) or '?'}"
        )

    alert = Alert(
        alert_id=alert_id,
        network_id=network_id,
        situation_id=f"SIT-PUSH-{uuid4().hex[:8].upper()}",
        severity=AlertSeverity.CRITICAL,
        event_type=event.event_type or event.signal_type.value,
        title=event.title,
        description=event.description or event.title,
        sources=[{"source": event.source, "url": event.source_url, "event_id": event.event_id}],
        affected_entities=affected_entities,
        affected_locations=[loc.name for loc in event.locations if loc.name],
        affected_commodities=list(event.commodities),
        confidence=max(event.confidence, 0.9),
        why_it_matters=why,
        idempotency_key=alert_id,
    )

    dispatched = await orch.dispatcher.dispatch(alert, project_id=project_id)
    orch.metrics.alerts_generated += 1
    if dispatched:
        orch.metrics.alerts_dispatched += 1
    else:
        orch.metrics.alerts_dispatch_failed += 1
    if orch.alert_manager is not None:
        orch.alert_manager._register_alert(alert)
    if orch._initialized:
        orch.store.save_alert(alert)

    return {
        "alert_id": alert.alert_id,
        "dispatched": dispatched,
        "dispatch_attempts": alert.dispatch_attempts,
        "webhook_url": orch.dispatcher.webhook_url,
        "forced": True,
        "reason": (
            f"forced forward ({reason})" if dispatched
            else f"forced forward ({reason}) but webhook dispatch failed — is the main backend up on port 8000?"
        ),
    }


@router.post("/tradewatch/webhook")
async def tradewatch_webhook(payload: dict):
    """Receive pushed tariff updates from TradeWatch/TariffWire (or CMD/curl).

    Accepts a single tariff object, a list, or ``{"data": [...]}``. Optional
    top-level keys:

    - ``project_id``: pin the resulting alert to a specific main-backend project.
    - ``force`` (default ``true``): if the normal pipeline does not forward the
      event (no profile loaded, relevance gate rejected it, severity below
      threshold, cooldown), forward it anyway as a CRITICAL alert so the main
      backend still regenerates the architecture. Set ``false`` to require the
      event to pass the full pipeline.

    Matching events flow through the full pipeline first; anything that clears
    the severity threshold is forwarded to the main backend, which triggers
    crisis re-architecture.
    """
    orch = _get_orchestrator()

    from ..connectors.tradewatch import TradeWatchConnector
    connector = orch.connectors.get("tradewatch")
    if not connector:
        connector = TradeWatchConnector(orch.config)

    project_id: Optional[str] = None
    force = True
    if isinstance(payload, dict):
        project_id = payload.get("project_id") or None
        raw_force = payload.get("force", True)
        force = raw_force if isinstance(raw_force, bool) else str(raw_force).lower() not in ("0", "false", "no")

    # skip_seen=False: a re-sent CMD payload must not be silently swallowed by
    # the connector — the pipeline deduplicator makes the final call.
    events = connector._normalize(payload, skip_seen=False)
    if not events:
        raise HTTPException(
            400,
            "No tariff events could be parsed. Expected keys: imposingCountry, "
            "targetCountry, sector, newRatePercent (previousRatePercent, delta optional).",
        )

    if not orch.profile and not force:
        raise HTTPException(
            400,
            "Load a profile first via POST /api/monitor/profile (or omit 'force': false "
            "to forward the event directly to the main backend).",
        )

    results = []
    for event in events:
        try:
            situation = None
            alert_summary: dict

            if orch.profile:
                situation = await orch.process_event(event, project_id=project_id)
                alert_summary = _alert_dispatch_summary(orch, situation)
            else:
                alert_summary = {"alert_id": None, "dispatched": False, "reason": "no profile loaded"}

            # The pipeline decided NOT to notify the main backend. For a pushed
            # event that is almost always wrong, so forward it anyway.
            if force and not alert_summary.get("dispatched") and alert_summary.get("alert_id") is None:
                logger.warning(
                    f"Pushed event {event.event_id} not forwarded by pipeline "
                    f"({alert_summary.get('reason')}) — forcing forward to main backend"
                )
                alert_summary = await _force_forward_event(
                    orch, event, project_id, alert_summary.get("reason") or "pipeline did not alert"
                )

            results.append({
                "event_id": event.event_id,
                "title": event.title,
                "countries": event.countries,
                "commodities": event.commodities,
                "matched": situation is not None,
                "situation_id": situation.situation_id if situation else None,
                "severity": situation.severity.value if situation else ("critical" if alert_summary.get("forced") else None),
                "alert": alert_summary,
            })
        except Exception as e:
            logger.exception(f"Error processing webhook event: {e}")
            results.append({"error": str(e), "title": event.title})

    forwarded = sum(1 for r in results if r.get("alert", {}).get("dispatched"))
    return {
        "status": "received",
        "processed": len(results),
        "forwarded_to_main_backend": forwarded,
        "main_backend_webhook": orch.dispatcher.webhook_url,
        "results": results,
    }


# ── Direct Alert Forward (CMD / manual) ──

class ForwardAlertRequest(BaseModel):
    """A pre-formed alert to forward to the main backend through the monitor.

    Mirrors the main backend's ``AlertPayload`` so the same JSON you would
    send to ``/api/v1/monitor/alert`` can be sent here instead and is logged,
    persisted, and forwarded by the monitor.
    """
    alert_id: Optional[str] = None
    severity: str = "CRITICAL"
    title: str
    description: Optional[str] = None
    affected_entities: list[str] = []
    project_id: Optional[str] = None


@router.post("/alerts/forward")
async def forward_alert(request: ForwardAlertRequest):
    """Forward a manual alert to the main backend, bypassing relevance scoring.

    Use this when you already know the alert matters (demo, drill, CMD test)
    and just want the monitor to hand it to the main backend so the main
    backend regenerates the architecture around the new constraint.
    """
    orch = _get_orchestrator()

    from uuid import uuid4
    from ..models.situations import Alert
    from ..models.state import AlertSeverity

    try:
        severity = AlertSeverity(request.severity.lower())
    except ValueError:
        raise HTTPException(
            400, f"Invalid severity '{request.severity}'. Use one of: info, watch, warning, critical"
        )

    alert_id = request.alert_id or f"ALT-MAN-{uuid4().hex[:8].upper()}"
    network_id = orch.profile.network_id if orch.profile else "manual"

    alert = Alert(
        alert_id=alert_id,
        network_id=network_id,
        situation_id=f"SIT-MAN-{uuid4().hex[:8].upper()}",
        severity=severity,
        event_type="manual",
        title=request.title,
        description=request.description or request.title,
        affected_entities=[{"entity_id": e} for e in request.affected_entities],
        confidence=1.0,
        idempotency_key=alert_id,
    )

    dispatched = await orch.dispatcher.dispatch(alert, project_id=request.project_id)
    orch.alert_manager._register_alert(alert)
    orch.metrics.alerts_generated += 1
    if dispatched:
        orch.metrics.alerts_dispatched += 1
    else:
        orch.metrics.alerts_dispatch_failed += 1
    if orch._initialized:
        orch.store.save_alert(alert)

    if not dispatched:
        raise HTTPException(
            502,
            f"Alert {alert_id} could not be delivered to the main backend at "
            f"{orch.dispatcher.webhook_url}. Is the main backend running on port 8000?",
        )

    return {
        "status": "forwarded",
        "alert_id": alert_id,
        "severity": severity.value,
        "webhook_url": orch.dispatcher.webhook_url,
        "project_id": request.project_id,
    }
