"""
Deduplication engine.

Three-layer deduplication:
1. Exact source ID / URL / GUID
2. Canonicalized title + content SimHash
3. Near-duplicate via entity/location/time-window overlap

100 reports about one factory fire → ONE EVENT with MULTIPLE SOURCES.
Provenance is never lost — corroborating sources are stored.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger

from ..models.events import CanonicalEvent


class DeduplicationEngine:
    """Layered event deduplication.

    Maintains in-memory indices for fast lookup. Events that are duplicates
    get their dedup_of field set to the original event ID.
    """

    def __init__(self, time_window_hours: int = 48, simhash_threshold: int = 3):
        self.time_window = timedelta(hours=time_window_hours)
        self.simhash_threshold = simhash_threshold

        # Layer 1: Exact ID index
        self._source_ids: dict[str, str] = {}  # source_event_id → event_id
        self._urls: dict[str, str] = {}  # source_url → event_id

        # Layer 2: Content hash index
        self._content_hashes: dict[str, str] = {}  # content_hash → event_id
        self._title_hashes: dict[str, str] = {}  # title_hash → event_id

        # Layer 3: Simhash index for near-duplicates
        self._simhashes: dict[int, list[tuple[str, datetime]]] = {}

        # Source tracking: event_id → list of corroborating sources
        self.corroborating_sources: dict[str, list[str]] = {}

    def check_and_register(self, event: CanonicalEvent) -> Optional[str]:
        """Check if event is a duplicate. If so, return original event_id.

        If not a duplicate, registers the event and returns None.
        """
        # Layer 1: Exact source ID
        if event.source_event_id:
            if event.source_event_id in self._source_ids:
                original = self._source_ids[event.source_event_id]
                self._add_corroborating_source(original, event.source)
                event.log(f"DUPLICATE: exact source_id match → {original}")
                return original

        if event.source_url:
            if event.source_url in self._urls:
                original = self._urls[event.source_url]
                self._add_corroborating_source(original, event.source)
                event.log(f"DUPLICATE: exact URL match → {original}")
                return original

        # Layer 2: Content hash
        if event.content_hash and event.content_hash in self._content_hashes:
            original = self._content_hashes[event.content_hash]
            self._add_corroborating_source(original, event.source)
            event.log(f"DUPLICATE: content hash match → {original}")
            return original

        # Layer 2b: Title hash (catches same story from different domains)
        if event.title_hash and event.title_hash in self._title_hashes:
            original = self._title_hashes[event.title_hash]
            self._add_corroborating_source(original, event.source)
            event.log(f"DUPLICATE: title hash match → {original}")
            return original

        # Layer 3: SimHash near-duplicate
        simhash = self._compute_simhash(event.title)
        near_dup = self._find_near_duplicate(simhash, event.detected_at)
        if near_dup:
            self._add_corroborating_source(near_dup, event.source)
            event.log(f"NEAR-DUPLICATE: simhash match → {near_dup}")
            return near_dup

        # Not a duplicate — register it
        self._register(event, simhash)
        return None

    def _register(self, event: CanonicalEvent, simhash: int) -> None:
        """Register a new unique event."""
        if event.source_event_id:
            self._source_ids[event.source_event_id] = event.event_id
        if event.source_url:
            self._urls[event.source_url] = event.event_id
        if event.content_hash:
            self._content_hashes[event.content_hash] = event.event_id
        if event.title_hash:
            self._title_hashes[event.title_hash] = event.event_id

        self._simhashes.setdefault(simhash, []).append(
            (event.event_id, event.detected_at)
        )
        self.corroborating_sources[event.event_id] = [event.source]

    def _add_corroborating_source(self, original_id: str, source: str) -> None:
        """Track that another source corroborates an existing event."""
        sources = self.corroborating_sources.setdefault(original_id, [])
        if source not in sources:
            sources.append(source)

    def get_source_count(self, event_id: str) -> int:
        """How many independent sources corroborate this event."""
        return len(self.corroborating_sources.get(event_id, []))

    def get_sources(self, event_id: str) -> list[str]:
        """Get all corroborating source names."""
        return self.corroborating_sources.get(event_id, [])

    def _compute_simhash(self, text: str) -> int:
        """Compute a 64-bit SimHash for near-duplicate detection."""
        # Normalize text
        text = re.sub(r'[^\w\s]', '', text.lower())
        tokens = text.split()

        if not tokens:
            return 0

        # Weighted bit vector
        v = [0] * 64
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)
            for i in range(64):
                if token_hash & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1

        # Threshold to bits
        fingerprint = 0
        for i in range(64):
            if v[i] >= 0:
                fingerprint |= (1 << i)

        return fingerprint

    def _find_near_duplicate(
        self, simhash: int, timestamp: datetime
    ) -> Optional[str]:
        """Find a near-duplicate using SimHash hamming distance."""
        cutoff = timestamp - self.time_window

        for existing_hash, entries in self._simhashes.items():
            distance = bin(simhash ^ existing_hash).count('1')
            if distance <= self.simhash_threshold:
                for event_id, event_time in entries:
                    if event_time >= cutoff:
                        return event_id

        return None

    def cleanup_old(self, max_age_hours: int = 72) -> int:
        """Remove entries older than max_age to prevent unbounded memory growth."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        removed = 0

        # Clean simhash index
        for hash_val in list(self._simhashes.keys()):
            entries = self._simhashes[hash_val]
            self._simhashes[hash_val] = [
                (eid, t) for eid, t in entries if t >= cutoff
            ]
            removed += len(entries) - len(self._simhashes[hash_val])
            if not self._simhashes[hash_val]:
                del self._simhashes[hash_val]

        return removed
