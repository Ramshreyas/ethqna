# services/llm.py

from abc import ABC, abstractmethod

class LLMService(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Summarize the given text and return a short description."""
        pass

    @abstractmethod
    def cluster_documents(self, documents_json: str, prompt: str) -> dict:
        """Cluster documents based on their descriptions and return clustering results."""
        pass
