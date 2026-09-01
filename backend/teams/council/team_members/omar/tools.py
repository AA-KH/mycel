import json

OMAR_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_regulatory_compliance_audit",
            "description": "Runs a multi-framework regulatory compliance audit on a vendor. Checks FCPA, GDPR, ISO 37001, REACH/RoHS, and local labor law compliance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string"},
                    "country": {"type": "string"},
                    "industry": {"type": "string"},
                    "processes_eu_citizen_data": {"type": "boolean", "description": "Does the vendor handle EU citizen personal data?"},
                    "has_anti_bribery_policy": {"type": "boolean", "description": "Does the vendor have a formal ISO 37001 anti-bribery policy?"},
                    "has_conflict_minerals_declaration": {"type": "boolean", "description": "Has the vendor filed a Conflict Minerals (3TG) declaration?"},
                    "has_reach_rohs_certification": {"type": "boolean", "description": "Is the vendor REACH/RoHS certified (relevant for electronics/chemicals)?"},
                    "has_child_labor_audit": {"type": "boolean", "description": "Has the vendor undergone a third-party child labor audit?"}
                },
                "required": ["vendor_name", "country", "industry", "processes_eu_citizen_data",
                             "has_anti_bribery_policy", "has_conflict_minerals_declaration",
                             "has_reach_rohs_certification", "has_child_labor_audit"]
            }
        }
    }
]

CORRUPTION_INDEX = {
    "Denmark": 88, "Finland": 87, "New Zealand": 87, "Singapore": 85,
    "Germany": 79, "United Kingdom": 73, "Japan": 73, "United States": 69,
    "Taiwan": 63, "South Korea": 63, "Poland": 54, "Brazil": 36,
    "India": 39, "Turkey": 36, "Mexico": 31, "China": 42,
    "Vietnam": 41, "Bangladesh": 25, "Myanmar": 23, "Russia": 26,
    "Iran": 25, "Nigeria": 25
}

async def run_regulatory_compliance_audit(
    vendor_name: str,
    country: str,
    industry: str,
    processes_eu_citizen_data: bool,
    has_anti_bribery_policy: bool,
    has_conflict_minerals_declaration: bool,
    has_reach_rohs_certification: bool,
    has_child_labor_audit: bool
) -> str:
    try:
        critical_violations = []
        warnings = []
        passed = []

        # GDPR Check
        if processes_eu_citizen_data and country not in ["Germany", "France", "Netherlands", "Ireland",
                                                          "United Kingdom", "European Union"]:
            critical_violations.append("GDPR Article 44: Data transfer to non-adequate country without SCCs verified.")
        elif processes_eu_citizen_data:
            passed.append("GDPR: Data residency in adequate country ✅")

        # Anti-bribery (FCPA / ISO 37001)
        corruption_score = CORRUPTION_INDEX.get(country, 40)
        if not has_anti_bribery_policy and corruption_score < 50:
            critical_violations.append(f"FCPA/ISO 37001: No anti-bribery policy. CPI score {corruption_score}/100 is high-risk. Mandatory before onboarding.")
        elif has_anti_bribery_policy:
            passed.append(f"ISO 37001 Anti-Bribery Policy: ✅ (CPI: {corruption_score})")
        else:
            warnings.append(f"ISO 37001: No anti-bribery policy declared. CPI: {corruption_score}.")

        # Conflict Minerals (Dodd-Frank 1502)
        if not has_conflict_minerals_declaration:
            warnings.append("Dodd-Frank 1502: No Conflict Minerals (3TG) declaration. Required for SEC-registered supply chains.")
        else:
            passed.append("Conflict Minerals Declaration (3TG): ✅")

        # REACH/RoHS
        if industry.lower() in ["electronics", "chemicals", "automotive", "manufacturing"]:
            if not has_reach_rohs_certification:
                critical_violations.append("REACH/RoHS: Missing certification. Products cannot legally enter EU market.")
            else:
                passed.append("REACH/RoHS Certification: ✅")

        # Child Labor / ILO
        if not has_child_labor_audit and country in ["Bangladesh", "Myanmar", "Pakistan", "Nigeria", "India"]:
            critical_violations.append("ILO Convention 138/182: No third-party child labor audit. High-risk jurisdiction requires mandatory audit.")
        elif has_child_labor_audit:
            passed.append("Third-Party Child Labor Audit: ✅")

        if critical_violations:
            status = "NON-COMPLIANT"
            omar_decision = "BLOCK — Critical regulatory violations must be resolved before any contract is signed."
        elif warnings:
            status = "CONDITIONAL"
            omar_decision = "CONDITIONAL APPROVAL — Address all warnings within 90 days. Contract may include remediation clause."
        else:
            status = "FULLY COMPLIANT"
            omar_decision = "CLEAR — No regulatory obstacles. Omar approves from compliance perspective."

        return json.dumps({
            "vendor": vendor_name,
            "country": country,
            "corruption_perception_index": corruption_score,
            "compliance_status": status,
            "critical_violations": critical_violations if critical_violations else ["None"],
            "warnings": warnings if warnings else ["None"],
            "passed_checks": passed,
            "omar_decision": omar_decision
        }, indent=2)
    except Exception as e:
        return f"Error running compliance audit: {str(e)}"
