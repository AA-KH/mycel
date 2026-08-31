"""
Visit Counter Module - Website visit statistics
"""

import asyncio

from .config import VISIT_COUNT_FILE


def _get_visit_count_sync():
    """Get current visit count synchronously (internal function)"""
    if VISIT_COUNT_FILE.exists():
        try:
            return int(VISIT_COUNT_FILE.read_text().strip())
        except:
            return 218
    return 218


def _increment_visit_count_sync():
    """Increment visit count synchronously and return new value (internal function)"""
    count = _get_visit_count_sync() + 1
    VISIT_COUNT_FILE.write_text(str(count))
    return count


async def get_visit_count():
    """Asynchronously get visit count"""
    count = await asyncio.to_thread(_get_visit_count_sync)
    return count


async def increment_visit_count():
    """Asynchronously increment visit count"""
    new_count = await asyncio.to_thread(_increment_visit_count_sync)
    return new_count
