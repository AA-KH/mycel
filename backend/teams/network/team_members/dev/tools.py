import logging
import json
import requests

logger = logging.getLogger(__name__)

# --- SCHEMAS ---
DEV_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_total_landed_cost",
            "description": "Calculates the Total Landed Cost (TLC) and cost per unit for a shipment. This includes unit costs, freight, customs/duties, insurance, and overheads.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_cost": {
                        "type": "number",
                        "description": "Base cost of a single unit."
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Total number of units being shipped."
                    },
                    "freight_cost": {
                        "type": "number",
                        "description": "Total cost of shipping/freight for the entire order."
                    },
                    "customs_percent": {
                        "type": "number",
                        "description": "Customs duty or tariff as a percentage (e.g., 5.5 for 5.5%)."
                    },
                    "insurance_percent": {
                        "type": "number",
                        "description": "Insurance cost as a percentage of the total goods value (e.g., 1.5 for 1.5%)."
                    },
                    "overhead_cost": {
                        "type": "number",
                        "description": "Any additional fixed overhead or handling costs per shipment."
                    }
                },
                "required": ["unit_cost", "quantity", "freight_cost", "customs_percent", "insurance_percent", "overhead_cost"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_live_currency_exchange",
            "description": "Fetches the real-time currency exchange rate using the Frankfurter API (European Central Bank). Note: Frankfurter does not support some minor currencies, but supports major ones like USD, EUR, GBP, JPY, AUD, CAD, CHF, CNY, SEK, NZD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "description": "3-letter currency code to convert from (e.g., 'CNY', 'EUR', 'GBP'). Use 'USD' if converting to something else."
                    },
                    "target_currency": {
                        "type": "string",
                        "description": "3-letter currency code to convert to (e.g., 'USD')."
                    },
                    "amount": {
                        "type": "number",
                        "description": "The amount in the base currency to convert."
                    }
                },
                "required": ["base_currency", "target_currency", "amount"]
            }
        }
    }
]

# --- IMPLEMENTATIONS ---

async def calculate_total_landed_cost(unit_cost: float, quantity: int, freight_cost: float, customs_percent: float, insurance_percent: float, overhead_cost: float) -> str:
    """
    Calculates the Total Landed Cost (TLC) of a shipment.
    """
    try:
        if quantity <= 0:
            return "Error: Quantity must be greater than zero."
            
        total_goods_value = unit_cost * quantity
        
        # Calculate Duty based on goods value (sometimes duty includes freight, but we'll stick to standard FOB value for simplicity)
        customs_cost = total_goods_value * (customs_percent / 100.0)
        
        # Calculate Insurance based on goods value
        insurance_cost = total_goods_value * (insurance_percent / 100.0)
        
        # Total Landed Cost
        tlc = total_goods_value + freight_cost + customs_cost + insurance_cost + overhead_cost
        
        # Cost per unit
        landed_cost_per_unit = tlc / quantity
        
        # Increase from base cost
        cost_increase_percent = ((landed_cost_per_unit - unit_cost) / unit_cost) * 100.0 if unit_cost > 0 else 0
        
        result = {
            "breakdown": {
                "goods_value": round(total_goods_value, 2),
                "freight": round(freight_cost, 2),
                "customs_duty": round(customs_cost, 2),
                "insurance": round(insurance_cost, 2),
                "overheads": round(overhead_cost, 2)
            },
            "totals": {
                "total_landed_cost": round(tlc, 2),
                "base_unit_cost": round(unit_cost, 2),
                "landed_cost_per_unit": round(landed_cost_per_unit, 2),
                "hidden_cost_markup_percent": round(cost_increase_percent, 2)
            },
            "insight": f"The hidden costs (freight, duties, insurance, overhead) added {round(cost_increase_percent, 2)}% to the base unit cost."
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error calculating landed cost: {str(e)}"

async def get_live_currency_exchange(base_currency: str, target_currency: str, amount: float) -> str:
    """
    Fetches real-time exchange rates from the Frankfurter API.
    """
    try:
        base = base_currency.upper()
        target = target_currency.upper()
        
        if base == target:
            return json.dumps({
                "base": base,
                "target": target,
                "rate": 1.0,
                "original_amount": amount,
                "converted_amount": amount
            }, indent=2)
            
        # Frankfurter API URL
        url = f"https://api.frankfurter.app/latest?amount={amount}&from={base}&to={target}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            converted = data.get("rates", {}).get(target)
            
            if converted:
                rate = converted / amount if amount > 0 else 0
                result = {
                    "base": base,
                    "target": target,
                    "rate": round(rate, 4),
                    "original_amount": round(amount, 2),
                    "converted_amount": round(converted, 2),
                    "date": data.get("date")
                }
                return json.dumps(result, indent=2)
            else:
                return f"Error: Target currency '{target}' not found in response."
        elif response.status_code == 404:
            return f"Error: Currency '{base}' or '{target}' might not be supported by Frankfurter API. (Note: Only ECB major currencies are supported)."
        else:
            return f"Error fetching exchange rate. Status code: {response.status_code}"
            
    except Exception as e:
        return f"Error fetching currency exchange data: {str(e)}"
