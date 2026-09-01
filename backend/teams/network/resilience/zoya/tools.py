import logging
import json
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

ZOYA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_global_news",
            "description": "Searches Google News for live breaking events, port strikes, canal blockages, or natural disasters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'Suez Canal blocked', 'Port of LA strike', 'Taiwan semiconductor fire')."
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days back to search for news."
                    }
                },
                "required": ["query", "days_back"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_supplier_financial_health",
            "description": "Analyzes the credit risk and bankruptcy probability of a supplier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "Name of the supplier company."
                    }
                },
                "required": ["supplier_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_geopolitical_risk",
            "description": "Evaluates the current geopolitical risk level for a specific country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "The 2-letter country code (e.g., 'TW', 'CN', 'US', 'UA')."
                    }
                },
                "required": ["country_code"]
            }
        }
    }
]

async def search_global_news(query: str, days_back: int) -> str:
    """Uses Serper.dev API to fetch live news."""
    try:
        api_key = settings.serper_api_key
        if not api_key or api_key == "your_serper_key_here":
            return json.dumps({
                "status": "warning",
                "message": f"Serper API key not configured. Mocking news for query: {query}",
                "articles": [
                    {"title": f"Mock Alert: Disruption reported relating to {query}", "snippet": "Unconfirmed reports suggest operations are halted."}
                ]
            })

        url = "https://google.serper.dev/news"
        payload = json.dumps({
            "q": query,
            "tbs": f"qdr:d{days_back}"
        })
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=payload)
            
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get("news", [])[:3] # Return top 3
            result = []
            for art in articles:
                result.append({
                    "title": art.get("title"),
                    "snippet": art.get("snippet"),
                    "date": art.get("date")
                })
            return json.dumps({"status": "success", "articles": result}, indent=2)
        else:
            return f"Error: Failed to fetch news. Status Code {response.status_code}"
    except Exception as e:
        return f"Error searching news: {str(e)}"

async def check_supplier_financial_health(supplier_name: str) -> str:
    """Simulates checking financial risk databases for supplier bankruptcy."""
    try:
        # Mock logic based on keyword to simulate live financial DB lookup
        name_lower = supplier_name.lower()
        
        if "evergrande" in name_lower or "bankrupt" in name_lower:
            risk = "CRITICAL"
            z_score = 1.1
            insight = f"{supplier_name} is in severe distress (Altman Z-Score < 1.8). High risk of immediate insolvency."
        elif "startup" in name_lower:
            risk = "HIGH"
            z_score = 2.0
            insight = f"{supplier_name} shows high cash-burn rate. Financials are unstable."
        else:
            risk = "LOW"
            z_score = 3.5
            insight = f"{supplier_name} appears financially stable with strong cash reserves."
            
        return json.dumps({
            "supplier": supplier_name,
            "altman_z_score": z_score,
            "bankruptcy_risk_level": risk,
            "insight": insight
        }, indent=2)
    except Exception as e:
        return f"Error checking financial health: {str(e)}"

async def analyze_geopolitical_risk(country_code: str) -> str:
    """Evaluates country-level geopolitical risks."""
    try:
        code = country_code.upper()
        # Simulated risk index based on macro geopolitical climate
        risk_map = {
            "TW": {"risk": "HIGH", "factors": ["Tensions in Taiwan Strait", "Semiconductor export controls"]},
            "UA": {"risk": "CRITICAL", "factors": ["Active conflict zone", "Infrastructure damage"]},
            "RU": {"risk": "CRITICAL", "factors": ["International sanctions", "SWIFT ban"]},
            "CN": {"risk": "MEDIUM", "factors": ["Tariffs", "Trade policy shifts"]},
            "IL": {"risk": "HIGH", "factors": ["Regional conflict", "Red Sea shipping diversions"]},
            "US": {"risk": "LOW", "factors": ["Stable institutions, but watch for domestic port strikes"]},
            "DE": {"risk": "LOW", "factors": ["Stable EU member, energy prices normalized"]}
        }
        
        data = risk_map.get(code, {"risk": "UNKNOWN", "factors": ["No specific alerts in database"]})
        
        return json.dumps({
            "country": code,
            "geopolitical_risk_level": data["risk"],
            "key_factors": data["factors"]
        }, indent=2)
    except Exception as e:
        return f"Error checking geopolitical risk: {str(e)}"
