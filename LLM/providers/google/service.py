from LLM.interface import LLMService as BaseLLMService

class LLMService(BaseLLMService):
    def summarize(self, text: str) -> str:
        # Dummy implementation for the Google provider.
        # Replace this with actual integration when ready.
        return "DESCRIPTION/SUMMARY COMES HERE FROM GOOGLE"
