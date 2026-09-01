"""
Entity resolver.

Deterministic entity resolution chain:
1. Exact match
2. Normalized match (case, punctuation, whitespace)
3. Alias match
4. Fuzzy match (RapidFuzz)

Network-scoped: only resolves against THIS network's entities.
Genuinely ambiguous cases are flagged for the semantic analyst.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from loguru import logger

from ..models.profile import EntityAlias

# Try to import rapidfuzz; fall back to basic matching if unavailable
try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    logger.warning("rapidfuzz not installed — fuzzy matching disabled")


class EntityResolver:
    """Resolves entity mentions to canonical network entities.

    Only resolves against entities in the current monitoring profile.
    This is NOT a general-world entity knowledge system.
    """

    def __init__(self, entity_aliases: list[EntityAlias], fuzzy_threshold: int = 78):
        self.fuzzy_threshold = fuzzy_threshold

        # Build lookup indices
        self._exact: dict[str, str] = {}  # lowered name → entity_id
        self._normalized: dict[str, str] = {}  # normalized name → entity_id
        self._domain: dict[str, str] = {}  # domain → entity_id
        self._all_names: dict[str, str] = {}  # all variants → entity_id
        self._id_to_canonical: dict[str, str] = {}  # entity_id → canonical name

        for alias in entity_aliases:
            eid = alias.entity_id
            self._id_to_canonical[eid] = alias.canonical_name

            # Register canonical name
            self._exact[alias.canonical_name.lower()] = eid
            self._normalized[self._normalize(alias.canonical_name)] = eid
            self._all_names[alias.canonical_name.lower()] = eid

            # Register all aliases
            for a in alias.aliases:
                self._exact[a.lower()] = eid
                self._normalized[self._normalize(a)] = eid
                self._all_names[a.lower()] = eid

            # Register abbreviations
            for abbr in alias.abbreviations:
                self._exact[abbr.lower()] = eid
                self._all_names[abbr.lower()] = eid

            # Register domain
            if alias.domain:
                self._domain[alias.domain.lower()] = eid

    def resolve(self, mention: str) -> Optional[EntityMatch]:
        """Try to resolve an entity mention to a network entity.

        Returns EntityMatch with the resolution method and confidence,
        or None if no match found.
        """
        if not mention or not mention.strip():
            return None

        mention_clean = mention.strip()

        # Layer 1: Exact match
        result = self._exact.get(mention_clean.lower())
        if result:
            return EntityMatch(
                entity_id=result,
                canonical_name=self._id_to_canonical[result],
                method="exact",
                confidence=1.0,
                matched_text=mention_clean,
            )

        # Layer 2: Normalized match
        norm = self._normalize(mention_clean)
        result = self._normalized.get(norm)
        if result:
            return EntityMatch(
                entity_id=result,
                canonical_name=self._id_to_canonical[result],
                method="normalized",
                confidence=0.95,
                matched_text=mention_clean,
            )

        # Layer 3: Domain match
        if "." in mention_clean:
            domain = mention_clean.lower().replace("https://", "").replace("http://", "").split("/")[0]
            result = self._domain.get(domain)
            if result:
                return EntityMatch(
                    entity_id=result,
                    canonical_name=self._id_to_canonical[result],
                    method="domain",
                    confidence=0.9,
                    matched_text=domain,
                )

        # Layer 4: Fuzzy match
        if HAS_RAPIDFUZZ:
            return self._fuzzy_match(mention_clean)

        return None

    def resolve_many(self, mentions: list[str]) -> list[EntityMatch]:
        """Resolve multiple entity mentions. Returns all matches."""
        matches = []
        for mention in mentions:
            match = self.resolve(mention)
            if match:
                matches.append(match)
        return matches

    def scan_text(self, text: str) -> list[EntityMatch]:
        """Scan free text for entity mentions.

        Checks all known entity names against the text.
        More expensive than resolve() but catches embedded mentions.
        """
        if not text:
            return []

        text_lower = text.lower()
        matches: list[EntityMatch] = []
        seen_entities: set[str] = set()

        for name, entity_id in self._all_names.items():
            if entity_id in seen_entities:
                continue
            if len(name) < 3:
                continue  # Skip very short abbreviations in free text scan

            if name in text_lower:
                # Verify word boundary to avoid false positives
                pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
                if pattern.search(text):
                    matches.append(EntityMatch(
                        entity_id=entity_id,
                        canonical_name=self._id_to_canonical[entity_id],
                        method="text_scan",
                        confidence=0.8,
                        matched_text=name,
                    ))
                    seen_entities.add(entity_id)

        return matches

    def _normalize(self, text: str) -> str:
        """Normalize text for matching: lowercase, remove punctuation, compact whitespace."""
        text = unicodedata.normalize("NFKD", text)
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text).strip()  # Compact whitespace
        # Remove common business suffixes
        for suffix in ["pvt ltd", "pvt", "ltd", "gmbh", "inc", "corp", "co", "llc"]:
            text = re.sub(rf'\b{suffix}\b', '', text).strip()
        return text

    def _fuzzy_match(self, mention: str) -> Optional[EntityMatch]:
        """Fuzzy match using RapidFuzz."""
        if not self._all_names:
            return None

        all_names = list(self._all_names.keys())
        result = process.extractOne(
            mention.lower(), all_names, scorer=fuzz.token_sort_ratio
        )
        if result and result[1] >= self.fuzzy_threshold:
            matched_name, score, _ = result
            entity_id = self._all_names[matched_name]
            return EntityMatch(
                entity_id=entity_id,
                canonical_name=self._id_to_canonical[entity_id],
                method="fuzzy",
                confidence=score / 100.0,
                matched_text=matched_name,
            )

        return None


class EntityMatch:
    """Result of entity resolution."""

    __slots__ = ("entity_id", "canonical_name", "method", "confidence", "matched_text")

    def __init__(
        self,
        entity_id: str,
        canonical_name: str,
        method: str,
        confidence: float,
        matched_text: str,
    ):
        self.entity_id = entity_id
        self.canonical_name = canonical_name
        self.method = method  # exact, normalized, domain, fuzzy, text_scan
        self.confidence = confidence
        self.matched_text = matched_text

    def __repr__(self) -> str:
        return (
            f"EntityMatch({self.canonical_name!r}, method={self.method}, "
            f"confidence={self.confidence:.2f})"
        )
