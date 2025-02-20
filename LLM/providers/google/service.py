import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env
from google import genai
from google.genai import types
import pathlib
import json
from LLM.providers.google.prompts import SUMMARIZATION_PROMPT, METADATA_PROMPT

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise Exception("GEMINI_API_KEY not set in environment variables")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-1.5-flash"

    def _process_input(self, input_str: str, prompt: str):
        """Helper function to determine if input is a file or text."""
        if os.path.exists(input_str):
            print(f"DEBUG: Reading PDF file: {input_str}")
            pdf_bytes = pathlib.Path(input_str).read_bytes()
            part = types.Part.from_bytes(
                data=pdf_bytes,
                mime_type='application/pdf'
            )
            contents = [part, prompt]
        else:
            print("DEBUG: Input is plain text.")
            contents = [input_str, prompt]
        
        return contents

    def summarize(self, input_str: str) -> str:
        """Summarizes a PDF file or text input using SUMMARIZATION_PROMPT."""
        print("DEBUG: Summarizing document...")
        contents = self._process_input(input_str, SUMMARIZATION_PROMPT)

        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=SUMMARIZATION_PROMPT),
            contents=contents
        )
        print("DEBUG: Gemini API summary response:", response.text)
        return response.text

    def generate_metadata(self, input_str: str) -> dict:
        """Extracts metadata (title, authors, date, tags) from a PDF or text."""
        print("DEBUG: Extracting metadata...")
        contents = self._process_input(input_str, METADATA_PROMPT)

        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=METADATA_PROMPT),
            contents=contents
        )
        print("DEBUG: Gemini API metadata response:", response.text)

        try:
            metadata = json.loads(response.text)  # Ensure valid JSON
            return metadata
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse metadata JSON: {e}")
