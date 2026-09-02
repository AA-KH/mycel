import json
import aiohttp

# ─────────────────────────────────────────────────────────────
# TOOL SCHEMAS
# ─────────────────────────────────────────────────────────────
HELENA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "benchmark_supplier_cost",
            "description": "Benchmarks a supplier's quoted price against global market averages for that product category. Returns variance %, cost rating, and renegotiation recommendation with exact dollar impact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {"type": "string"},
                    "product_category": {"type": "string", "description": "e.g., 'Electronics Components', 'Raw Steel', 'Logistics Services'"},
                    "quoted_price_per_unit": {"type": "number", "description": "Supplier's quoted price per unit in USD."},
                    "volume_units_per_year": {"type": "number", "description": "Annual volume ordered from this supplier."}
                },
                "required": ["supplier_name", "product_category", "quoted_price_per_unit", "volume_units_per_year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_commodity_price",
            "description": "Fetches live global commodity prices from World Bank API. Use this FIRST when the product involves raw materials (steel, copper, oil, cotton, wheat, aluminum, etc.) to check if the supplier's quote is aligned with global spot prices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {
                        "type": "string",
                        "description": "Commodity name. Supported: 'steel', 'copper', 'aluminum', 'oil', 'cotton', 'wheat', 'corn', 'coal', 'gold', 'silver', 'rubber', 'sugar'"
                    }
                },
                "required": ["commodity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_total_cost_of_ownership",
            "description": "Calculates the TRUE Total Cost of Ownership (TCO) of a supplier, going beyond unit price to include logistics, quality failure costs, inventory carrying costs, and switching costs. Never evaluate a supplier on unit price alone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {"type": "string"},
                    "unit_price_usd": {"type": "number"},
                    "annual_volume_units": {"type": "number"},
                    "freight_cost_per_unit_usd": {"type": "number", "description": "Inbound logistics cost per unit."},
                    "defect_rate_pct": {"type": "number", "description": "Percentage of units that are defective or require rework."},
                    "rework_cost_per_unit_usd": {"type": "number", "description": "Cost to rework or return a defective unit."},
                    "avg_lead_time_days": {"type": "number", "description": "Average lead time in days (longer = higher inventory carrying cost)."},
                    "unit_holding_cost_per_day_usd": {"type": "number", "description": "Daily inventory carrying cost per unit held."},
                    "switching_cost_one_time_usd": {"type": "number", "description": "One-time cost to switch away from this supplier if needed.", "default": 0}
                },
                "required": ["supplier_name", "unit_price_usd", "annual_volume_units", "freight_cost_per_unit_usd",
                             "defect_rate_pct", "rework_cost_per_unit_usd", "avg_lead_time_days", "unit_holding_cost_per_day_usd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_spend_concentration",
            "description": "Performs a Pareto/spend concentration analysis. Identifies if too much spend is concentrated in too few suppliers (dangerous for negotiation leverage AND resilience).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Product/service category being analyzed."},
                    "total_category_spend_usd": {"type": "number", "description": "Total annual spend in this category."},
                    "supplier_spend_breakdown": {
                        "type": "array",
                        "description": "List of suppliers and their annual spend.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "supplier": {"type": "string"},
                                "spend_usd": {"type": "number"}
                            }
                        }
                    }
                },
                "required": ["category", "total_category_spend_usd", "supplier_spend_breakdown"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_payment_terms",
            "description": "Calculates the financial value of early payment discounts vs. extending Days Payable Outstanding (DPO). Identifies free cash flow opportunities hidden in payment terms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {"type": "string"},
                    "annual_spend_usd": {"type": "number"},
                    "current_payment_days": {"type": "integer", "description": "Current payment terms in days (e.g., 30 for Net 30)."},
                    "early_payment_discount_pct": {"type": "number", "description": "Discount % offered for early payment (e.g., 2.0 for 2/10 Net 30)."},
                    "early_payment_days": {"type": "integer", "description": "Days to pay to capture discount (e.g., 10 for 2/10 Net 30)."},
                    "cost_of_capital_pct": {"type": "number", "description": "Company's annual cost of capital/borrowing rate % (e.g., 8.0).", "default": 8.0}
                },
                "required": ["supplier_name", "annual_spend_usd", "current_payment_days",
                             "early_payment_discount_pct", "early_payment_days"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_supplier_quote_to_usd",
            "description": "Converts a supplier's quoted price from their local currency to USD using live Frankfurter exchange rates. Use this when comparing suppliers across different countries (e.g. China CNY vs Vietnam VND vs Germany EUR) for apples-to-apples TCO comparison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {"type": "string"},
                    "quoted_amount": {"type": "number", "description": "The quoted price in the supplier's local currency."},
                    "source_currency": {"type": "string", "description": "3-letter ISO currency code of supplier's currency (e.g., 'CNY', 'VND', 'EUR', 'MXN', 'INR')."}
                },
                "required": ["supplier_name", "quoted_amount", "source_currency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_country_inflation_risk",
            "description": "Checks a country's current inflation rate using World Bank data. Critical for evaluating long-term fixed-price contracts — high inflation means the supplier will break the contract or go bankrupt before the term ends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {"type": "string", "description": "World Bank 2-letter or 3-letter country code (e.g., 'CN' for China, 'VN' for Vietnam, 'BD' for Bangladesh, 'IN' for India, 'MX' for Mexico, 'DE' for Germany)."},
                    "country_name": {"type": "string", "description": "Human-readable country name for the report."},
                    "contract_duration_years": {"type": "integer", "description": "Duration of the proposed fixed-price contract in years."}
                },
                "required": ["country_code", "country_name", "contract_duration_years"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email_stakeholders",
            "description": "Emails the final strategic report to the executive stakeholders (CEO, Board of Directors). This MUST be the very last action you take before finishing your task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "report_body": {"type": "string", "description": "The full final report to be sent."}
                },
                "required": ["subject", "report_body"]
            }
        }
    }
]


# ─────────────────────────────────────────────────────────────
# COMMODITY CODE MAP for World Bank API
# ─────────────────────────────────────────────────────────────
COMMODITY_CODES = {
    "oil":       "CRUDE_PETRO",
    "coal":      "COAL_AUS",
    "copper":    "COPPER",
    "aluminum":  "ALUMINUM",
    "gold":      "GOLD",
    "silver":    "SILVER",
    "wheat":     "WHEAT_US_HRW",
    "corn":      "MAIZE_US",
    "cotton":    "COTTON_A_INDX",
    "rubber":    "RUBBER1_MYSG",
    "sugar":     "SUGAR_WLD",
    "steel":     "IRON_ORE",  # Iron ore as proxy for steel
}

# Market benchmarks (USD per unit) by category — used in benchmark_supplier_cost
MARKET_BENCHMARKS = {
    "Electronics Components": 12.50,
    "Raw Steel":              0.85,
    "Iron Ore":               0.12,
    "Logistics Services":     3.20,
    "Pharmaceuticals":        45.00,
    "Packaging Materials":    0.35,
    "Automotive Parts":       22.00,
    "Textiles":               4.80,
    "Chemical Raw Materials": 2.10,
    "Food Ingredients":       1.75,
    "IT Hardware":            180.00,
    "Copper":                 8.50,
    "Aluminum":               2.20,
}


# ─────────────────────────────────────────────────────────────
# TOOL 1: Benchmark Supplier Cost
# ─────────────────────────────────────────────────────────────
async def benchmark_supplier_cost(
    supplier_name: str,
    product_category: str,
    quoted_price_per_unit: float,
    volume_units_per_year: float
) -> str:
    try:
        benchmark = None
        for category, price in MARKET_BENCHMARKS.items():
            if any(word in product_category.lower() for word in category.lower().split()):
                benchmark = price
                break
        if benchmark is None:
            benchmark = quoted_price_per_unit * 0.85  # assume 15% above market if unknown

        variance_pct = ((quoted_price_per_unit - benchmark) / benchmark) * 100
        annual_overpay = (quoted_price_per_unit - benchmark) * volume_units_per_year

        if variance_pct > 20:
            rating = "OVERPRICED"
            action = f"RENEGOTIATE immediately. Annual dollar overpayment: ${abs(annual_overpay):,.2f}. Target: ${benchmark:.2f}/unit."
        elif variance_pct > 8:
            rating = "ABOVE MARKET"
            action = f"Request price review. Estimated overpayment: ${abs(annual_overpay):,.2f}/yr. Push back to ${benchmark * 1.05:.2f}/unit."
        elif variance_pct >= -5:
            rating = "MARKET RATE"
            action = "Pricing is competitive. Proceed with contract review."
        else:
            rating = "BELOW MARKET (Favorable)"
            action = f"Excellent pricing. Estimated saving vs. market: ${abs(annual_overpay):,.2f}/yr. Verify quality before long-term lock-in."

        return json.dumps({
            "supplier": supplier_name,
            "product_category": product_category,
            "quoted_price_per_unit": f"${quoted_price_per_unit:.2f}",
            "market_benchmark_per_unit": f"${benchmark:.2f}",
            "variance_vs_market": f"{variance_pct:+.1f}%",
            "annual_volume": int(volume_units_per_year),
            "annual_dollar_impact": f"${abs(annual_overpay):,.2f} {'OVERPAID' if annual_overpay > 0 else 'SAVED'}",
            "cost_rating": rating,
            "helena_action": action
        }, indent=2)
    except Exception as e:
        return f"Error benchmarking cost: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: Fetch Live Commodity Price (World Bank API — FREE, no key)
# ─────────────────────────────────────────────────────────────
async def fetch_commodity_price(commodity: str) -> str:
    """Fetches live commodity price from World Bank Commodity Price API."""
    try:
        commodity_key = commodity.lower().strip()
        indicator = COMMODITY_CODES.get(commodity_key)

        if not indicator:
            return json.dumps({
                "error": f"Commodity '{commodity}' not supported.",
                "supported": list(COMMODITY_CODES.keys())
            }, indent=2)

        url = f"https://api.worldbank.org/v2/en/indicator/{indicator}?downloadformat=json&mrv=1&format=json"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return f"World Bank API error: {response.status}"
                data = await response.json()

        # World Bank returns [metadata, [data_points]]
        records = data[1] if len(data) > 1 and data[1] else []
        if not records:
            return json.dumps({
                "commodity": commodity,
                "note": "No recent data returned from World Bank. Use industry benchmark instead.",
                "fallback_benchmark": MARKET_BENCHMARKS.get(commodity.title(), "Unknown")
            }, indent=2)

        latest = records[0]
        price_value = latest.get("value")
        period = latest.get("date", "Unknown")

        return json.dumps({
            "commodity": commodity.title(),
            "world_bank_indicator": indicator,
            "latest_price_usd": f"${price_value:.4f}" if price_value else "Data unavailable",
            "period": period,
            "source": "World Bank Commodity Price Data",
            "helena_insight": f"Use ${price_value:.4f} as the spot price anchor. Any supplier quoting >20% above this needs justification." if price_value else "Fallback to industry benchmark."
        }, indent=2)

    except Exception as e:
        return f"Error fetching commodity price: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 3: Calculate Total Cost of Ownership (TCO)
# ─────────────────────────────────────────────────────────────
async def calculate_total_cost_of_ownership(
    supplier_name: str,
    unit_price_usd: float,
    annual_volume_units: float,
    freight_cost_per_unit_usd: float,
    defect_rate_pct: float,
    rework_cost_per_unit_usd: float,
    avg_lead_time_days: float,
    unit_holding_cost_per_day_usd: float,
    switching_cost_one_time_usd: float = 0.0
) -> str:
    try:
        # Base purchase cost
        base_cost = unit_price_usd * annual_volume_units

        # Logistics cost
        logistics_cost = freight_cost_per_unit_usd * annual_volume_units

        # Quality failure cost (defective units × rework cost)
        defective_units = (defect_rate_pct / 100) * annual_volume_units
        quality_cost = defective_units * rework_cost_per_unit_usd

        # Inventory carrying cost (safety stock = lead time × avg daily demand)
        avg_daily_demand = annual_volume_units / 250  # 250 working days
        safety_stock_units = avg_lead_time_days * avg_daily_demand
        inventory_cost = safety_stock_units * unit_holding_cost_per_day_usd * 365

        # Total TCO
        total_tco = base_cost + logistics_cost + quality_cost + inventory_cost + switching_cost_one_time_usd
        tco_per_unit = total_tco / annual_volume_units if annual_volume_units > 0 else 0

        hidden_cost_pct = ((total_tco - base_cost) / base_cost * 100) if base_cost > 0 else 0

        breakdown = {
            "base_purchase_cost": f"${base_cost:,.2f}",
            "logistics_cost": f"${logistics_cost:,.2f}",
            "quality_failure_cost": f"${quality_cost:,.2f} ({defect_rate_pct}% defect × ${rework_cost_per_unit_usd}/unit)",
            "inventory_carrying_cost": f"${inventory_cost:,.2f} ({avg_lead_time_days}d lead time buffer)",
            "switching_cost_amortized": f"${switching_cost_one_time_usd:,.2f}",
            "TOTAL_TCO": f"${total_tco:,.2f}",
            "true_cost_per_unit": f"${tco_per_unit:.2f}",
            "hidden_cost_premium": f"{hidden_cost_pct:.1f}% above quoted unit price"
        }

        if hidden_cost_pct > 30:
            verdict = "HIGH HIDDEN COSTS — True cost is significantly above quoted price. Renegotiate freight, push supplier on quality SLAs."
        elif hidden_cost_pct > 15:
            verdict = "MODERATE HIDDEN COSTS — Factor TCO into contract. Negotiate quality guarantees and FOB terms."
        else:
            verdict = "TCO IS CLEAN — Hidden costs are acceptable. Unit price comparison is reliable."

        return json.dumps({
            "supplier": supplier_name,
            "tco_breakdown": breakdown,
            "tco_verdict": verdict,
            "helena_note": f"Quoted unit price was ${unit_price_usd:.2f}. True cost per unit is ${tco_per_unit:.2f} — a {hidden_cost_pct:.1f}% premium."
        }, indent=2)
    except Exception as e:
        return f"Error calculating TCO: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 4: Analyze Spend Concentration (Pareto)
# ─────────────────────────────────────────────────────────────
async def analyze_spend_concentration(
    category: str,
    total_category_spend_usd: float,
    supplier_spend_breakdown: list
) -> str:
    try:
        # Sort suppliers by spend descending
        sorted_suppliers = sorted(supplier_spend_breakdown, key=lambda x: x.get("spend_usd", 0), reverse=True)

        enriched = []
        cumulative = 0
        critical_vendors = []
        for s in sorted_suppliers:
            spend = s.get("spend_usd", 0)
            pct = (spend / total_category_spend_usd * 100) if total_category_spend_usd > 0 else 0
            cumulative += pct
            flag = "⚠️ CONCENTRATION RISK" if pct > 40 else ("🔶 MONITOR" if pct > 25 else "✅ OK")
            if pct > 40:
                critical_vendors.append(s.get("supplier", "Unknown"))
            enriched.append({
                "supplier": s.get("supplier"),
                "annual_spend": f"${spend:,.2f}",
                "category_share": f"{pct:.1f}%",
                "cumulative_share": f"{cumulative:.1f}%",
                "concentration_flag": flag
            })

        top1_pct = (sorted_suppliers[0].get("spend_usd", 0) / total_category_spend_usd * 100) if sorted_suppliers else 0
        top3_spend = sum(s.get("spend_usd", 0) for s in sorted_suppliers[:3])
        top3_pct = (top3_spend / total_category_spend_usd * 100) if total_category_spend_usd > 0 else 0

        if top1_pct > 40:
            risk_level = "CRITICAL"
            action = f"Single vendor ({sorted_suppliers[0].get('supplier')}) holds {top1_pct:.0f}% of spend. MANDATE dual-source qualification within 90 days."
        elif top3_pct > 80:
            risk_level = "HIGH"
            action = f"Top 3 vendors hold {top3_pct:.0f}% of spend. Limited negotiation leverage. Qualify 2 additional vendors."
        elif top3_pct > 60:
            risk_level = "MODERATE"
            action = "Spend is moderately concentrated. Monitor quarterly and build negotiation leverage through competitive bids."
        else:
            risk_level = "LOW"
            action = "Good diversification. Maintain current supplier mix and run annual competitive benchmarking."

        return json.dumps({
            "category": category,
            "total_category_spend": f"${total_category_spend_usd:,.2f}",
            "num_suppliers": len(sorted_suppliers),
            "top_supplier_share": f"{top1_pct:.1f}%",
            "top_3_suppliers_share": f"{top3_pct:.1f}%",
            "concentration_risk": risk_level,
            "critical_vendors": critical_vendors if critical_vendors else ["None"],
            "supplier_breakdown": enriched,
            "helena_action": action
        }, indent=2)
    except Exception as e:
        return f"Error analyzing spend concentration: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 5: Optimize Payment Terms
# ─────────────────────────────────────────────────────────────
async def optimize_payment_terms(
    supplier_name: str,
    annual_spend_usd: float,
    current_payment_days: int,
    early_payment_discount_pct: float,
    early_payment_days: int,
    cost_of_capital_pct: float = 8.0
) -> str:
    try:
        # Annualized cost of early payment discount
        days_saved = current_payment_days - early_payment_days
        annualized_discount_rate = (early_payment_discount_pct / 100) * (365 / days_saved) * 100

        # Dollar value of taking the discount
        annual_discount_saving = annual_spend_usd * (early_payment_discount_pct / 100)

        # Cost of capital to fund early payment (opportunity cost)
        capital_cost = annual_spend_usd * (cost_of_capital_pct / 100) * (days_saved / 365)

        # Net benefit
        net_benefit = annual_discount_saving - capital_cost

        if annualized_discount_rate > cost_of_capital_pct:
            verdict = f"TAKE THE DISCOUNT — Annualized return of {annualized_discount_rate:.1f}% far exceeds {cost_of_capital_pct:.1f}% cost of capital."
            action = f"Pay within {early_payment_days} days to capture ${annual_discount_saving:,.2f} annually."
        else:
            verdict = f"EXTEND DPO — Annualized return ({annualized_discount_rate:.1f}%) is below cost of capital ({cost_of_capital_pct:.1f}%). Hold cash longer."
            action = f"Negotiate to extend payment terms to {current_payment_days + 15} days to improve cash flow."

        return json.dumps({
            "supplier": supplier_name,
            "annual_spend": f"${annual_spend_usd:,.2f}",
            "current_terms": f"Net {current_payment_days}",
            "early_payment_offer": f"{early_payment_discount_pct}% discount if paid within {early_payment_days} days",
            "annualized_discount_return": f"{annualized_discount_rate:.1f}%",
            "annual_discount_saving": f"${annual_discount_saving:,.2f}",
            "cost_of_capital_for_early_pay": f"${capital_cost:,.2f}",
            "net_annual_benefit": f"${net_benefit:,.2f}",
            "verdict": verdict,
            "helena_action": action
        }, indent=2)
    except Exception as e:
        return f"Error optimizing payment terms: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 6: Cross-Currency Supplier Quote Converter (Frankfurter API)
# ─────────────────────────────────────────────────────────────
async def convert_supplier_quote_to_usd(supplier_name: str, quoted_amount: float, source_currency: str) -> str:
    """Converts supplier's local currency quote to USD using live Frankfurter exchange rates."""
    try:
        url = f"https://api.frankfurter.app/latest?amount={quoted_amount}&from={source_currency.upper()}&to=USD"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return f"Frankfurter API error {response.status}. Check currency code: '{source_currency}'." 
                data = await response.json()

        usd_amount = data.get("rates", {}).get("USD", 0.0)
        rate = usd_amount / quoted_amount if quoted_amount else 0

        return json.dumps({
            "supplier": supplier_name,
            "original_quote": f"{quoted_amount:,.4f} {source_currency.upper()}",
            "converted_to_usd": f"${usd_amount:,.4f}",
            "exchange_rate": f"1 {source_currency.upper()} = {rate:.6f} USD",
            "rate_date": data.get("date"),
            "source": "Frankfurter API (European Central Bank data)",
            "helena_insight": f"Use ${usd_amount:,.4f} USD as the comparable unit price for apples-to-apples TCO analysis against other suppliers."
        }, indent=2)
    except Exception as e:
        return f"Error converting currency: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 7: Country Inflation Risk Checker (World Bank API)
# ─────────────────────────────────────────────────────────────
async def check_country_inflation_risk(country_code: str, country_name: str, contract_duration_years: int) -> str:
    """Fetches country inflation rate from World Bank and assesses long-term contract risk."""
    try:
        # World Bank inflation indicator: FP.CPI.TOTL.ZG
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/FP.CPI.TOTL.ZG?format=json&mrv=3"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return f"World Bank API error: {response.status}"
                data = await response.json()

        records = data[1] if len(data) > 1 and data[1] else []
        # Get latest non-null value
        inflation_rate = None
        period = "Unknown"
        for record in records:
            if record.get("value") is not None:
                inflation_rate = record["value"]
                period = record.get("date", "Unknown")
                break

        if inflation_rate is None:
            return json.dumps({
                "country": country_name,
                "inflation_data": "Not available from World Bank",
                "helena_note": "Manually verify inflation before signing long-term contracts."
            }, indent=2)

        # Calculate compound price increase over contract duration
        compound_increase = ((1 + inflation_rate / 100) ** contract_duration_years - 1) * 100

        if inflation_rate > 15:
            risk = "CRITICAL"
            action = f"DO NOT sign fixed-price contract. At {inflation_rate:.1f}% inflation, supplier costs rise {compound_increase:.0f}% over {contract_duration_years} years. Mandate price escalation clauses tied to CPI."
        elif inflation_rate > 8:
            risk = "HIGH"
            action = f"Include annual price escalation clause capped at {min(inflation_rate * 0.7, 5):.1f}%. Without it, supplier will renegotiate under duress."
        elif inflation_rate > 4:
            risk = "MODERATE"
            action = f"Include a CPI-linked escalation clause for contracts >2 years. Projected cost increase: {compound_increase:.1f}% over {contract_duration_years} years."
        else:
            risk = "LOW"
            action = f"Inflation is stable ({inflation_rate:.1f}%). Fixed-price contract for {contract_duration_years} years is viable. Projected drift: {compound_increase:.1f}%."

        return json.dumps({
            "country": country_name,
            "latest_inflation_rate": f"{inflation_rate:.2f}%",
            "data_period": period,
            "source": "World Bank CPI Indicator (FP.CPI.TOTL.ZG)",
            "contract_duration_years": contract_duration_years,
            "projected_cost_increase_over_contract": f"{compound_increase:.1f}%",
            "inflation_risk": risk,
            "helena_action": action
        }, indent=2)
    except Exception as e:
        return f"Error checking inflation risk: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 8: Email Stakeholders (AMBER RISK - TRIGGERS ARMORIQ)
# ─────────────────────────────────────────────────────────────
async def email_stakeholders(subject: str, report_body: str) -> str:
    """Simulates sending an email to stakeholders. Triggers the ArmorIQ human-in-the-loop gate."""
    return f"SUCCESS: Email '{subject}' successfully dispatched to executive stakeholders."
