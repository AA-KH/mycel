"""
Research Engine — Content Fetcher

Fetches web pages and extracts clean text content.
Uses httpx for async HTTP and trafilatura for article extraction.
All content is treated as untrusted data.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_fetch_semaphore = asyncio.Semaphore(5)
_FETCH_TIMEOUT = 15
_MAX_CONTENT_LENGTH = 200_000

# Common user agent
_USER_AGENT = "Mozilla/5.0 (compatible; MycelResearch/1.0; +https://mycel.ai)"

_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class FetchResult:
    """Result of fetching a URL."""
    __slots__ = ('url', 'status_code', 'content', 'html', 'title', 'author',
                 'published_date', 'description', 'content_hash', 'retrieved_at',
                 'error', 'is_success')
    
    def __init__(self, url: str):
        self.url = url
        self.status_code = 0
        self.content = ""          # Extracted clean text
        self.html = ""             # Raw HTML (for further parsing if needed)
        self.title = ""
        self.author = ""
        self.published_date = ""
        self.description = ""
        self.content_hash = ""
        self.retrieved_at = datetime.now(timezone.utc)
        self.error = ""
        self.is_success = False


class ContentFetcher:
    """
    Async content fetcher with:
    - HTTP-first approach (no browser automation)
    - trafilatura for clean article extraction
    - BeautifulSoup fallback
    - Content deduplication via hashing
    - Rate limiting
    - Timeout handling
    - SSRF protection
    """
    
    def __init__(self, timeout: int = _FETCH_TIMEOUT, max_concurrent: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._timeout = timeout
        self._cache: Dict[str, FetchResult] = {}  # url → FetchResult
        self._content_hashes: Dict[str, str] = {}  # hash → first url
    
    async def fetch(self, url: str, use_cache: bool = True) -> FetchResult:
        """Fetch a URL and extract clean text content."""
        if use_cache and url in self._cache:
            logger.debug(f"[Fetcher] Cache hit: {url}")
            return self._cache[url]
        
        result = FetchResult(url)
        
        # Validate URL
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            result.error = f"Unsupported scheme: {parsed.scheme}"
            return result
        
        # SSRF check
        try:
            from tools.security import ToolSecurityPolicy
            ToolSecurityPolicy.validate_ssrf(url)
        except Exception as e:
            result.error = f"Security check failed: {e}"
            return result
        
        async with self._semaphore:
            try:
                import httpx
                
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=httpx.Timeout(self._timeout),
                    max_redirects=5
                ) as client:
                    response = await client.get(url, headers=_HEADERS)
                    result.status_code = response.status_code
                    
                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    if not any(ct in content_type.lower() for ct in 
                              ["text/html", "text/plain", "application/xhtml", "application/xml"]):
                        result.error = f"Non-text content: {content_type}"
                        result.content = f"[Binary content: {content_type}]"
                        return result
                    
                    html = response.text[:_MAX_CONTENT_LENGTH]
                    result.html = html
                
                # Extract content
                content, metadata = await asyncio.get_event_loop().run_in_executor(
                    None, self._extract, html, url
                )
                
                result.content = self._sanitize(content or "")
                result.title = metadata.get("title", "")
                result.author = metadata.get("author", "")
                result.published_date = metadata.get("date", "")
                result.description = metadata.get("description", "")
                
                # Content hash for deduplication
                if result.content:
                    result.content_hash = hashlib.md5(result.content[:5000].encode()).hexdigest()
                    
                    # Check for duplicate content from different URL
                    if result.content_hash in self._content_hashes:
                        original_url = self._content_hashes[result.content_hash]
                        logger.info(f"[Fetcher] Duplicate content detected: {url} matches {original_url}")
                    else:
                        self._content_hashes[result.content_hash] = url
                
                result.is_success = bool(result.content)
                
                if not result.content:
                    result.error = "No content could be extracted"
                
                logger.info(f"[Fetcher] {url} → {len(result.content)} chars")
                
            except asyncio.TimeoutError:
                result.error = f"Timeout after {self._timeout}s"
            except Exception as e:
                result.error = f"Fetch error: {str(e)[:200]}"
                logger.error(f"[Fetcher] Failed {url}: {e}")
        
        # Cache the result
        if use_cache:
            self._cache[url] = result
        
        return result
    
    async def fetch_multiple(self, urls: list, use_cache: bool = True) -> list:
        """Fetch multiple URLs concurrently."""
        tasks = [self.fetch(url, use_cache) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def is_duplicate_content(self, content_hash: str) -> bool:
        """Check if content with this hash has been seen before."""
        return content_hash in self._content_hashes
    
    def _extract(self, html: str, url: str) -> Tuple[str, Dict[str, str]]:
        """Extract clean text and metadata from HTML."""
        metadata = {}
        content = ""
        
        # Try trafilatura first (best for articles)
        try:
            import trafilatura
            result = trafilatura.extract(
                html, url=url,
                include_comments=False,
                include_tables=True,
                include_links=True,
                favor_recall=True,
                deduplicate=True
            )
            if result:
                content = result
            
            # Extract metadata via trafilatura
            meta = trafilatura.extract(html, url=url, output_format='xmltei',
                                        include_comments=False)
            # trafilatura metadata extraction is complex; use BS4 for reliability
        except Exception as e:
            logger.debug(f"trafilatura failed for {url}: {e}")
        
        # Extract metadata with BS4
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html[:20_000], 'lxml')
            
            title_tag = soup.find('title')
            if title_tag:
                metadata["title"] = title_tag.get_text(strip=True)[:200]
            
            for name, attr, key in [
                ('description', 'name', 'description'),
                ('author', 'name', 'author'),
                ('article:published_time', 'property', 'date'),
            ]:
                tag = soup.find('meta', attrs={attr: name})
                if tag and tag.get('content'):
                    metadata[key] = tag['content'][:200]
        except Exception:
            pass
        
        # Fallback extraction if trafilatura failed
        if not content:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'lxml')
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                    tag.decompose()
                content = soup.get_text(separator='\n', strip=True)
                content = re.sub(r'\n{3,}', '\n\n', content)
            except Exception:
                content = ""
        
        return content, metadata
    
    def _sanitize(self, text: str) -> str:
        """Sanitize extracted web content — treat as DATA, never as instructions."""
        if not text:
            return ""
        text = text[:50_000]
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text
    
    @property
    def cache_size(self) -> int:
        return len(self._cache)
    
    @property 
    def duplicate_count(self) -> int:
        """Number of URLs that had duplicate content."""
        return max(0, len(self._cache) - len(self._content_hashes))
