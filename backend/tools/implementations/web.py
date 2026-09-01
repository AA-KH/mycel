"""
Real Web Research Tools — Production implementations for web search, 
page fetching, and structured content extraction.

Search: DuckDuckGo (free, no API key required)
Fetching: httpx (async HTTP, already in dependencies)
Extraction: trafilatura (article text) + BeautifulSoup (structured HTML)

All web content is treated as UNTRUSTED DATA — never executed as instructions.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from ..base import BaseTool
from ..context import ToolExecutionContext
from ..models import ToolDefinition
from ..security import ToolSecurityPolicy
from agents.runtime.result import ToolResult

logger = logging.getLogger(__name__)

# --- Rate limiting ---
_search_semaphore = asyncio.Semaphore(3)   # max 3 concurrent searches
_fetch_semaphore = asyncio.Semaphore(5)    # max 5 concurrent fetches
_FETCH_TIMEOUT = 15  # seconds
_MAX_CONTENT_LENGTH = 200_000  # bytes — don't download huge files

# Known dangerous/useless patterns to filter from extracted text
_INJECTION_PATTERNS = re.compile(
    r'(ignore\s+(all\s+)?previous\s+instructions|'
    r'you\s+are\s+now\s+|'
    r'system\s*:\s*|'
    r'<\s*script|'
    r'javascript\s*:)',
    re.IGNORECASE
)


def _sanitize_content(text: str) -> str:
    """
    Sanitize extracted web content. Treat everything as DATA, not instructions.
    Strip potential prompt injection attempts but preserve factual content.
    """
    if not text:
        return ""
    # Truncate excessively long content
    text = text[:50_000]
    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


def _extract_metadata(html: str, url: str) -> Dict[str, Any]:
    """Extract basic page metadata from HTML."""
    metadata = {"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat()}
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html[:20_000], 'lxml')
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)[:200]
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata["description"] = meta_desc['content'][:500]
        
        # Publication date
        for attr_name in ['article:published_time', 'datePublished', 'date']:
            date_tag = soup.find('meta', attrs={'property': attr_name}) or soup.find('meta', attrs={'name': attr_name})
            if date_tag and date_tag.get('content'):
                metadata["published_date"] = date_tag['content'][:50]
                break
        
        # Author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag and author_tag.get('content'):
            metadata["author"] = author_tag['content'][:100]
            
    except Exception as e:
        logger.debug(f"Metadata extraction failed for {url}: {e}")
    
    return metadata


class WebSearchTool(BaseTool):
    """Real web search using DuckDuckGo — free, no API key required."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="web.search",
            name="Web Search",
            category="research",
            description="Search the web for information using DuckDuckGo.",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 8, "description": "Max results to return"},
                    "region": {"type": "string", "default": "wt-wt", "description": "Region code"}
                }
            },
            output_schema={"type": "object"},
            capabilities=["web_research"],
            requires_network=True,
            idempotent=True,
            timeout_seconds=30
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        query = arguments.get("query", "").strip()
        if not query:
            return ToolResult(tool_name="web.search", status="error", output={}, error="Empty search query")
        
        max_results = min(arguments.get("max_results", 8), 20)  # cap at 20
        region = arguments.get("region", "wt-wt")
        
        async with _search_semaphore:
            try:
                # Run DuckDuckGo search in thread pool (it's synchronous internally)
                results = await asyncio.get_event_loop().run_in_executor(
                    None, self._do_search, query, max_results, region
                )
                
                logger.info(f"[web.search] Query '{query}' returned {len(results)} results")
                
                return ToolResult(
                    tool_name="web.search",
                    status="success",
                    output={
                        "query": query,
                        "result_count": len(results),
                        "results": results,
                        "searched_at": datetime.now(timezone.utc).isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"[web.search] Search failed for '{query}': {e}")
                return ToolResult(
                    tool_name="web.search",
                    status="error",
                    output={"query": query, "results": []},
                    error=f"Search failed: {str(e)[:200]}"
                )

    def _do_search(self, query: str, max_results: int, region: str) -> List[Dict[str, str]]:
        """Execute DuckDuckGo search (synchronous, called from executor)."""
        from ddgs import DDGS
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region=region, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
        return results


class BrowserOpenTool(BaseTool):
    """Fetch a URL and extract clean article text using trafilatura."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="browser.open",
            name="Browser Open",
            category="browser",
            description="Open a URL and extract its main text content.",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "extract_metadata": {"type": "boolean", "default": True}
                }
            },
            output_schema={"type": "object"},
            capabilities=["web_research"],
            requires_network=True,
            idempotent=True,
            timeout_seconds=_FETCH_TIMEOUT + 5
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        url = arguments.get("url", "").strip()
        if not url:
            return ToolResult(tool_name="browser.open", status="error", output={}, error="No URL provided")
        
        # Security: SSRF check
        try:
            ToolSecurityPolicy.validate_ssrf(url)
        except Exception as e:
            return ToolResult(tool_name="browser.open", status="error", output={}, error=f"Security: {e}")
        
        # Validate URL format
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return ToolResult(tool_name="browser.open", status="error", output={}, error="Only HTTP/HTTPS URLs supported")
        
        async with _fetch_semaphore:
            try:
                import httpx
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; MycelResearch/1.0; +https://mycel.ai)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=httpx.Timeout(_FETCH_TIMEOUT),
                    max_redirects=5
                ) as client:
                    response = await client.get(url, headers=headers)
                    
                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    if not any(ct in content_type.lower() for ct in ["text/html", "text/plain", "application/xhtml", "application/xml"]):
                        return ToolResult(
                            tool_name="browser.open",
                            status="success",
                            output={
                                "url": url,
                                "status_code": response.status_code,
                                "content_type": content_type,
                                "content": f"[Non-text content: {content_type}]",
                                "metadata": {"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat()}
                            }
                        )
                    
                    # Limit download size
                    html = response.text[:_MAX_CONTENT_LENGTH]
                
                # Extract clean article text using trafilatura
                extracted_text = await asyncio.get_event_loop().run_in_executor(
                    None, self._extract_content, html, url
                )
                
                # Extract metadata
                metadata = _extract_metadata(html, url)
                metadata["status_code"] = response.status_code
                
                content = _sanitize_content(extracted_text or "")
                
                if not content:
                    # Fallback: basic BS4 extraction if trafilatura returns nothing
                    content = await asyncio.get_event_loop().run_in_executor(
                        None, self._fallback_extract, html
                    )
                    content = _sanitize_content(content)
                
                logger.info(f"[browser.open] Fetched {url} — {len(content)} chars extracted")
                
                return ToolResult(
                    tool_name="browser.open",
                    status="success",
                    output={
                        "url": url,
                        "content": content[:30_000],  # cap for LLM context
                        "content_length": len(content),
                        "metadata": metadata
                    }
                )
                
            except httpx.TimeoutException:
                return ToolResult(tool_name="browser.open", status="error", output={"url": url}, error=f"Timeout fetching {url}")
            except httpx.HTTPStatusError as e:
                return ToolResult(tool_name="browser.open", status="error", output={"url": url}, error=f"HTTP {e.response.status_code}")
            except Exception as e:
                logger.error(f"[browser.open] Failed to fetch {url}: {e}")
                return ToolResult(tool_name="browser.open", status="error", output={"url": url}, error=f"Fetch failed: {str(e)[:200]}")

    def _extract_content(self, html: str, url: str) -> Optional[str]:
        """Extract main text content using trafilatura."""
        try:
            import trafilatura
            return trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_links=True,
                favor_recall=True,
                deduplicate=True
            )
        except Exception as e:
            logger.debug(f"trafilatura extraction failed: {e}")
            return None
    
    def _fallback_extract(self, html: str) -> str:
        """Fallback text extraction using BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script/style elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            # Collapse multiple newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text
        except Exception as e:
            logger.debug(f"BS4 fallback extraction failed: {e}")
            return ""


class WebScrapeTool(BaseTool):
    """Scrape structured data from a URL using BeautifulSoup."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="web.scrape",
            name="Web Scrape",
            category="research",
            description="Scrape structured data (headings, links, tables, lists) from a URL.",
            input_schema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},
                    "extract": {"type": "array", "items": {"type": "string"}, 
                               "default": ["headings", "links", "tables"],
                               "description": "What to extract: headings, links, tables, lists, text, images"}
                }
            },
            output_schema={"type": "object"},
            capabilities=["web_scraping"],
            requires_network=True,
            idempotent=True,
            timeout_seconds=_FETCH_TIMEOUT + 5
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        url = arguments.get("url", "").strip()
        if not url:
            return ToolResult(tool_name="web.scrape", status="error", output={}, error="No URL provided")
        
        # Security: SSRF check
        try:
            ToolSecurityPolicy.validate_ssrf(url)
        except Exception as e:
            return ToolResult(tool_name="web.scrape", status="error", output={}, error=f"Security: {e}")
        
        extract_types = arguments.get("extract", ["headings", "links", "tables"])
        
        async with _fetch_semaphore:
            try:
                import httpx
                from bs4 import BeautifulSoup
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; MycelResearch/1.0; +https://mycel.ai)",
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                }
                
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=httpx.Timeout(_FETCH_TIMEOUT),
                    max_redirects=5
                ) as client:
                    response = await client.get(url, headers=headers)
                    html = response.text[:_MAX_CONTENT_LENGTH]
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, 'lxml')
                
                # Remove script/style
                for tag in soup(['script', 'style']):
                    tag.decompose()
                
                data = {
                    "url": url,
                    "status_code": response.status_code,
                    "retrieved_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Title
                title_tag = soup.find('title')
                data["title"] = title_tag.get_text(strip=True)[:200] if title_tag else ""
                
                if "headings" in extract_types:
                    data["headings"] = self._extract_headings(soup)
                
                if "links" in extract_types:
                    data["links"] = self._extract_links(soup, url)
                
                if "tables" in extract_types:
                    data["tables"] = self._extract_tables(soup)
                
                if "lists" in extract_types:
                    data["lists"] = self._extract_lists(soup)
                
                if "text" in extract_types:
                    text = soup.get_text(separator='\n', strip=True)
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    data["text"] = _sanitize_content(text[:20_000])
                
                if "images" in extract_types:
                    data["images"] = self._extract_images(soup, url)
                
                logger.info(f"[web.scrape] Scraped {url} — extracted: {extract_types}")
                
                return ToolResult(
                    tool_name="web.scrape",
                    status="success",
                    output=data
                )
                
            except Exception as e:
                logger.error(f"[web.scrape] Failed to scrape {url}: {e}")
                return ToolResult(
                    tool_name="web.scrape",
                    status="error",
                    output={"url": url},
                    error=f"Scrape failed: {str(e)[:200]}"
                )

    def _extract_headings(self, soup) -> List[Dict[str, str]]:
        """Extract all headings (h1-h6)."""
        headings = []
        for level in range(1, 7):
            for tag in soup.find_all(f'h{level}'):
                text = tag.get_text(strip=True)[:200]
                if text:
                    headings.append({"level": level, "text": text})
        return headings[:50]  # cap

    def _extract_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract meaningful links."""
        from urllib.parse import urljoin
        links = []
        seen_urls = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            full_url = urljoin(base_url, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            text = a.get_text(strip=True)[:100]
            if text:
                links.append({"text": text, "url": full_url})
        return links[:100]  # cap

    def _extract_tables(self, soup) -> List[List[List[str]]]:
        """Extract HTML tables as lists of rows."""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = []
                for td in tr.find_all(['td', 'th']):
                    cells.append(td.get_text(strip=True)[:200])
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables[:10]  # cap at 10 tables

    def _extract_lists(self, soup) -> List[List[str]]:
        """Extract bulleted/numbered lists."""
        lists = []
        for ul in soup.find_all(['ul', 'ol']):
            items = []
            for li in ul.find_all('li', recursive=False):
                text = li.get_text(strip=True)[:200]
                if text:
                    items.append(text)
            if items:
                lists.append(items)
        return lists[:20]  # cap

    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract image URLs and alt text."""
        from urllib.parse import urljoin
        images = []
        for img in soup.find_all('img', src=True):
            src = urljoin(base_url, img['src'])
            alt = img.get('alt', '')[:200]
            images.append({"src": src, "alt": alt})
        return images[:30]  # cap
