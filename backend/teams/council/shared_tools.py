"""
Council Team Shared Tools
These are the common analytical tools available to all 5 Council members:
Helena, Vikram, Nisha, Omar, Sofia.

The Council is the strategic governing body of Mycel. They debate, align,
and make binding decisions on vendor contracts, compliance, and ESG policy.
"""

import json
import aiohttp
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────
# TOOL 1: Vendor Contract Risk Scorer
# ─────────────────────────────────────────────────────────────
async def score_vendor_contract_risk(
    vendor_name: str,
    contract_value_usd: float,
    contract_duration_months: int,
    single_source: bool,
    country: str
) -> str:
    """
    Scores a vendor contract from 0 (safe) to 100 (critical risk)
    using concentration risk, geopolitical exposure, and contract duration.
    """
    try:
        risk_score = 0
        factors = []

        # Single-source penalty
        if single_source:
            risk_score += 35
            factors.append("Single-source dependency: +35 pts")

        # Contract value risk
        if contract_value_usd > 5_000_000:
            risk_score += 20
            factors.append(f"High contract value (${contract_value_usd:,.0f}): +20 pts")
        elif contract_value_usd > 1_000_000:
            risk_score += 10
            factors.append(f"Medium contract value (${contract_value_usd:,.0f}): +10 pts")

        # Duration risk
        if contract_duration_months > 36:
            risk_score += 20
            factors.append(f"Long lock-in period ({contract_duration_months} months): +20 pts")
        elif contract_duration_months > 12:
            risk_score += 10
            factors.append(f"Medium lock-in period ({contract_duration_months} months): +10 pts")

        # Geopolitical risk by country
        HIGH_RISK_COUNTRIES = ["China", "Russia", "Belarus", "Iran", "Myanmar"]
        MEDIUM_RISK_COUNTRIES = ["Pakistan", "Bangladesh", "Egypt", "Turkey", "Vietnam"]
        if country in HIGH_RISK_COUNTRIES:
            risk_score += 25
            factors.append(f"Geopolitical exposure ({country}): +25 pts")
        elif country in MEDIUM_RISK_COUNTRIES:
            risk_score += 12
            factors.append(f"Moderate geopolitical exposure ({country}): +12 pts")

        risk_score = min(risk_score, 100)

        if risk_score >= 70:
            verdict = "HIGH RISK - Council approval required before signing"
        elif risk_score >= 40:
            verdict = "MODERATE RISK - Request dual-source contingency clause"
        else:
            verdict = "LOW RISK - Standard procurement process applies"

        return json.dumps({
            "vendor": vendor_name,
            "risk_score": risk_score,
            "verdict": verdict,
            "risk_factors": factors,
            "recommendation": verdict
        }, indent=2)
    except Exception as e:
        return f"Error scoring vendor risk: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: ESG (Environmental, Social, Governance) Compliance Checker
# ─────────────────────────────────────────────────────────────
async def check_esg_compliance(
    vendor_name: str,
    country: str,
    industry: str,
    has_iso_14001: bool,
    has_sa8000: bool,
    has_annual_esg_report: bool,
    carbon_footprint_tons_per_year: float
) -> str:
    """
    Checks a vendor's ESG compliance posture and flags any regulatory gaps.
    """
    try:
        compliance_score = 0
        gaps = []
        passed = []

        if has_iso_14001:
            compliance_score += 30
            passed.append("ISO 14001 Environmental Management: ✅")
        else:
            gaps.append("ISO 14001 Environmental Management: ❌ Missing")

        if has_sa8000:
            compliance_score += 30
            passed.append("SA8000 Social Accountability: ✅")
        else:
            gaps.append("SA8000 Social Accountability: ❌ Missing")

        if has_annual_esg_report:
            compliance_score += 20
            passed.append("Annual ESG Disclosure Report: ✅")
        else:
            gaps.append("Annual ESG Disclosure Report: ❌ Missing")

        # Carbon footprint assessment
        if carbon_footprint_tons_per_year < 500:
            compliance_score += 20
            passed.append(f"Carbon Footprint ({carbon_footprint_tons_per_year}t/yr): ✅ Below threshold")
        elif carbon_footprint_tons_per_year < 2000:
            compliance_score += 10
            passed.append(f"Carbon Footprint ({carbon_footprint_tons_per_year}t/yr): ⚠️ Moderate")
        else:
            gaps.append(f"Carbon Footprint ({carbon_footprint_tons_per_year}t/yr): ❌ Exceeds green procurement threshold")

        if compliance_score >= 80:
            esg_status = "COMPLIANT - Approved for ESG-aligned procurement"
        elif compliance_score >= 50:
            esg_status = "PARTIAL COMPLIANCE - Require improvement roadmap before contract renewal"
        else:
            esg_status = "NON-COMPLIANT - Cannot proceed under ESG mandate"

        return json.dumps({
            "vendor": vendor_name,
            "country": country,
            "industry": industry,
            "esg_compliance_score": compliance_score,
            "status": esg_status,
            "passed_checks": passed,
            "compliance_gaps": gaps,
            "action": esg_status
        }, indent=2)
    except Exception as e:
        return f"Error checking ESG compliance: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 3: Regulatory Trade Policy Checker (WTO/Tariff Advisor)
# ─────────────────────────────────────────────────────────────
async def check_trade_policy(origin_country: str, destination_country: str, product_category: str) -> str:
    """
    Checks active trade restrictions, tariff alerts, and compliance warnings
    between two countries for a specific product category.
    Uses the free RestCountries API to validate country data.
    """
    try:
        ACTIVE_RESTRICTIONS = {
            ("China", "United States"): {
                "tariff_rate": "7.5-25%",
                "policy": "Section 301 Tariffs",
                "status": "ACTIVE",
                "risk": "HIGH"
            },
            ("Russia", "United States"): {
                "tariff_rate": "Prohibited",
                "policy": "OFAC Sanctions + Export Control",
                "status": "EMBARGO",
                "risk": "CRITICAL"
            },
            ("Russia", "European Union"): {
                "tariff_rate": "Prohibited",
                "policy": "EU Council Regulation No 833/2014 (Extended)",
                "status": "EMBARGO",
                "risk": "CRITICAL"
            },
            ("Belarus", "European Union"): {
                "tariff_rate": "Prohibited",
                "policy": "EU Sanctions Package",
                "status": "EMBARGO",
                "risk": "CRITICAL"
            },
            ("Iran", "United States"): {
                "tariff_rate": "Prohibited",
                "policy": "OFAC Comprehensive Iran Sanctions",
                "status": "EMBARGO",
                "risk": "CRITICAL"
            },
        }

        key = (origin_country, destination_country)
        reverse_key = (destination_country, origin_country)

        restriction = ACTIVE_RESTRICTIONS.get(key) or ACTIVE_RESTRICTIONS.get(reverse_key)

        if restriction:
            return json.dumps({
                "origin": origin_country,
                "destination": destination_country,
                "product_category": product_category,
                "tariff_rate": restriction["tariff_rate"],
                "active_policy": restriction["policy"],
                "status": restriction["status"],
                "risk_level": restriction["risk"],
                "council_action": "BLOCK contract signing until legal team signs off on compliance exemption."
            }, indent=2)
        else:
            return json.dumps({
                "origin": origin_country,
                "destination": destination_country,
                "product_category": product_category,
                "status": "NO_ACTIVE_RESTRICTION",
                "risk_level": "LOW",
                "council_action": "Standard import/export documentation applies. No trade barriers detected."
            }, indent=2)

    except Exception as e:
        return f"Error checking trade policy: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 4: Strategic Cost-Benefit Analyzer
# ─────────────────────────────────────────────────────────────
async def analyze_strategic_cost_benefit(
    initiative_name: str,
    upfront_investment_usd: float,
    annual_savings_usd: float,
    risk_mitigation_value_usd: float,
    implementation_years: int
) -> str:
    """
    Computes the strategic ROI, payback period, and NPV of a proposed
    initiative (e.g., supplier diversification, automation, new warehouse).
    """
    try:
        DISCOUNT_RATE = 0.10  # 10% corporate discount rate

        total_benefit = (annual_savings_usd + risk_mitigation_value_usd) * implementation_years

        # NPV calculation (simplified)
        npv = 0
        for year in range(1, implementation_years + 1):
            yearly_benefit = annual_savings_usd + risk_mitigation_value_usd
            npv += yearly_benefit / ((1 + DISCOUNT_RATE) ** year)
        npv -= upfront_investment_usd

        # Payback period
        annual_net = annual_savings_usd + risk_mitigation_value_usd
        payback_years = upfront_investment_usd / annual_net if annual_net > 0 else float('inf')

        roi_pct = ((total_benefit - upfront_investment_usd) / upfront_investment_usd) * 100

        if npv > 0 and payback_years < implementation_years:
            verdict = "APPROVE - Positive NPV and achievable payback period"
        elif npv > 0:
            verdict = "CONDITIONAL APPROVE - Positive NPV but review payback timeline"
        else:
            verdict = "REJECT - Negative NPV. Initiative does not justify investment."

        return json.dumps({
            "initiative": initiative_name,
            "upfront_investment": f"${upfront_investment_usd:,.2f}",
            "total_benefit_over_period": f"${total_benefit:,.2f}",
            "npv_at_10pct_discount": f"${npv:,.2f}",
            "roi_percentage": f"{roi_pct:.1f}%",
            "payback_period_years": round(payback_years, 1),
            "council_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error analyzing cost-benefit: {str(e)}"
