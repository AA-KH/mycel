import json

HELENA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "benchmark_supplier_cost",
            "description": "Benchmarks a supplier's quoted price against global market averages for that product category. Returns variance %, cost rating, and renegotiation recommendation.",
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
    }
]

# Market benchmarks (USD per unit) by category
MARKET_BENCHMARKS = {
    "Electronics Components": 12.50,
    "Raw Steel": 0.85,
    "Logistics Services": 3.20,
    "Pharmaceuticals": 45.00,
    "Packaging Materials": 0.35,
    "Automotive Parts": 22.00,
    "Textiles": 4.80,
    "Chemical Raw Materials": 2.10,
    "Food Ingredients": 1.75,
    "IT Hardware": 180.00,
}

async def benchmark_supplier_cost(
    supplier_name: str,
    product_category: str,
    quoted_price_per_unit: float,
    volume_units_per_year: float
) -> str:
    try:
        # Find closest benchmark
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
            action = f"RENEGOTIATE immediately. Annual overpayment: ${annual_overpay:,.2f}. Target: ${benchmark:.2f}/unit."
        elif variance_pct > 8:
            rating = "ABOVE MARKET"
            action = f"Request price review. Estimated overpayment: ${annual_overpay:,.2f}/yr."
        elif variance_pct >= -5:
            rating = "MARKET RATE"
            action = "Pricing is competitive. Proceed with contract review."
        else:
            rating = "BELOW MARKET"
            action = "Favorable pricing. Verify quality standards before locking in long-term."

        return json.dumps({
            "supplier": supplier_name,
            "product_category": product_category,
            "quoted_price_per_unit": f"${quoted_price_per_unit:.2f}",
            "market_benchmark": f"${benchmark:.2f}",
            "variance": f"{variance_pct:+.1f}%",
            "annual_volume": int(volume_units_per_year),
            "annual_cost_impact": f"${abs(annual_overpay):,.2f} {'overpaid' if annual_overpay > 0 else 'saved'}",
            "cost_rating": rating,
            "helena_action": action
        }, indent=2)
    except Exception as e:
        return f"Error benchmarking cost: {str(e)}"
