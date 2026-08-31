import logging
import asyncio
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

async def fetch_competitor_metrics(ticker: str) -> str:
    """
    Fetches real-world financial metrics (Gross Margins, Revenue) for a competitor using yfinance.
    Ticker should be a valid Yahoo Finance ticker (e.g., 'AAPL', 'TSLA').
    """
    logger.info(f"Fetching financial metrics for competitor: {ticker}")
    
    def _fetch():
        try:
            import yfinance as yf
            company = yf.Ticker(ticker)
            info = company.info
            
            if not info or 'shortName' not in info:
                return f"No financial data found for ticker '{ticker}'."
                
            name = info.get('shortName', ticker)
            gross_margin = info.get('grossMargins', 'N/A')
            operating_margin = info.get('operatingMargins', 'N/A')
            revenue_growth = info.get('revenueGrowth', 'N/A')
            ebitda = info.get('ebitda', 'N/A')
            
            # Format percentages
            def format_pct(val):
                return f"{val * 100:.2f}%" if isinstance(val, (float, int)) else str(val)
                
            report = (
                f"FINANCIAL & EFFICIENCY METRICS FOR {name} ({ticker}):\n"
                f"- Gross Margin: {format_pct(gross_margin)}\n"
                f"- Operating Margin: {format_pct(operating_margin)}\n"
                f"- Revenue Growth: {format_pct(revenue_growth)}\n"
                f"- EBITDA: {ebitda}\n"
                "Use this data to benchmark if their supply chain is actually highly efficient or struggling financially."
            )
            return report
            
        except ImportError:
            return f"BENCHMARK DATA FOR '{ticker}': yfinance not installed. Mocking -> Gross Margin: 35%."
        except Exception as e:
            logger.error(f"yfinance failed for {ticker}: {e}")
            return f"BENCHMARK DATA FOR '{ticker}': Error fetching data ({str(e)}). Could be a private company."

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch)

async def analyze_industry_trends(industry: str) -> str:
    """
    Uses Serper API to search for high-level consulting reports (McKinsey, Gartner, etc.) 
    to determine true industry supply chain standards.
    """
    logger.info(f"Analyzing industry trends for: {industry}")
    
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY is not set. Returning mock consulting data.")
        return f"[MOCK] Consulting reports suggest a 20% shift towards nearshoring in the {industry} sector."
        
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': settings.serper_api_key,
        'Content-Type': 'application/json'
    }
    
    # Advanced Google Dorking: Force search on top consulting firms
    dork_query = f"{industry} supply chain benchmark report site:mckinsey.com OR site:gartner.com OR site:bain.com OR site:deloitte.com"
    payload = {"q": dork_query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            organic = data.get("organic", [])
            if not organic:
                return f"No direct top-tier consulting reports found for '{industry}'."
                
            results = []
            for item in organic[:3]: # Top 3 reports
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                results.append(f"Report: {title}\nKey Insight: {snippet}\n")
                
            return f"CONSULTING-GRADE INDUSTRY STANDARDS FOR '{industry}':\n" + "\n".join(results)
            
    except Exception as e:
        logger.error(f"Industry trend search failed for '{industry}': {e}")
        return f"Error executing industry trend query: {e}"
