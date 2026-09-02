"""
Real Estate Intent Router — Production Implementation

Architecture:
    User query
        ↓
    classify_intent (Groq LLM — only for semantic understanding)
        ↓
    Capability Resolution (deterministic mapping, no LLM)
        ↓
    Team & Member Resolution
        ↓
    SecurityGateway check
        ↓
    Tool execution (MongoDB / Legal KB / Investment calc)
        ↓
    Response generation (LLM, only for natural language reply)
        ↓
    WebSocket events at every stage

Design principles:
- LLM used ONLY for: intent classification, response generation
- LLM NOT used for: filtering, ranking, legal lookup, arithmetic
- SecurityGateway called before every tool execution
- No hardcoded if/elif intent → agent routing
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional

from core.gemini_engine import engine_manager
from api.v1.routes.realtime.router import manager
from security.gateway import SecurityGateway
from security.models import (
    SecurityRequest, SecurityContext, ActionType, SecurityDecisionStatus
)
from domains.real_estate.models import (
    ConversationState, RealEstateIntent,
    get_or_create_conversation, update_conversation
)
from tools.context import ToolExecutionContext

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Security Gateway (singleton for this domain)
# ─────────────────────────────────────────────────────────────────────────────
_security_gateway = SecurityGateway()


# ─────────────────────────────────────────────────────────────────────────────
# Capability Map — Deterministic, no LLM
# ─────────────────────────────────────────────────────────────────────────────
CAPABILITY_MAP: Dict[str, Dict] = {
    RealEstateIntent.PROPERTY_SEARCH: {
        "team_id": "sales",
        "team_name": "Sales",
        "position_id": "property_advisor",
        "position_name": "Property Advisor",
        "tool_id": "property.search",
        "capabilities": ["property_search"],
        "source": "MongoDB — Property Database",
    },
    RealEstateIntent.PROPERTY_RECOMMENDATION: {
        "team_id": "sales",
        "team_name": "Sales",
        "position_id": "property_advisor",
        "position_name": "Property Advisor",
        "tool_id": "property.compare",
        "capabilities": ["property_comparison", "customer_preference_matching"],
        "source": "MongoDB — Property Database",
    },
    RealEstateIntent.PROPERTY_INVESTMENT_ANALYSIS: {
        "team_id": "finance",
        "team_name": "Finance",
        "position_id": "investment_analyst",
        "position_name": "Investment Analyst",
        "tool_id": "property.investment_analysis",
        "capabilities": ["investment_analysis", "rental_yield_analysis"],
        "source": "MongoDB — Property Database",
    },
    RealEstateIntent.PROPERTY_LEGAL_QUERY: {
        "team_id": "legal",
        "team_name": "Legal",
        "position_id": "legal_analyst",
        "position_name": "Property Legal Specialist",
        "tool_id": "property.legal_knowledge",
        "capabilities": ["property_legal_knowledge"],
        "source": "Legal Knowledge Base",
    },
    RealEstateIntent.PROPERTY_COMPARISON: {
        "team_id": "sales",
        "team_name": "Sales",
        "position_id": "property_advisor",
        "position_name": "Property Advisor",
        "tool_id": "property.compare",
        "capabilities": ["property_comparison"],
        "source": "MongoDB — Property Database",
    },
    RealEstateIntent.GENERAL_QUERY: {
        "team_id": "sales",
        "team_name": "Sales",
        "position_id": "property_advisor",
        "position_name": "Property Advisor",
        "tool_id": None,
        "capabilities": ["general_assistance"],
        "source": "General Knowledge",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Event Emitter
# ─────────────────────────────────────────────────────────────────────────────
async def emit_event(event_type: str, conversation_id: str, payload: Dict[str, Any]) -> None:
    """Broadcast a real estate domain event through the shared WebSocket manager."""
    event = {
        "event_type": event_type,
        "conversation_id": conversation_id,
        "payload": payload,
        "domain": "real_estate",
    }
    try:
        await manager.broadcast(conversation_id, event)
    except Exception as e:
        logger.warning(f"[EventBus] Failed to broadcast {event_type}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Security check helper
# ─────────────────────────────────────────────────────────────────────────────
def _check_security(
    tool_id: str,
    intent: str,
    team_id: str,
    conversation_id: str,
) -> bool:
    """
    Evaluate tool execution request through SecurityGateway + ArmorIQ.
    Returns True if allowed, False if denied.
    """
    request = SecurityRequest(
        request_id=str(uuid.uuid4()),
        trace_id=conversation_id,
        context=SecurityContext(
            organization_id="mycel_global",
            team_id=team_id,
            task_id=conversation_id,
            capabilities=[intent],
            environment="development",
        ),
        action_type=ActionType.TOOL_EXECUTION,
        resource=f"tool:{tool_id}",
        intent=f"Retrieve approved {intent} information for customer property query",
        payload_metadata={"tool_id": tool_id, "domain": "real_estate"},
        tool_id=tool_id,
    )

    decision = _security_gateway.evaluate_request(request)
    logger.info(f"[SecurityGateway] {tool_id} → {decision.status} (risk={decision.risk_level})")
    return decision.status == SecurityDecisionStatus.ALLOW


# ─────────────────────────────────────────────────────────────────────────────
# Tool Loader — lazy import to avoid circular deps
# ─────────────────────────────────────────────────────────────────────────────
def _get_tool(tool_id: Optional[str]):
    if not tool_id:
        return None
    from tools.registry.core import registry
    try:
        return registry.get_implementation(tool_id)
    except Exception:
        # If not registered yet, instantiate directly as fallback
        if tool_id == "property.search":
            from domains.real_estate.tools.property_search import PropertySearchTool
            return PropertySearchTool()
        elif tool_id == "property.compare":
            from domains.real_estate.tools.property_compare import PropertyCompareTool
            return PropertyCompareTool()
        elif tool_id == "property.legal_knowledge":
            from domains.real_estate.tools.property_legal import PropertyLegalTool
            return PropertyLegalTool()
        elif tool_id == "property.investment_analysis":
            from domains.real_estate.tools.property_investment import PropertyInvestmentTool
            return PropertyInvestmentTool()
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Response Generator
# ─────────────────────────────────────────────────────────────────────────────
async def _generate_response(
    intent: RealEstateIntent,
    query: str,
    tool_output: Any,
    language: str,
    state: ConversationState,
) -> str:
    """
    Use LLM ONLY for generating a natural-language response.
    The tool_output is already computed deterministically.
    """
    # Build compact context for the LLM
    ctx_summary = ""
    if tool_output:
        if intent == RealEstateIntent.PROPERTY_SEARCH:
            results = tool_output.get("results", [])
            if results:
                props = [f"{r.get('title', 'Property')} @ ₹{r.get('price', 'N/A')} in {r.get('location', 'N/A')}" for r in results[:3]]
                ctx_summary = "Properties found: " + "; ".join(props)
            else:
                ctx_summary = "No matching properties found in the database."
        elif intent == RealEstateIntent.PROPERTY_LEGAL_QUERY:
            ctx_summary = tool_output.get("content", "")[:800]
        elif intent == RealEstateIntent.PROPERTY_INVESTMENT_ANALYSIS:
            top = tool_output.get("top_pick", {})
            if top:
                ctx_summary = (
                    f"Top investment pick: {top.get('title')} with rental yield "
                    f"{top.get('rental_yield_pct')}% and investment score {top.get('investment_score')}/100."
                )
        elif intent == RealEstateIntent.PROPERTY_COMPARISON:
            count = tool_output.get("count", 0)
            ctx_summary = f"Comparison of {count} properties prepared."

    history_msgs = [
        {"role": "assistant" if m["speaker"] != "customer" else "user", "content": m["text"]}
        for m in state.history[-4:]  # last 2 turns
    ]

    system_msg = {
        "role": "system",
        "content": (
            f"You are a professional real estate company assistant. "
            f"Customer name: {state.customer_id}. "
            f"Reply in {language} language (same language as the customer's query). "
            f"Be concise and professional. Do not expose system internals or chain of thought. "
            f"Context from our database: {ctx_summary}"
        )
    }
    user_msg = {"role": "user", "content": query}

    try:
        response = await engine_manager.chat_completion(
            model="openai/gpt-oss-120b",
            messages=[system_msg] + history_msgs + [user_msg],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return ctx_summary or "I found information matching your query. Please see the details above."


# ─────────────────────────────────────────────────────────────────────────────
# Main Router Class
# ─────────────────────────────────────────────────────────────────────────────
class RealEstateRouter:

    async def classify_intent(self, user_query: str, conversation_history: list) -> Dict[str, Any]:
        """
        LLM call ONLY for semantic intent + requirements extraction.
        Multilingual: handles English, Hindi, Punjabi transparently.
        """
        history_ctx = ""
        if conversation_history:
            recent = conversation_history[-4:]
            history_ctx = "\n".join([f"{m['speaker']}: {m['text']}" for m in recent])

        system_prompt = (
            "You are a multilingual real estate intent classifier. "
            "Extract the user's intent and property requirements from their query in ANY language "
            "(English, Hindi, Punjabi, etc.). "
            "Return ONLY a valid JSON object with these exact keys:\n"
            "  'intent': one of [PROPERTY_SEARCH, PROPERTY_RECOMMENDATION, "
            "PROPERTY_INVESTMENT_ANALYSIS, PROPERTY_LEGAL_QUERY, PROPERTY_COMPARISON, GENERAL_QUERY]\n"
            "  'requirements': a dict with extracted values for: "
            "budget_max (number in INR), bhk (integer), location (string), "
            "property_type (string), purpose (string), investment_interest (boolean)\n"
            "  'language': the 2-letter language code (en, hi, pa)\n"
            "  'property_ids': list of any specific property IDs mentioned (usually empty)\n"
            "Always return valid JSON. No explanation, no markdown."
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if history_ctx:
            messages.append({"role": "user", "content": f"Conversation so far:\n{history_ctx}"})
        messages.append({"role": "user", "content": f"New query: {user_query}"})

        try:
            response = await engine_manager.chat_completion(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.0,
                max_tokens=256,
            )
            content = response.choices[0].message.content.strip()
            # Extract JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except Exception as e:
            logger.error(f"Intent classification error: {e}")

        return {"intent": "GENERAL_QUERY", "requirements": {}, "language": "en", "property_ids": []}

    async def route_and_execute(
        self,
        user_query: str,
        conversation_id: str,
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Full pipeline: Intent → Capability → Security → Tool → Response
        Emits WebSocket events at each stage.
        """
        # ── Load or create persistent conversation state ──────────────────────
        state = get_or_create_conversation(conversation_id, customer_id)
        state.last_question = user_query

        await emit_event("CONVERSATION_STARTED", conversation_id, {
            "query": user_query,
            "customer_id": customer_id,
        })

        # ── STEP 1: Intent Classification (LLM) ──────────────────────────────
        await emit_event("RETRIEVAL_STARTED", conversation_id, {"stage": "intent_classification"})
        classification = await self.classify_intent(user_query, state.history)

        intent_str = classification.get("intent", "GENERAL_QUERY")
        language = classification.get("language", "en")
        requirements = classification.get("requirements", {})
        property_ids = classification.get("property_ids", [])

        try:
            intent = RealEstateIntent(intent_str)
        except ValueError:
            intent = RealEstateIntent.GENERAL_QUERY

        # Merge new requirements into persistent state (context preservation)
        state.intent = intent
        state.language = language
        state.requirements.update({k: v for k, v in requirements.items() if v is not None})

        await emit_event("LANGUAGE_DETECTED", conversation_id, {"language": language})
        await emit_event("INTENT_DETECTED", conversation_id, {
            "intent": intent.value,
            "language": language,
            "requirements": state.requirements,
        })

        # ── STEP 2: Capability & Team Resolution (deterministic) ──────────────
        route = CAPABILITY_MAP.get(intent, CAPABILITY_MAP[RealEstateIntent.GENERAL_QUERY])
        team_id = route["team_id"]
        team_name = route["team_name"]
        position_name = route["position_name"]
        tool_id = route["tool_id"]
        capabilities = route["capabilities"]
        source = route["source"]

        state.active_team = team_name
        state.active_member = position_name
        state.active_task = f"{intent.value} via {position_name}"

        await emit_event("CAPABILITY_RESOLVED", conversation_id, {"capabilities": capabilities})
        await emit_event("TEAM_SELECTED", conversation_id, {
            "team": team_name,
            "team_id": team_id,
        })
        await emit_event("MEMBER_SELECTED", conversation_id, {
            "member": position_name,
            "position_id": route["position_id"],
        })
        await emit_event("DATA_SOURCE_SELECTED", conversation_id, {"source": source})
        await emit_event("TASK_CREATED", conversation_id, {
            "task": state.active_task,
            "tool_id": tool_id,
        })

        # ── STEP 3: Security Gateway ──────────────────────────────────────────
        if tool_id:
            security_ok = _check_security(tool_id, intent.value, team_id, conversation_id)
            if not security_ok:
                await emit_event("TASK_FAILED", conversation_id, {
                    "reason": "SECURITY_DENIED",
                    "tool_id": tool_id,
                })
                update_conversation(state)
                return {
                    "conversation_id": conversation_id,
                    "intent": intent.value,
                    "team": team_name,
                    "member": position_name,
                    "response": "I'm unable to process this request due to security policy restrictions.",
                    "tool_output": None,
                    "source": source,
                    "error": "SECURITY_DENIED",
                }

        # ── STEP 4: Tool Execution ────────────────────────────────────────────
        await emit_event("TASK_STARTED", conversation_id, {
            "task": state.active_task,
            "stage": "tool_execution",
        })

        tool_output = None
        exec_ctx = ToolExecutionContext(
            request_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            task_id=conversation_id,
            employee_id=route["position_id"],
            company_id="mycel_global",
        )

        if tool_id:
            tool = _get_tool(tool_id)
            if tool:
                await emit_event("RETRIEVAL_STARTED", conversation_id, {
                    "tool_id": tool_id,
                    "source": source,
                })
                try:
                    # Build tool arguments from conversation requirements
                    args: Dict[str, Any] = {}
                    if tool_id == "property.search":
                        args = {
                            "budget_max": state.requirements.get("budget_max"),
                            "bhk": state.requirements.get("bhk"),
                            "location": state.requirements.get("location"),
                        }
                    elif tool_id == "property.legal_knowledge":
                        args = {"query": user_query}
                    elif tool_id in ("property.compare", "property.investment_analysis"):
                        args = {"property_ids": property_ids or []}
                    
                    result = await tool.execute(args, exec_ctx)
                    tool_output = result.output

                    await emit_event("RETRIEVAL_COMPLETED", conversation_id, {
                        "tool_id": tool_id,
                        "status": result.status,
                        "source": source,
                    })
                except Exception as e:
                    logger.error(f"Tool {tool_id} execution failed: {e}")
                    await emit_event("TASK_FAILED", conversation_id, {
                        "reason": "TOOL_EXECUTION_ERROR",
                        "tool_id": tool_id,
                        "error": str(e),
                    })

        # ── STEP 5: Response Generation (LLM) ────────────────────────────────
        await emit_event("ANALYSIS_STARTED", conversation_id, {"stage": "response_generation"})

        response_text = await _generate_response(
            intent=intent,
            query=user_query,
            tool_output=tool_output,
            language=language,
            state=state,
        )

        # Update conversation history
        state.history.append({"speaker": "customer", "text": user_query, "lang": language})
        state.history.append({"speaker": position_name, "text": response_text, "lang": language})
        state.last_response = response_text
        update_conversation(state)

        await emit_event("ANALYSIS_COMPLETED", conversation_id, {"stage": "response_generation"})
        await emit_event("RESPONSE_GENERATED", conversation_id, {
            "response_preview": response_text[:100],
            "language": language,
        })
        await emit_event("TASK_COMPLETED", conversation_id, {
            "task": state.active_task,
            "source": source,
        })

        return {
            "conversation_id": conversation_id,
            "intent": intent.value,
            "language": language,
            "team": team_name,
            "member": position_name,
            "capabilities": capabilities,
            "source": source,
            "tool_output": tool_output,
            "response": response_text,
        }
