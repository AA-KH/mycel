import httpx
import logging
from core.config import settings

logger = logging.getLogger(__name__)

async def web_search(query: str) -> str:
    """
    Performs a web search using the Serper (Google Search) API.
    Returns a summarized text string of the top results.
    """
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY is not set. Returning mock data.")
        return f"[MOCK SEARCH RESULT] Found 3 articles about '{query}'. Trend is highly volatile."
        
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': settings.serper_api_key,
        'Content-Type': 'application/json'
    }
    payload = {"q": query}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Extract organic results
            organic = data.get("organic", [])
            if not organic:
                return "No search results found."
                
            results = []
            for item in organic[:5]: # Top 5 results
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                results.append(f"Title: {title}\nSnippet: {snippet}\nSource: {link}\n")
                
            return "\n".join(results)
    except Exception as e:
        logger.error(f"Web search failed for query '{query}': {e}")
        return f"Error executing web search: {e}"

async def web_scrape(url: str) -> str:
    """
    Scrapes a webpage using Firecrawl API.
    Returns the clean markdown content of the page.
    """
    if not settings.firecrawl_api_key:
        logger.warning("FIRECRAWL_API_KEY is not set. Returning mock data.")
        return f"[MOCK SCRAPE RESULT] Content of {url}:\n# Analysis Report\nMarket is showing 15% growth."
        
    endpoint = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        'Authorization': f'Bearer {settings.firecrawl_api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        "url": url,
        "formats": ["markdown"]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                markdown = data.get("data", {}).get("markdown", "")
                return markdown[:5000] # Limit to 5000 chars to save LLM tokens
            else:
                return f"Scrape failed: {data.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Web scrape failed for URL '{url}': {e}")
        return f"Error executing web scrape: {e}"
