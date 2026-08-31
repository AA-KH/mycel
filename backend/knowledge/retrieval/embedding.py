from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

class MockEmbeddingProvider(EmbeddingProvider):
    """
    A lightweight mock provider for TOS 4 to avoid heavy ML dependencies.
    """
    async def embed_text(self, text: str) -> List[float]:
        # Return a deterministic mock vector based on length
        return [float(len(text) % 10) / 10.0] * 128

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]
