import pathlib

class LLMService:
    def summarize(self, pdf_path: str) -> str:
        try:
            file_size = pathlib.Path(pdf_path).stat().st_size
            return f"Dummy summary: The document is {file_size} bytes in size."
        except Exception as e:
            return f"Dummy summarization error: {str(e)}"
