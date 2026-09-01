import json
import aiohttp

# ─────────────────────────────────────────────────────────────
# COUNTRY CODE MAP for World Bank WGI queries
# ─────────────────────────────────────────────────────────────
WGI_COUNTRY_CODES = {
    "china": "CN", "vietnam": "VN", "bangladesh": "BD", "india": "IN",
    "germany": "DE", "usa": "US", "united states": "US", "mexico": "MX",
    "indonesia": "ID", "thailand": "TH", "pakistan": "PK", "turkey": "TR",
    "brazil": "BR", "poland": "PL", "malaysia": "MY", "philippines": "PH",
    "south korea": "KR", "japan": "JP", "taiwan": "TW", "france": "FR",
    "united kingdom": "GB", "uk": "GB", "australia": "AU", "canada": "CA",
    "russia": "RU", "iran": "IR", "myanmar": "MM", "venezuela": "VE",
    "nigeria": "NG", "south africa": "ZA"
}

# ─────────────────────────────────────────────────────────────
# TOOL SCHEMAS
# ─────────────────────────────────────────────────────────────
OMAR_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_anti_corruption_index",
            "description": "Fetches a country's 'Control of Corruption' score from World Bank Governance Indicators (WGI). Returns a score from -2.5 (highly corrupt) to +2.5 (very clean). Use this FIRST to assess FCPA/UKBA bribery risk before evaluating any vendor or contract in that country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_name": {
                        "type": "string",
                        "description": "Country where the vendor operates."
                    }
                },
                "required": ["country_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screen_for_sanctions_and_aml",
            "description": "Screens a vendor and its operating countries against global sanctions lists (OFAC, UN, EU) and AML (Anti-Money Laundering) risk profiles. A single hit here means the deal must be blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string"},
                    "operating_countries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of countries the vendor operates in or routes money through."
                    },
                    "has_pep_exposure": {
                        "type": "boolean",
                        "description": "Is the vendor owned by or affiliated with a Politically Exposed Person (PEP)?"
                    }
                },
                "required": ["vendor_name", "operating_countries", "has_pep_exposure"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audit_gdpr_data_residency",
            "description": "Audits a vendor or system for GDPR data privacy compliance. Checks data residency, adequacy decisions, and Standard Contractual Clauses (SCCs). Fines for failure are up to 4% of global revenue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_name": {"type": "string"},
                    "processes_eu_pii": {"type": "boolean", "description": "Does this system process Personally Identifiable Information (PII) of EU citizens?"},
                    "data_hosting_country": {"type": "string", "description": "Where the data servers are physically located."},
                    "has_scc_agreements": {"type": "boolean", "description": "Are Standard Contractual Clauses signed?"},
                    "has_dpia_completed": {"type": "boolean", "description": "Has a Data Protection Impact Assessment (DPIA) been completed?"}
                },
                "required": ["system_name", "processes_eu_pii", "data_hosting_country", "has_scc_agreements", "has_dpia_completed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audit_esg_and_labor_compliance",
            "description": "Audits a vendor for environmental, social, and governance (ESG) compliance, including Conflict Minerals (Dodd-Frank), REACH/RoHS, and ILO labor standards (forced/child labor).",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string"},
                    "industry": {"type": "string"},
                    "country": {"type": "string"},
                    "has_conflict_minerals_declaration": {"type": "boolean"},
                    "has_reach_rohs_certification": {"type": "boolean"},
                    "has_third_party_labor_audit": {"type": "boolean"}
                },
                "required": ["vendor_name", "industry", "country", "has_conflict_minerals_declaration", "has_reach_rohs_certification", "has_third_party_labor_audit"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_regulatory_fines_exposure",
            "description": "Calculates the maximum statutory financial exposure (fines and penalties) if identified compliance gaps are exploited by regulators. Converts legal risk into CFO-ready dollar figures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_global_revenue_usd": {"type": "number", "description": "Total global revenue of the company (used for % based fines like GDPR)."},
                    "gdpr_violation_flag": {"type": "boolean"},
                    "fcpa_violation_flag": {"type": "boolean"},
                    "sanctions_violation_flag": {"type": "boolean"},
                    "number_of_incidents": {"type": "integer", "description": "Estimated number of regulatory incidents or corrupt transactions.", "default": 1}
                },
                "required": ["company_global_revenue_usd", "gdpr_violation_flag", "fcpa_violation_flag", "sanctions_violation_flag"]
            }
        }
    }
]


# ─────────────────────────────────────────────────────────────
# TOOL 1: World Bank Control of Corruption Index (WGI API — FREE)
# Indicator: CC.EST (Control of Corruption)
# ─────────────────────────────────────────────────────────────
async def fetch_anti_corruption_index(country_name: str) -> str:
    """Fetches a country's Control of Corruption score from World Bank WGI."""
    try:
        country_code = WGI_COUNTRY_CODES.get(country_name.lower().strip())
        if not country_code:
            return json.dumps({
                "error": f"Country '{country_name}' not in supported list. Assume High Risk by default.",
                "supported_countries": list(WGI_COUNTRY_CODES.keys())
            }, indent=2)

        url = (
            f"https://api.worldbank.org/v2/country/{country_code}/indicator/CC.EST"
            f"?format=json&mrv=3"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return f"World Bank WGI API error: {response.status}"
                data = await response.json()

        records = data[1] if len(data) > 1 and data[1] else []
        cc_score = None
        period = "Unknown"
        for record in records:
            if record.get("value") is not None:
                cc_score = record["value"]
                period = record.get("date", "Unknown")
                break

        if cc_score is None:
            return json.dumps({
                "country": country_name,
                "note": "No Control of Corruption data available. Treat as High Risk."
            }, indent=2)

        if cc_score >= 1.0:
            risk = "LOW RISK"
            mandate = "Standard FCPA compliance clauses sufficient."
        elif cc_score >= 0.0:
            risk = "MODERATE RISK"
            mandate = "Enhanced due diligence recommended. Include audit rights in contract."
        elif cc_score >= -1.0:
            risk = "HIGH RISK"
            mandate = "ISO 37001 Anti-Bribery certification or rigorous third-party audit MANDATORY before signing."
        else:
            risk = "CRITICAL EXTREME RISK"
            mandate = "Systemic corruption environment. Board-level approval required. Reject unless vendor is a multinational with proven FCPA track record."

        return json.dumps({
            "country": country_name,
            "country_code": country_code,
            "control_of_corruption_score": round(cc_score, 3),
            "score_range": "-2.5 (highly corrupt) to +2.5 (very clean)",
            "data_period": period,
            "source": "World Bank Governance Indicators (WGI) — CC.EST",
            "fcpa_risk_level": risk,
            "omar_mandate": mandate
        }, indent=2)
    except Exception as e:
        return f"Error fetching anti-corruption data: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: Sanctions & AML Screening
# ─────────────────────────────────────────────────────────────
async def screen_for_sanctions_and_aml(vendor_name: str, operating_countries: list, has_pep_exposure: bool) -> str:
    try:
        COMPREHENSIVE_SANCTIONS = ["Iran", "North Korea", "Syria", "Cuba", "Russia", "Belarus"]
        HIGH_AML_RISK = ["Myanmar", "Panama", "Cayman Islands", "United Arab Emirates", "Turkey"]

        violations = []
        warnings = []

        for country in operating_countries:
            if country in COMPREHENSIVE_SANCTIONS:
                violations.append(f"OFAC violation: Operations in comprehensively sanctioned jurisdiction ({country}).")
            elif country in HIGH_AML_RISK:
                warnings.append(f"FATF Grey/Black List: Operations in high AML risk jurisdiction ({country}).")

        if has_pep_exposure:
            warnings.append("Politically Exposed Person (PEP) exposure detected. Triggers mandatory Enhanced Due Diligence (EDD).")

        if violations:
            status = "FAIL"
            decision = "BLOCK — Strict liability sanctions violation detected. Proceeding constitutes a felony."
        elif warnings:
            status = "CONDITIONAL"
            decision = "HOLD — EDD required to clear AML/PEP warnings before onboarding."
        else:
            status = "PASS"
            decision = "CLEAR — No obvious sanctions or AML flags."

        return json.dumps({
            "entity": vendor_name,
            "sanctions_aml_status": status,
            "violations": violations if violations else ["None"],
            "warnings": warnings if warnings else ["None"],
            "omar_decision": decision
        }, indent=2)
    except Exception as e:
        return f"Error screening sanctions: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 3: GDPR Data Privacy Audit
# ─────────────────────────────────────────────────────────────
async def audit_gdpr_data_residency(
    system_name: str,
    processes_eu_pii: bool,
    data_hosting_country: str,
    has_scc_agreements: bool,
    has_dpia_completed: bool
) -> str:
    try:
        if not processes_eu_pii:
            return json.dumps({"system": system_name, "status": "OUT OF SCOPE", "note": "No EU PII processed. GDPR does not apply."})

        EU_ADEQUATE_COUNTRIES = ["Germany", "France", "Netherlands", "Ireland", "European Union", "United Kingdom", "Japan", "Canada", "New Zealand", "Switzerland", "Israel"]

        gaps = []
        is_adequate = data_hosting_country in EU_ADEQUATE_COUNTRIES

        if not is_adequate and not has_scc_agreements:
            gaps.append(f"GDPR Article 44 Violation: Cross-border transfer to non-adequate country ({data_hosting_country}) without Standard Contractual Clauses (SCCs).")

        if not has_dpia_completed:
            gaps.append("GDPR Article 35 Violation: No Data Protection Impact Assessment (DPIA) completed for high-risk processing.")

        if gaps:
            status = "NON-COMPLIANT"
            decision = "BLOCK deployment. 4% global revenue fine exposure detected."
        else:
            status = "COMPLIANT"
            decision = "CLEAR — Data privacy controls meet GDPR standards."

        return json.dumps({
            "system": system_name,
            "hosting_country": data_hosting_country,
            "adequacy_status": "Adequate" if is_adequate else "Non-Adequate",
            "gdpr_status": status,
            "compliance_gaps": gaps if gaps else ["None"],
            "omar_decision": decision
        }, indent=2)
    except Exception as e:
        return f"Error auditing GDPR: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 4: ESG, Labor & Supply Chain Compliance
# ─────────────────────────────────────────────────────────────
async def audit_esg_and_labor_compliance(
    vendor_name: str,
    industry: str,
    country: str,
    has_conflict_minerals_declaration: bool,
    has_reach_rohs_certification: bool,
    has_third_party_labor_audit: bool
) -> str:
    try:
        gaps = []
        HIGH_LABOR_RISK = ["China", "Bangladesh", "Myanmar", "Pakistan", "India", "Malaysia", "Congo"]
        HARDWARE_INDUSTRIES = ["electronics", "automotive", "hardware", "manufacturing", "semiconductors"]

        ind = industry.lower()

        if ind in HARDWARE_INDUSTRIES and not has_conflict_minerals_declaration:
            gaps.append("Dodd-Frank Section 1502: Missing Conflict Minerals (3TG) declaration. SEC violation risk.")

        if ind in HARDWARE_INDUSTRIES and not has_reach_rohs_certification:
            gaps.append("REACH/RoHS: Missing certification. Products cannot legally enter European markets.")

        if country in HIGH_LABOR_RISK and not has_third_party_labor_audit:
            gaps.append(f"ILO / Supply Chain Act: Operating in high-risk labor market ({country}) without third-party child/forced labor audit. Massive reputational & regulatory risk.")

        if gaps:
            status = "NON-COMPLIANT"
            decision = "CONDITIONAL — Resolve identified gaps before signing."
        else:
            status = "COMPLIANT"
            decision = "CLEAR — ESG and Labor standards met."

        return json.dumps({
            "vendor": vendor_name,
            "industry": industry,
            "country": country,
            "esg_labor_status": status,
            "compliance_gaps": gaps if gaps else ["None"],
            "omar_decision": decision
        }, indent=2)
    except Exception as e:
        return f"Error auditing ESG: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 5: Regulatory Fines Exposure Calculator
# ─────────────────────────────────────────────────────────────
async def calculate_regulatory_fines_exposure(
    company_global_revenue_usd: float,
    gdpr_violation_flag: bool,
    fcpa_violation_flag: bool,
    sanctions_violation_flag: bool,
    number_of_incidents: int = 1
) -> str:
    try:
        total_exposure = 0
        breakdown = {}

        if gdpr_violation_flag:
            gdpr_max = company_global_revenue_usd * 0.04
            total_exposure += gdpr_max
            breakdown["GDPR (Article 83 - up to 4% global revenue)"] = f"${gdpr_max:,.2f}"

        if fcpa_violation_flag:
            # FCPA fines can be up to 2x the gross pecuniary gain, plus $2M per violation for entities
            # We estimate a standard severe penalty base of $25M per incident for calculation context
            fcpa_est = 25_000_000 * number_of_incidents
            total_exposure += fcpa_est
            breakdown["FCPA (DOJ/SEC - estimate base + disgorgement)"] = f"~${fcpa_est:,.2f}"

        if sanctions_violation_flag:
            # OFAC civil penalties are ~ $350k per violation OR 2x transaction value
            # Assuming severe multi-transaction violation
            ofac_est = 5_000_000 * number_of_incidents
            total_exposure += ofac_est
            breakdown["OFAC Sanctions (Strict Liability civil/criminal)"] = f"~${ofac_est:,.2f}"

        if total_exposure == 0:
            return json.dumps({"status": "CLEAN", "total_exposure": "$0", "note": "No flagged regulatory violations."})

        return json.dumps({
            "total_statutory_exposure": f"${total_exposure:,.2f}",
            "exposure_breakdown": breakdown,
            "omar_insight": "These are maximum statutory exposures or historical averages. Fines of this magnitude also trigger stock drops and executive criminal liability. DO NOT PROCEED."
        }, indent=2)
    except Exception as e:
        return f"Error calculating fines: {str(e)}"
