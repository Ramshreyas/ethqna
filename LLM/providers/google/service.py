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

    def summarize(self, input_str: str) -> str:
        print("DEBUG: In google LLMService.summarize, received input_str:", repr(input_str))
        # Check if input_str is a valid file path.
        if os.path.exists(input_str):
            print("DEBUG: Detected input_str as a valid file path. Reading PDF bytes.")
            pdf_bytes = pathlib.Path(input_str).read_bytes()
            part = types.Part.from_bytes(
                data=pdf_bytes,
                mime_type='application/pdf'
            )
            contents = [part, SUMMARIZATION_PROMPT]
        else:
            print("DEBUG: Input_str is not a file path. Treating input as plain text.")
            contents = [input_str, SUMMARIZATION_PROMPT]
        
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=SUMMARIZATION_PROMPT),
            contents=contents
        )
        print("DEBUG: Gemini API raw response text:", response.text)
        return response.text
