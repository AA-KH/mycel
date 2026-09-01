import json
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
# TOOL SCHEMAS
# ─────────────────────────────────────────────────────────────
SOFIA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "synthesize_council_reports",
            "description": "Ingests and synthesizes the recommendations from Helena (Cost), Vikram (Resilience), Nisha (Operations), and Omar (Compliance). Identifies areas of consensus and direct conflict.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "helena_verdict": {"type": "string", "description": "Helena's cost/margin recommendation (APPROVE/REJECT/RENEGOTIATE)."},
                    "vikram_verdict": {"type": "string", "description": "Vikram's resilience recommendation (RESILIENT/CONDITIONAL/BLOCK)."},
                    "nisha_verdict": {"type": "string", "description": "Nisha's operations recommendation (APPROVE/CONDITIONAL/SEND BACK)."},
                    "omar_verdict": {"type": "string", "description": "Omar's compliance recommendation (CLEAR/CONDITIONAL/BLOCK)."}
                },
                "required": ["subject", "helena_verdict", "vikram_verdict", "nisha_verdict", "omar_verdict"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resolve_strategic_conflict",
            "description": "Resolves direct conflicts between Council members based on the company's current strategic priority (e.g., Cost vs. Resilience, Speed vs. Compliance).",
            "parameters": {
                "type": "object",
                "properties": {
                    "conflict_description": {"type": "string", "description": "Description of the clash (e.g., 'Helena wants cheap single-source; Vikram wants expensive dual-source')."},
                    "member_1": {"type": "string", "description": "Name of first conflicting member (e.g., 'Helena')."},
                    "member_2": {"type": "string", "description": "Name of second conflicting member (e.g., 'Vikram')."},
                    "company_strategic_priority": {
                        "type": "string",
                        "enum": ["MARGIN_MAXIMIZATION", "SUPPLY_CHAIN_SURVIVAL", "RAPID_GROWTH", "ZERO_COMPLIANCE_RISK"],
                        "description": "The current overriding corporate strategy."
                    }
                },
                "required": ["conflict_description", "member_1", "member_2", "company_strategic_priority"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_risk_adjusted_roi",
            "description": "Calculates the TRUE financial return of an initiative by taking Helena's Base ROI and discounting it by Vikram's fragility, Nisha's execution risk, and Omar's compliance exposure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_projected_roi_usd": {"type": "number", "description": "Helena's optimistic ROI / Cost Savings estimate."},
                    "vikram_resilience_score": {"type": "number", "description": "Vikram's score (0-100). Lower score = higher probability of supply shock destroying ROI."},
                    "nisha_feasibility_score": {"type": "number", "description": "Nisha's score (0-100). Lower score = higher probability of execution failure."},
                    "omar_fine_exposure_usd": {"type": "number", "description": "Omar's calculation of maximum statutory fines if compliance gaps are exploited."}
                },
                "required": ["base_projected_roi_usd", "vikram_resilience_score", "nisha_feasibility_score", "omar_fine_exposure_usd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_council_resolution",
            "description": "Formalizes the Council's final binding decision into an official resolution document. Sofia uses this as the LAST step after resolving conflicts and calculating true ROI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "council_decision": {
                        "type": "string",
                        "enum": ["APPROVED", "REJECTED", "DEFERRED", "APPROVED_WITH_CONDITIONS"],
                        "description": "The Council's final binding decision."
                    },
                    "rationale": {"type": "string", "description": "Sofia's synthesis explaining WHY this decision was made."},
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of binding conditions that must be met by specific deadlines."
                    },
                    "review_days": {
                        "type": "integer",
                        "description": "Days until next mandatory review.",
                        "default": 90
                    }
                },
                "required": ["subject", "council_decision", "rationale"]
            }
        }
    }
]


# ─────────────────────────────────────────────────────────────
# TOOL 1: Synthesize Council Reports
# ─────────────────────────────────────────────────────────────
async def synthesize_council_reports(
    subject: str,
    helena_verdict: str,
    vikram_verdict: str,
    nisha_verdict: str,
    omar_verdict: str
) -> str:
    try:
        verdicts = [helena_verdict.upper(), vikram_verdict.upper(), nisha_verdict.upper(), omar_verdict.upper()]
        
        blocks = sum(1 for v in verdicts if "BLOCK" in v or "REJECT" in v or "SEND BACK" in v)
        approves = sum(1 for v in verdicts if "APPROVE" in v or "CLEAR" in v or "RESILIENT" in v)
        conditionals = sum(1 for v in verdicts if "CONDITIONAL" in v or "RENEGOTIATE" in v)

        if blocks == 0 and conditionals == 0:
            consensus = "FULL AGREEMENT — Proceed immediately."
            conflicts = "None."
        elif blocks >= 2:
            consensus = "MULTIPLE VETOS — Highly toxic initiative."
            conflicts = "Fundamental misalignment with corporate risk appetite."
        else:
            consensus = "MIXED — Strategic conflict resolution required."
            clashing = []
            if "APPROVE" in helena_verdict.upper() and ("BLOCK" in vikram_verdict.upper() or "BLOCK" in omar_verdict.upper()):
                clashing.append("Helena (Cost) vs. Risk/Compliance (Vikram/Omar)")
            if "APPROVE" in helena_verdict.upper() and "SEND BACK" in nisha_verdict.upper():
                clashing.append("Helena (Cost) vs. Nisha (Execution Feasibility)")
            
            conflicts = ", ".join(clashing) if clashing else "Varying degrees of conditionality."

        return json.dumps({
            "subject": subject,
            "vote_tally": {
                "APPROVE": approves,
                "CONDITIONAL": conditionals,
                "BLOCK/REJECT": blocks
            },
            "member_breakdown": {
                "Helena_Cost": helena_verdict,
                "Vikram_Resilience": vikram_verdict,
                "Nisha_Operations": nisha_verdict,
                "Omar_Compliance": omar_verdict
            },
            "consensus_status": consensus,
            "identified_conflicts": conflicts
        }, indent=2)
    except Exception as e:
        return f"Error synthesizing reports: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: Resolve Strategic Conflict
# ─────────────────────────────────────────────────────────────
async def resolve_strategic_conflict(
    conflict_description: str,
    member_1: str,
    member_2: str,
    company_strategic_priority: str
) -> str:
    try:
        # Hard Veto Rules
        if member_1.lower() == "omar" or member_2.lower() == "omar":
            if "sanctions" in conflict_description.lower() or "fcpa" in conflict_description.lower():
                return json.dumps({
                    "conflict": conflict_description,
                    "priority_applied": "ABSOLUTE VETO",
                    "resolution": "Omar wins. Sanctions/Bribery risk cannot be overruled by any strategic priority. Reject proposal.",
                    "ruled_in_favor_of": "Omar"
                }, indent=2)

        winner = ""
        reason = ""

        if company_strategic_priority == "MARGIN_MAXIMIZATION":
            if "helena" in [member_1.lower(), member_2.lower()]:
                winner = "Helena"
                reason = "Company is in margin preservation mode. Accept higher operational/resilience risk to secure cost savings."
            else:
                winner = "Depends on context"
                reason = "Tie-breaker: Whichever option preserves cash flow."

        elif company_strategic_priority == "SUPPLY_CHAIN_SURVIVAL":
            if "vikram" in [member_1.lower(), member_2.lower()]:
                winner = "Vikram"
                reason = "Company cannot afford a stockout. Pay the premium for redundancy and resilience."
            else:
                winner = "Nisha"
                reason = "Operational stability over cost savings."

        elif company_strategic_priority == "ZERO_COMPLIANCE_RISK":
            if "omar" in [member_1.lower(), member_2.lower()]:
                winner = "Omar"
                reason = "Regulatory environment is hostile. Take zero chances. Block anything with legal ambiguity."

        elif company_strategic_priority == "RAPID_GROWTH":
            if "nisha" in [member_1.lower(), member_2.lower()]:
                winner = "Nisha"
                reason = "Execution speed is paramount. We cannot scale a broken process. Fix operations before adding volume."

        return json.dumps({
            "conflict": conflict_description,
            "strategic_priority_applied": company_strategic_priority,
            "ruled_in_favor_of": winner,
            "sofia_justification": reason
        }, indent=2)
    except Exception as e:
        return f"Error resolving conflict: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 3: Calculate Risk-Adjusted ROI
# ─────────────────────────────────────────────────────────────
async def calculate_risk_adjusted_roi(
    base_projected_roi_usd: float,
    vikram_resilience_score: float,
    nisha_feasibility_score: float,
    omar_fine_exposure_usd: float
) -> str:
    try:
        # Convert 0-100 scores to probabilities (discount factors)
        # A 100 score means 100% of the ROI is realizable. 
        # A 50 score means a 50% chance of failure wiping out the ROI.
        resilience_probability = max(0, min(100, vikram_resilience_score)) / 100.0
        feasibility_probability = max(0, min(100, nisha_feasibility_score)) / 100.0

        # The probability that BOTH the supply chain survives AND the team can execute it
        combined_success_probability = resilience_probability * feasibility_probability

        # Expected Value = (Base ROI * Probability of Success) - (Statutory Fine Exposure * estimated 5% chance of getting caught if there is an exposure)
        expected_roi = base_projected_roi_usd * combined_success_probability
        
        expected_fine_loss = 0
        if omar_fine_exposure_usd > 0:
            expected_fine_loss = omar_fine_exposure_usd * 0.05 # 5% probability of regulator enforcement action
        
        true_risk_adjusted_roi = expected_roi - expected_fine_loss

        if true_risk_adjusted_roi < 0:
            verdict = "NEGATIVE REAL ROI ❌ — The risks (fragility, execution failure, fines) completely wipe out Helena's projected savings. REJECT."
        elif true_risk_adjusted_roi < (base_projected_roi_usd * 0.5):
            verdict = "HIGHLY DISCOUNTED ⚠️ — Realizable value is less than half of projections. Proceed with extreme caution."
        else:
            verdict = "VALUE ACCRETIVE ✅ — Risks are manageable. Expected ROI is strong."

        return json.dumps({
            "base_projected_roi": f"${base_projected_roi_usd:,.2f}",
            "combined_success_probability": f"{combined_success_probability*100:.1f}%",
            "discount_factors": {
                "resilience_discount": f"{resilience_probability*100:.1f}%",
                "feasibility_discount": f"{feasibility_probability*100:.1f}%"
            },
            "expected_gross_roi": f"${expected_roi:,.2f}",
            "statutory_fine_exposure": f"${omar_fine_exposure_usd:,.2f}",
            "expected_regulatory_loss": f"${expected_fine_loss:,.2f} (Assuming 5% enforcement prob)",
            "TRUE_RISK_ADJUSTED_ROI": f"${true_risk_adjusted_roi:,.2f}",
            "sofia_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error calculating risk-adjusted ROI: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 4: Draft Council Resolution
# ─────────────────────────────────────────────────────────────
async def draft_council_resolution(
    subject: str,
    council_decision: str,
    rationale: str,
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
            "chair_rationale": rationale,
            "binding_conditions": conditions if conditions else ["None. Unconditional approval."],
            "next_mandatory_review": next_review,
            "status": "BINDING RESOLUTION — Logged to corporate record.",
            "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        }, indent=2)
    except Exception as e:
        return f"Error drafting resolution: {str(e)}"
