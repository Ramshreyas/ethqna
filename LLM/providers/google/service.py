import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env
from google import genai
from google.genai import types
import pathlib
from LLM.providers.google.prompts import SUMMARIZATION_PROMPT

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise Exception("GEMINI_API_KEY not set in environment variables")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-1.5-flash"

    def summarize(self, pdf_path: str) -> str:
        pdf_bytes = pathlib.Path(pdf_path).read_bytes()
        part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type='application/pdf',
        )
        # Pass both the PDF part and the summarization prompt as a text parameter.
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=SUMMARIZATION_PROMPT),
            contents=[part, SUMMARIZATION_PROMPT]
        )
        return response.text
