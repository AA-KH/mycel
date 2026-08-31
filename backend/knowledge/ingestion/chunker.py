from typing import List

class ChunkingService:
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        
    async def chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks. Very naive fixed-size implementation for TOS 4.
        """
        if not text:
            return []
            
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i+self.chunk_size])
            
        return chunks
