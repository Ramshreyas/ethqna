# services/llm.py

from abc import ABC, abstractmethod

class LLMService(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Summarize the given text and return a short description."""
        pass
