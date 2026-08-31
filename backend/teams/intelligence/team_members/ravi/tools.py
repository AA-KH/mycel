import logging
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

async def query_supplier_database(material: str) -> str:
    """
    Simulates querying a global supply chain database by using Serper API 
    with Advanced Google Dorking on top B2B directories.
    """
    logger.info(f"Querying global supplier database (Serper API) for: {material}")
    
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY is not set. Returning mock supplier data.")
        return f"[MOCK] 1. AcmeCorp (USA) - $10/kg\n2. GlobalSupply (Asia) - $8/kg"
        
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': settings.serper_api_key,
        'Content-Type': 'application/json'
    }
    
    # Advanced Google Dorking: Force search on verified B2B platforms
    dork_query = f"top {material} manufacturers suppliers site:thomasnet.com OR site:alibaba.com OR site:kompass.com OR site:indiamart.com"
    payload = {"q": dork_query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            organic = data.get("organic", [])
            if not organic:
                return f"No direct supplier profiles found for '{material}' on major B2B directories."
                
            results = []
            for item in organic[:5]: # Top 5 B2B profiles
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                results.append(f"Supplier Profile: {title}\nSnippet: {snippet}\nLink: {link}\n")
                
            return f"SUPPLIER DATABASE RESULTS FOR '{material}':\n" + "\n".join(results)
            
    except Exception as e:
        logger.error(f"Supplier database search failed for '{material}': {e}")
        return f"Error executing supplier query: {e}"

async def analyze_supplier_risk(supplier_name: str) -> str:
    """
    Checks a specific supplier for ESG violations, labor strikes, 
    financial instability, or recent factory fires using Serper News API.
    """
    logger.info(f"Analyzing risk (Serper News API) for supplier: {supplier_name}")
    
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY is not set. Returning mock risk data.")
        return f"[MOCK] No observable risk found for {supplier_name}."
        
    url = "https://google.serper.dev/news"
    headers = {
        'X-API-KEY': settings.serper_api_key,
        'Content-Type': 'application/json'
    }
    
    # Targeted negative news hunting
    risk_query = f'"{supplier_name}" AND ("lawsuit" OR "strike" OR "bankruptcy" OR "fire" OR "violation" OR "scandal" OR "shortage" OR "tariff" OR "forced labor")'
    payload = {"q": risk_query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            news = data.get("news", [])
            if not news:
                return f"RISK REPORT FOR '{supplier_name}': Low observable risk. No recent negative news, lawsuits, or supply chain disruptions found."
                
            results = []
            for item in news[:3]: # Top 3 worst news
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                date = item.get("date", "Unknown date")
                results.append(f"Date: {date} | Alert: {title}\nSummary: {snippet}\n")
                
            return f"🚨 HIGH RISK DETECTED FOR '{supplier_name}' 🚨:\n" + "\n".join(results)
            
    except Exception as e:
        logger.error(f"Risk analysis failed for '{supplier_name}': {e}")
        return f"Error executing risk analysis: {e}"
