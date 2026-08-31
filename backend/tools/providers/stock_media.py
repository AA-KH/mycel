import logging
import asyncio
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class StockMediaProviderError(Exception):
    pass

class StockMediaProvider:
    """
    Native integration for sourcing stock footage and images.
    """
    
    def __init__(self, api_key: str = "mock"):
        self.api_key = api_key
        
    async def search_videos(self, query: str, per_page: int = 15) -> List[Dict]:
        """
        Search for stock videos.
        Returns a list of video metadata dictionaries.
        """
        logger.info(f"Searching stock videos for query: {query}")
        
        # MOCK IMPLEMENTATION
        # In a real implementation, this would call Pexels API
        await asyncio.sleep(1) # Simulate network call
        
        return [
            {
                "id": f"vid_mock_{i}",
                "url": f"https://mock.stock/videos/{query.replace(' ', '_')}_{i}.mp4",
                "width": 1920,
                "height": 1080,
                "duration": 15
            }
            for i in range(min(per_page, 3))
        ]
        
    async def download_video(self, url: str) -> bytes:
        """
        Download a stock video and return its bytes.
        """
        logger.info(f"Downloading stock video from {url}")
        
        # MOCK IMPLEMENTATION
        await asyncio.sleep(1)
        
        return b"MOCK_VIDEO_BYTES"

def get_stock_media_provider() -> StockMediaProvider:
    return StockMediaProvider()
