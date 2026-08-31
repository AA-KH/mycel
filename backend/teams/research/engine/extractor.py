"""
Research Engine — Content Extractor

Extracts structured information from fetched web content:
- Claims / factual assertions
- Pricing data
- Feature lists
- Entities
- Temporal information
- Source classification (tier & type)

Uses the Groq LLM for intelligent extraction where necessary,
and deterministic parsing where possible.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from teams.research.models import (
    Source, Evidence, Claim, SourceTier, SourceType, ClaimConfidence
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Source Classification (deterministic)
# ─────────────────────────────────────────────────────────────

# Domain → (SourceType, SourceTier) mapping for known domains
_DOMAIN_CLASSIFICATION: Dict[str, Tuple[SourceType, SourceTier]] = {
    # Tier 1 — Primary
    "github.com": (SourceType.GITHUB_REPOSITORY, SourceTier.PRIMARY),
    "docs.": (SourceType.DOCUMENTATION, SourceTier.PRIMARY),
    ".gov": (SourceType.GOVERNMENT_SITE, SourceTier.PRIMARY),
    ".edu": (SourceType.ACADEMIC_PAPER, SourceTier.HIGH_QUALITY_SECONDARY),
    
    # Tier 2 — High quality secondary
    "techcrunch.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "reuters.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "bloomberg.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "theverge.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "arstechnica.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "wired.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "forbes.com": (SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY),
    "nature.com": (SourceType.ACADEMIC_PAPER, SourceTier.PRIMARY),
    "arxiv.org": (SourceType.ACADEMIC_PAPER, SourceTier.HIGH_QUALITY_SECONDARY),
    "scholar.google.com": (SourceType.ACADEMIC_PAPER, SourceTier.HIGH_QUALITY_SECONDARY),
    
    # Tier 3 — Community
    "reddit.com": (SourceType.FORUM_POST, SourceTier.COMMUNITY),
    "news.ycombinator.com": (SourceType.FORUM_POST, SourceTier.COMMUNITY),
    "stackoverflow.com": (SourceType.FORUM_POST, SourceTier.COMMUNITY),
    "g2.com": (SourceType.REVIEW_SITE, SourceTier.COMMUNITY),
    "trustpilot.com": (SourceType.REVIEW_SITE, SourceTier.COMMUNITY),
    "capterra.com": (SourceType.REVIEW_SITE, SourceTier.COMMUNITY),
    "producthunt.com": (SourceType.REVIEW_SITE, SourceTier.COMMUNITY),
    
    # Tier 4 — Low confidence (catch-all for unknown domains)
}


def classify_source(url: str, title: str = "") -> Tuple[SourceType, SourceTier]:
    """
    Classify a source by its URL and title into a type and reliability tier.
    Uses deterministic rules — no LLM needed.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()
    
    # Check exact domain matches first
    for pattern, classification in _DOMAIN_CLASSIFICATION.items():
        if pattern in domain:
            return classification
    
    # Heuristic classification based on URL patterns
    
    # Pricing pages → PRIMARY (official)
    if any(kw in path for kw in ['/pricing', '/plans', '/cost']):
        return SourceType.PRICING_PAGE, SourceTier.PRIMARY
    
    # Documentation
    if any(kw in domain or kw in path for kw in ['docs.', '/docs/', '/documentation/', '/api/']):
        return SourceType.DOCUMENTATION, SourceTier.PRIMARY
    
    # Blog posts
    if any(kw in path for kw in ['/blog/', '/post/', '/article/']):
        return SourceType.BLOG_POST, SourceTier.HIGH_QUALITY_SECONDARY
    
    # GitHub
    if 'github.com' in domain or 'github.io' in domain:
        return SourceType.GITHUB_REPOSITORY, SourceTier.PRIMARY
    
    # News
    if any(kw in domain for kw in ['news', 'press', 'media']):
        return SourceType.NEWS_ARTICLE, SourceTier.HIGH_QUALITY_SECONDARY
    
    # Review sites
    if any(kw in domain for kw in ['review', 'compare', 'versus']):
        return SourceType.REVIEW_SITE, SourceTier.COMMUNITY
    
    # Job postings
    if any(kw in domain or kw in path for kw in ['careers', 'jobs', 'linkedin.com/jobs']):
        return SourceType.JOB_POSTING, SourceTier.HIGH_QUALITY_SECONDARY
    
    # Default
    return SourceType.OTHER, SourceTier.LOW_CONFIDENCE


def create_source_from_fetch(url: str, title: str = "", author: str = "",
                              published_date: str = "", description: str = "",
                              content_hash: str = "", is_accessible: bool = True,
                              access_error: str = "") -> Source:
    """Create a Source object from fetched metadata."""
    source_type, tier = classify_source(url, title)
    domain = urlparse(url).netloc.replace("www.", "")
    
    return Source(
        url=url,
        title=title,
        source_type=source_type,
        tier=tier,
        published_date=published_date or None,
        author=author or None,
        domain=domain,
        description=description or None,
        is_accessible=is_accessible,
        access_error=access_error or None,
        content_hash=content_hash or None,
    )


# ─────────────────────────────────────────────────────────────
# Evidence Extraction (from text content)
# ─────────────────────────────────────────────────────────────

def extract_evidence_snippets(content: str, question: str, source_id: str,
                                max_snippets: int = 5, agent_name: str = "Aarav") -> List[Evidence]:
    """
    Extract relevant text snippets from content that may answer a question.
    Uses simple keyword matching and paragraph extraction.
    For complex extraction, the agent will use the LLM.
    """
    if not content:
        return []
    
    evidence_list = []
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in content.split('\n') if p.strip() and len(p.strip()) > 30]
    
    # Score paragraphs by keyword relevance to the question
    question_words = set(question.lower().split())
    # Remove common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'who', 
                  'when', 'where', 'which', 'that', 'this', 'for', 'and', 'or', 'but',
                  'in', 'on', 'at', 'to', 'of', 'with', 'by', 'from', 'about', 'does', 'do'}
    question_keywords = question_words - stop_words
    
    scored = []
    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for kw in question_keywords if kw in para_lower)
        if score > 0:
            scored.append((score, para))
    
    # Sort by relevance, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    
    for score, para in scored[:max_snippets]:
        relevance = min(1.0, score / max(len(question_keywords), 1))
        evidence = Evidence(
            source_id=source_id,
            text=para[:1000],  # Truncate long paragraphs
            context=para[:200],
            extracted_by=agent_name,
            relevance_score=relevance
        )
        evidence_list.append(evidence)
    
    return evidence_list


# ─────────────────────────────────────────────────────────────
# Pricing Extraction (deterministic)
# ─────────────────────────────────────────────────────────────

_PRICE_PATTERN = re.compile(
    r'[\$€£]\s*(\d+[\d,]*\.?\d*)\s*(?:/\s*(?:month|mo|yr|year|user|seat))?',
    re.IGNORECASE
)

def extract_pricing(content: str) -> List[Dict[str, str]]:
    """Extract pricing information from text content."""
    prices = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        matches = _PRICE_PATTERN.findall(line)
        if matches:
            # Get context (surrounding lines)
            context_start = max(0, i - 1)
            context_end = min(len(lines), i + 2)
            context = '\n'.join(lines[context_start:context_end])
            
            for price in matches:
                prices.append({
                    "amount": price,
                    "context": context[:300],
                    "line": line.strip()[:200]
                })
    
    return prices[:20]  # Cap


# ─────────────────────────────────────────────────────────────
# Date Extraction (deterministic)
# ─────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    re.compile(r'(\d{4}-\d{2}-\d{2})'),  # ISO format
    re.compile(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})', re.IGNORECASE),
    re.compile(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})', re.IGNORECASE),
]

def extract_dates(content: str) -> List[str]:
    """Extract dates mentioned in content."""
    dates = []
    for pattern in _DATE_PATTERNS:
        for match in pattern.findall(content[:10_000]):
            if match not in dates:
                dates.append(match)
    return dates[:20]


# ─────────────────────────────────────────────────────────────
# Source Deduplication
# ─────────────────────────────────────────────────────────────

def are_sources_duplicate(source_a: Source, source_b: Source) -> bool:
    """Check if two sources contain the same content."""
    if source_a.content_hash and source_b.content_hash:
        return source_a.content_hash == source_b.content_hash
    return source_a.url == source_b.url


def count_independent_sources(claims_sources: List[Source]) -> int:
    """
    Count truly independent sources (not just copies of the same content).
    This helps distinguish '10 sources repeating one press release' from
    '3 genuinely independent sources.'
    """
    unique_hashes = set()
    unique_domains = set()
    
    for source in claims_sources:
        if source.content_hash:
            unique_hashes.add(source.content_hash)
        unique_domains.add(source.domain)
    
    # Independent = unique content OR unique domains
    return max(len(unique_hashes), len(unique_domains))
