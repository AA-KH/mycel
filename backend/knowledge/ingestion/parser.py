from abc import ABC, abstractmethod

class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, uri: str) -> str:
        """Extracts normalized text from the given URI."""
        pass

class MockTextParser(DocumentParser):
    """Simple parser that just returns the URI as text for testing."""
    async def parse(self, uri: str) -> str:
        # In a real system, we'd open the file at URI and extract text.
        # For TOS 4 foundation, we mock extraction.
        if uri.startswith("mock://"):
            return uri.replace("mock://", "")
        return f"Mocked content for {uri}"
