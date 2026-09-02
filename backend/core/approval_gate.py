"""
core/approval_gate.py

ArmorIQ Human-in-the-Loop Gate — GREEN / AMBER / RED classification.

GREEN  — Autonomous. Agent executes immediately, result logged to ArmorIQ portal.
AMBER  — User Approval required. Agent pauses, frontend shows approval modal,
         ArmorIQ verifies delegated authority, then execute via MCP.
RED    — Automatically blocked. ArmorIQ portal logs the block. No execution.

Flow for AMBER:
  agent.execute_tool()
    -> gate_tool_call()
      -> armoriq_session.check()  [raises PolicyHoldException]
        -> publish approval_request WS event
        -> wait for user decision (asyncio.Event, 120s timeout -> auto-deny)
        -> POST /realtime/approvals/{id}/respond  [frontend calls this]
      -> armoriq_session.report()  [logs to portal regardless of outcome]
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Any

from core.logger import logger

try:
    from armoriq_sdk import (
        ArmorIQClient,
        ArmorIQSession,
        SessionOptions,
        ReportOptions,
        PolicyHoldException,
        PolicyBlockedException,
    )
    HAS_SDK = True
except ImportError:
    HAS_SDK = False


class ActionClass(str, Enum):
    """Three-tier action classification matching user requirements."""
    GREEN = "GREEN"    # Autonomous — no user approval needed
    AMBER = "AMBER"    # User approval required via ArmorIQ delegation
    RED   = "RED"      # Automatically blocked, never executes


# ---------------------------------------------------------------------------
# Tool classification table
# ---------------------------------------------------------------------------
# Add any new tools here. Anything not listed defaults to AMBER (safe default).

_TOOL_CLASS: Dict[str, ActionClass] = {
    # GREEN — public data, calculations, document generation, simulations
    "web_search":                   ActionClass.GREEN,
    "web_scrape":                   ActionClass.GREEN,
    "generate_mermaid_graph":       ActionClass.GREEN,
    "validate_json_schema":         ActionClass.GREEN,
    "search_internal_documents":    ActionClass.GREEN,
    "generate_flow_diagram":        ActionClass.GREEN,
    "calculate_distance":           ActionClass.GREEN,
    "calculate_eoq":                ActionClass.GREEN,
    "calculate_financial_impact":   ActionClass.GREEN,
    "estimate_emergency_freight":   ActionClass.GREEN,
    "simulate_bottleneck":          ActionClass.GREEN,
    "calculate_resilience_score":   ActionClass.GREEN,
    "calculate_tariff_impact":      ActionClass.GREEN,
    "design_supply_chain_network":  ActionClass.GREEN,
    "map_supplier_dependencies":    ActionClass.GREEN,
    "score_vendor_contract_risk":   ActionClass.GREEN,
    "check_esg_compliance":         ActionClass.GREEN,
    "check_trade_policy":           ActionClass.GREEN,
    "analyze_strategic_cost_benefit": ActionClass.GREEN,
    "search_alternate_suppliers":   ActionClass.GREEN,

    # AMBER — requires human approval (private/external data or business accounts)
    "contact_supplier":             ActionClass.AMBER,
    "request_quotation":            ActionClass.AMBER,
    "request_private_information":  ActionClass.AMBER,
    "access_business_account":      ActionClass.AMBER,
    "access_connected_data":        ActionClass.AMBER,
    "send_email":                   ActionClass.AMBER,
    "send_external_message":        ActionClass.AMBER,
    "query_crm":                    ActionClass.AMBER,
    "query_erp":                    ActionClass.AMBER,

    # RED — automatically blocked (financial commitments, legal, out-of-scope)
    "make_purchase":                ActionClass.RED,
    "sign_agreement":               ActionClass.RED,
    "commit_company_funds":         ActionClass.RED,
    "change_financial_records":     ActionClass.RED,
    "access_out_of_scope_data":     ActionClass.RED,
    "contact_unauthorized_party":   ActionClass.RED,
    "deploy_config":                ActionClass.RED,
    "submit_procurement_request":   ActionClass.RED,
    "write_database":               ActionClass.RED,
}

_DEFAULT_CLASS = ActionClass.AMBER  # Unknown tools default to AMBER (require approval)


def classify(tool_name: str) -> ActionClass:
    return _TOOL_CLASS.get(tool_name, _DEFAULT_CLASS)


# ---------------------------------------------------------------------------
# ArmorIQ Session Pool  (one session per agent/session_id pair)
# ---------------------------------------------------------------------------

@dataclass
class ApprovalSlot:
    """Holds the pending state for one human approval request."""
    event: asyncio.Event = field(default_factory=asyncio.Event)
    approved: bool = False


_pending: Dict[str, ApprovalSlot] = {}
_sessions: Dict[str, "ArmorIQSession"] = {}  # cache: session_id -> ArmorIQSession
_armoriq_client: Optional[Any] = None


def _get_client() -> Optional[Any]:
    """Lazy-init the ArmorIQ client singleton.
    
    Returns None when:
      - security_provider_mode = 'mock'  (dev/testing — no SDK connection)
      - armoriq_api_key not set
      - SDK not installed
    GREEN/AMBER/RED classification still applies in mock mode.
    AMBER actions still show the human approval modal.
    Only ArmorIQ portal logging + SDK delegation are skipped.
    """
    global _armoriq_client
    if _armoriq_client is not None:
        return _armoriq_client
    if not HAS_SDK:
        logger.warning("[ArmorIQ] SDK not installed.")
        return None
    try:
        from core.config import settings
        mode = getattr(settings, 'security_provider_mode', 'armoriq').lower()
        if mode == 'mock':
            logger.info("[ArmorIQ] MOCK mode — ArmorIQ SDK disabled. Classification rules still active.")
            return None
        if not settings.armoriq_api_key:
            logger.warning("[ArmorIQ] API key not set — running without ArmorIQ portal logging.")
            return None
        _armoriq_client = ArmorIQClient(api_key=settings.armoriq_api_key)
        logger.info("[ArmorIQ] Client initialized successfully (live mode).")
        return _armoriq_client
    except Exception as e:
        logger.error(f"[ArmorIQ] Failed to initialize client: {e}")
        return None


def _get_session(session_id: str, agent_name: str) -> Optional[Any]:
    """Get or create an ArmorIQ session for this agent."""
    key = f"{session_id}:{agent_name}"
    if key in _sessions:
        return _sessions[key]
    client = _get_client()
    if not client:
        return None
    try:
        opts = SessionOptions(llm=agent_name, mode="sdk")
        session = client.start_session(opts)
        _sessions[key] = session
        logger.debug(f"[ArmorIQ] New session for {agent_name} in project {session_id}")
        return session
    except Exception as e:
        logger.error(f"[ArmorIQ] Session creation failed for {agent_name}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main gate function
# ---------------------------------------------------------------------------

async def gate_tool_call(
    session_id: str,
    agent_name: str,
    tool_name: str,
    arguments: dict,
    timeout_seconds: int = 120,
) -> bool:
    """
    Gate a tool call through the GREEN/AMBER/RED classification system.

    Returns True if execution should proceed, False if blocked/denied.
    """
    action_class = classify(tool_name)
    session = _get_session(session_id, agent_name)

    logger.info(f"[ArmorIQ] {agent_name} -> {tool_name} | class={action_class.value}")

    # -- GREEN: Autonomous, execute immediately --------------------------------
    if action_class == ActionClass.GREEN:
        logger.debug(f"[ArmorIQ] AUTO-ALLOW (GREEN) {tool_name} for {agent_name}")
        return True

    # -- RED: Automatically blocked -------------------------------------------
    if action_class == ActionClass.RED:
        reason = f"Tool '{tool_name}' is classified RED — financial/legal/out-of-scope actions are blocked."
        logger.warning(f"[ArmorIQ] BLOCKED (RED) {tool_name} for {agent_name}: {reason}")

        # Log to ArmorIQ portal
        if session:
            try:
                session.report(
                    tool_name=tool_name,
                    tool_args=arguments,
                    result=None,
                    opts=ReportOptions(status="failed", error_message=f"RED: {reason}"),
                )
            except Exception as e:
                logger.debug(f"[ArmorIQ] Portal log error (RED): {e}")

        # Publish block event to frontend
        from core.events import event_publisher
        await event_publisher.publish(session_id, "approval_response", {
            "approval_id": None,
            "approved": False,
            "agent": agent_name,
            "tool": tool_name,
            "class": "RED",
            "reason": reason,
        })
        return False

    # -- AMBER: Requires human approval ----------------------------------------
    # Try ArmorIQ SDK check first
    armoriq_reason = "Agent requires access to non-public data or a business account."
    if session:
        try:
            session.check(tool_name, arguments)
            # If check passes without raising, ArmorIQ says auto-allow (unusual for AMBER but respect it)
            logger.info(f"[ArmorIQ] SDK auto-approved (AMBER) {tool_name} for {agent_name}")
            return True
        except PolicyHoldException as e:
            armoriq_reason = str(e) or armoriq_reason
            logger.info(f"[ArmorIQ] SDK PolicyHold for {tool_name}: {armoriq_reason}")
        except PolicyBlockedException as e:
            reason = str(e) or "ArmorIQ policy blocked this action."
            logger.warning(f"[ArmorIQ] SDK PolicyBlocked (RED override) for {tool_name}: {reason}")
            if session:
                try:
                    session.report(tool_name, arguments, None,
                                   ReportOptions(status="failed", error_message=reason))
                except Exception:
                    pass
            return False
        except Exception as e:
            logger.warning(f"[ArmorIQ] SDK check error for {tool_name}: {e}. Falling through to manual approval.")

    # Request human approval via frontend modal
    approved = await _request_human_approval(
        session_id=session_id,
        agent_name=agent_name,
        tool_name=tool_name,
        arguments=arguments,
        action_class=action_class,
        reason=armoriq_reason,
        timeout_seconds=timeout_seconds,
    )

    # Report outcome to ArmorIQ portal
    if session:
        try:
            session.report(
                tool_name=tool_name,
                tool_args=arguments,
                result=None,
                opts=ReportOptions(
                    status="success" if approved else "failed",
                    error_message=None if approved else "Human denied the action.",
                    is_delegated=True,
                ),
            )
        except Exception as e:
            logger.debug(f"[ArmorIQ] Portal report error: {e}")

    return approved


async def _request_human_approval(
    session_id: str,
    agent_name: str,
    tool_name: str,
    arguments: dict,
    action_class: ActionClass,
    reason: str,
    timeout_seconds: int,
) -> bool:
    """
    Publish an approval_request WS event and pause until user responds.
    Auto-denies on timeout (fail-safe).
    """
    from core.events import event_publisher

    approval_id = str(uuid.uuid4())
    slot = ApprovalSlot()
    _pending[approval_id] = slot

    logger.info(f"[ArmorIQ] Awaiting human approval [{approval_id}] for '{tool_name}'")

    await event_publisher.publish(session_id, "approval_request", {
        "approval_id": approval_id,
        "agent": agent_name,
        "tool": tool_name,
        "intent": (
            f"{agent_name} needs to call '{tool_name}'. "
            f"This requires access to non-public data or a business account."
        ),
        "risk": action_class.value,
        "reason": reason,
        "args_preview": str(arguments)[:300],
    })

    try:
        await asyncio.wait_for(slot.event.wait(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"[ArmorIQ] Approval [{approval_id}] timed out ({timeout_seconds}s). Auto-denying.")
        slot.approved = False

    _pending.pop(approval_id, None)
    action = "APPROVED" if slot.approved else "DENIED"
    logger.info(f"[ArmorIQ] Human {action} [{approval_id}] -> '{tool_name}'")

    # Fire approval_response so frontend can remove the modal and log the outcome
    await event_publisher.publish(session_id, "approval_response", {
        "approval_id": approval_id,
        "approved": slot.approved,
        "agent": agent_name,
        "tool": tool_name,
        "class": action_class.value,
    })

    return slot.approved


def resolve_approval(approval_id: str, approved: bool) -> bool:
    """
    Called by POST /api/v1/realtime/approvals/{id}/respond.
    Unblocks the waiting agent coroutine.
    """
    slot = _pending.get(approval_id)
    if not slot:
        logger.warning(f"[ArmorIQ] resolve_approval: unknown id {approval_id} (already expired?)")
        return False
    slot.approved = approved
    slot.event.set()
    return True
