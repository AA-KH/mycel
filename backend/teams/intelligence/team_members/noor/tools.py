import logging
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

async def monitor_geopolitical_risk(region: str) -> str:
    """
    Uses Serper News API to scan for military, political, or trade embargo threats in a specific region.
    """
    logger.info(f"Monitoring geopolitical risk for: {region}")
    
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY is not set. Returning mock geopolitical data.")
        return f"[MOCK] Geopolitical risk in {region} is currently assessed as MODERATE."
        
    url = "https://google.serper.dev/news"
    headers = {
        'X-API-KEY': settings.serper_api_key,
        'Content-Type': 'application/json'
    }
    
    # Advanced Google Dorking: Targeted geopolitical threat hunting
    risk_query = f'"{region}" AND ("war" OR "conflict" OR "embargo" OR "sanctions" OR "military" OR "blockade" OR "piracy" OR "geopolitical")'
    payload = {"q": risk_query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            news = data.get("news", [])
            if not news:
                return f"GEOPOLITICAL RISK REPORT FOR '{region}': No major active conflicts, blockades, or sanctions detected in the recent news cycle."
                
            results = []
            for item in news[:4]: # Top 4 news items
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                date = item.get("date", "Unknown date")
                results.append(f"Date: {date} | Alert: {title}\nSummary: {snippet}\n")
                
            return f"🚨 GEOPOLITICAL THREATS DETECTED FOR '{region}' 🚨:\n" + "\n".join(results)
            
    except Exception as e:
        logger.error(f"Geopolitical risk analysis failed for '{region}': {e}")
        return f"Error executing geopolitical risk analysis: {e}"


async def analyze_environmental_disasters(region: str) -> str:
    """
    Uses Serper News API to scan for natural disasters, port closures, or extreme weather in a specific region.
    """
    logger.info(f"Analyzing environmental disasters for: {region}")
    
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY is not set. Returning mock environmental data.")
        return f"[MOCK] Environmental risk in {region} is currently assessed as LOW."
        
    url = "https://google.serper.dev/news"
    headers = {
        'X-API-KEY': settings.serper_api_key,
        'Content-Type': 'application/json'
    }
    
    # Advanced Google Dorking: Targeted environmental threat hunting
    disaster_query = f'"{region}" AND ("hurricane" OR "earthquake" OR "flood" OR "tsunami" OR "wildfire" OR "disaster" OR "port closure" OR "typhoon")'
    payload = {"q": disaster_query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            news = data.get("news", [])
            if not news:
                return f"ENVIRONMENTAL RISK REPORT FOR '{region}': No major natural disasters or port closures detected in the recent news cycle."
                
            results = []
            for item in news[:3]: # Top 3 news items
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                date = item.get("date", "Unknown date")
                results.append(f"Date: {date} | Alert: {title}\nSummary: {snippet}\n")
                
            return f"⚠️ ENVIRONMENTAL THREATS DETECTED FOR '{region}' ⚠️:\n" + "\n".join(results)
            
    except Exception as e:
        logger.error(f"Environmental risk analysis failed for '{region}': {e}")
        return f"Error executing environmental risk analysis: {e}"
