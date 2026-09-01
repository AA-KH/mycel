import json
from datetime import datetime, timedelta

SOFIA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "draft_council_resolution",
            "description": "Formalizes the Council's final binding decision into an official resolution document. Sofia uses this as the LAST step after synthesizing all member inputs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Subject of the resolution (e.g., 'Vendor Onboarding: Acme Corp')."},
                    "council_decision": {
                        "type": "string",
                        "enum": ["APPROVED", "REJECTED", "DEFERRED", "APPROVED_WITH_CONDITIONS"],
                        "description": "The Council's final binding decision."
                    },
                    "member_votes": {
                        "type": "object",
                        "description": "Each member's recommendation. Keys: helena, vikram, nisha, omar.",
                        "properties": {
                            "helena": {"type": "string"},
                            "vikram": {"type": "string"},
                            "nisha": {"type": "string"},
                            "omar": {"type": "string"}
                        }
                    },
                    "rationale": {"type": "string", "description": "Sofia's synthesis explaining WHY this decision was made."},
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of conditions that must be met (if APPROVED_WITH_CONDITIONS)."
                    },
                    "review_days": {
                        "type": "integer",
                        "description": "Number of days until next mandatory review (e.g., 90, 180, 365).",
                        "default": 90
                    }
                },
                "required": ["subject", "council_decision", "rationale"]
            }
        }
    }
]

async def draft_council_resolution(
    subject: str,
    council_decision: str,
    rationale: str,
    member_votes: dict = None,
    conditions: list = None,
    review_days: int = 90
) -> str:
    try:
        resolution_id = f"COUNCIL-RES-{datetime.now().strftime('%Y%m%d-%H%M')}"
        next_review = (datetime.now() + timedelta(days=review_days)).strftime("%Y-%m-%d")

        decision_emoji = {
            "APPROVED": "✅",
            "REJECTED": "❌",
            "DEFERRED": "⏸️",
            "APPROVED_WITH_CONDITIONS": "⚠️✅"
        }.get(council_decision, "❓")

        return json.dumps({
            "resolution_id": resolution_id,
            "issued_by": "Sofia — Council Chair",
            "subject": subject,
            "final_decision": f"{decision_emoji} {council_decision}",
            "member_votes": member_votes or {
                "helena": "Not recorded",
                "vikram": "Not recorded",
                "nisha": "Not recorded",
                "omar": "Not recorded"
            },
            "sofia_rationale": rationale,
            "conditions_if_any": conditions if conditions else ["None"],
            "next_mandatory_review": next_review,
            "status": "BINDING — Requires COO/CFO co-signature for contracts >$1M",
            "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        }, indent=2)
    except Exception as e:
        return f"Error drafting resolution: {str(e)}"
