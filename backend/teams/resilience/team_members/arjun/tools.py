import json

ARJUN_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_recovery_plan",
            "description": "Formalizes the financial and operational recovery strategy into a Business Continuity Plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_name": {
                        "type": "string",
                        "description": "Name of the disruption (e.g., 'Port of LA Strike')."
                    },
                    "alternative_suppliers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of alternate suppliers to activate."
                    },
                    "freight_mode": {
                        "type": "string",
                        "description": "Emergency freight mode (e.g., 'Air Charter')."
                    },
                    "total_mitigation_cost": {
                        "type": "number",
                        "description": "Total cost of the emergency mitigation."
                    },
                    "financial_loss_prevented": {
                        "type": "number",
                        "description": "Total revenue saved by executing this plan."
                    }
                },
                "required": ["incident_name", "total_mitigation_cost", "financial_loss_prevented"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_live_exchange_rate",
            "description": "Fetches live currency exchange rates to calculate cross-border mitigation costs accurately in USD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "description": "The 3-letter currency code to convert from (e.g., 'CNY', 'MXN', 'EUR')."
                    },
                    "target_currency": {
                        "type": "string",
                        "description": "The 3-letter currency code to convert to (e.g., 'USD'). Default is 'USD'."
                    },
                    "amount": {
                        "type": "number",
                        "description": "The amount to convert."
                    }
                },
                "required": ["base_currency", "amount"]
            }
        }
    }
]

import aiohttp

async def generate_recovery_plan(incident_name: str, alternative_suppliers: list, freight_mode: str, total_mitigation_cost: float, financial_loss_prevented: float) -> str:
    """Formalizes the final BCP report."""
    try:
        roi = financial_loss_prevented - total_mitigation_cost
        status = "APPROVED_BY_SYSTEM" if roi > 0 else "REJECTED_NEGATIVE_ROI"
        
        return json.dumps({
            "bcp_id": f"BCP-{incident_name.upper().replace(' ', '-')}",
            "incident": incident_name,
            "operational_shifts": {
                "activate_suppliers": alternative_suppliers if alternative_suppliers else ["None required"],
                "emergency_freight": freight_mode if freight_mode else "Standard"
            },
            "financial_summary": {
                "mitigation_investment": f"${total_mitigation_cost:,.2f}",
                "loss_prevented": f"${financial_loss_prevented:,.2f}",
                "net_savings": f"${roi:,.2f}"
            },
            "execution_status": status,
            "insight": "Present this summarized Business Continuity Plan to the management for final sign-off."
        }, indent=2)
    except Exception as e:
        return f"Error generating recovery plan: {str(e)}"

async def fetch_live_exchange_rate(base_currency: str, amount: float, target_currency: str = "USD") -> str:
    """Fetches real-time exchange rate from Frankfurter API."""
    try:
        url = f"https://api.frankfurter.app/latest?amount={amount}&from={base_currency}&to={target_currency}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return f"Error: Frankfurter API returned {response.status}. Make sure currency codes are valid."
                data = await response.json()
                
        converted_amount = data.get("rates", {}).get(target_currency, 0.0)
        return json.dumps({
            "source_amount": f"{amount} {base_currency}",
            "converted_amount": f"{converted_amount} {target_currency}",
            "exchange_rate_date": data.get("date"),
            "insight": f"Use this {target_currency} value to accurately compare mitigation costs across different countries."
        }, indent=2)
    except Exception as e:
        return f"Error fetching exchange rate: {str(e)}"
