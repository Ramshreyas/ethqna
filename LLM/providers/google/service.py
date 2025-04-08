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
        """Extracts metadata (title, authors, date, tags) from a PDF or text input."""
        print("DEBUG: Extracting metadata...")
        contents = self._process_input(input_str, METADATA_PROMPT)

        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=METADATA_PROMPT),
            contents=contents
        )

        if not response or not response.text.strip():
            raise Exception("Gemini API returned an empty response for metadata extraction.")

        raw_text = response.text.strip()
        print("DEBUG: Gemini API metadata raw response:", raw_text)

        # Sanitize Gemini API response if wrapped in ```json ... ```
        if raw_text.startswith("```json"):
            raw_text = raw_text[len("```json"):].strip()
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].strip()

        try:
            metadata = json.loads(raw_text)  # Ensure it's valid JSON
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse metadata JSON: {e}. Raw response: {raw_text}")

        return metadata

    def filter_documents(self, documents_text: str, prompt: str) -> dict:
        print("DEBUG: Filtering documents using LLM...", flush=True)
        # Since documents_text is plain JSON (and not a file path), it will be processed as plain text.
        contents = [documents_text, prompt]
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=prompt),
            contents=contents
        )
        raw_response = response.text.strip()
        print("DEBUG: Gemini API filter documents response:", raw_response, flush=True)
        # Remove code fences if present
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()
        try:
            result = json.loads(raw_response)
        except Exception as e:
            raise Exception(f"Error parsing filter documents response: {e}. Raw response: {raw_response}")
        return result

    def chat(self, pdf_data: bytes, prompt: str) -> dict:
        print("DEBUG: Processing chat request...", flush=True)
        part = types.Part.from_bytes(data=pdf_data, mime_type='application/pdf')
        contents = [part, prompt]

        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=prompt),
            contents=contents
        )
        raw_response = response.text.strip()
        print("DEBUG: Gemini API chat response:", raw_response, flush=True)

        # Remove code fences if present
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()

        try:
            result = json.loads(raw_response)
        except Exception as e:
            raise Exception(f"Error parsing chat response: {e}. Raw response: {raw_response}")

        return result
    
    def cluster_documents(self, documents_json: str, prompt: str) -> dict:
        print("DEBUG: Clustering documents using LLM...", flush=True)
        contents = [documents_json, prompt]
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=prompt),
            contents=contents
        )
        raw_response = response.text.strip()
        print("DEBUG: Gemini API cluster documents response:", raw_response, flush=True)
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()
        try:
            result = json.loads(raw_response)
        except Exception as e:
            raise Exception(f"Error parsing cluster documents response: {e}. Raw response: {raw_response}")
        return result
    
    def analyze_pdf(self, pdf_path: str, prompt: str) -> dict:
        """
        Analyze a PDF file by sending it along with the provided prompt.
        Returns the response as a JSON object.
        """
        import json
        # Use the internal _process_input to check if the file exists and process it.
        contents = self._process_input(pdf_path, prompt)
        # Import the types from google.genai inside the service (hidden from analytics.py)
        from google.genai import types as genai_types
        response = self.client.models.generate_content(
            model=self.model,
            config=genai_types.GenerateContentConfig(system_instruction=prompt),
            contents=contents
        )
        raw_response = response.text.strip()
        # Remove code fences if present.
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()
        try:
            result = json.loads(raw_response)
        except Exception as e:
            raise Exception(f"Error parsing PDF analysis response: {e}. Raw response: {raw_response}")
        return result

    def generate_action_points(self, documents_json: str, prompt: str) -> dict:
        print("DEBUG: Generating action points using LLM...", flush=True)
        contents = [documents_json, prompt]
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(system_instruction=prompt),
            contents=contents
        )
        raw_response = response.text.strip()
        print("DEBUG: Gemini API generate action points response:", raw_response, flush=True)
        # Remove code fences if present
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()
        try:
            result = json.loads(raw_response)
        except Exception as e:
            raise Exception(f"Error parsing generate action points response: {e}. Raw response: {raw_response}")
        return result
