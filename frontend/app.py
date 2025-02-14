from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv
import yaml
import json

# Load environment variables from the .env file located at the root.
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path)

# Load configuration from config/config.yaml (located at the root)
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Read the name of the environment variable holding the Gemini API key from the config.
gemini_api_key_env_var = config.get('gemini_api_key_env_var', 'GEMINI_API_KEY')
api_key = os.getenv(gemini_api_key_env_var)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    # Path to the PDF file (relative to the frontend folder)
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources', 'e10894e5-eb42-4ac6-aa7d-afee1e87f8af.pdf')
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
    except Exception as e:
        return jsonify({'response': f"Error reading PDF: {e}", 'page': None})
    
    # Create an enhanced prompt to instruct Gemini to return structured JSON output.
    enhanced_prompt = f"""
{user_message}

Based on the content of the provided PDF document, please provide a detailed answer to the query.
Return the answer in JSON format following the schema below EXACTLY:

{{
  "response": "<Your answer as text>",
  "page": <Relevant page number as an integer>
}}

Ensure that your output is valid JSON and nothing else.
"""

    from google import genai
    from google.genai import types

    # Initialize the client with the API key.
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                # Upload the PDF file as a part.
                types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                # Pass the enhanced prompt.
                enhanced_prompt
            ]
        )
        raw_response = response.text

        # Print the raw response for debugging.
        print("Raw Gemini response:", raw_response)

        # Remove Markdown code fences if present.
        cleaned_response = raw_response
        if cleaned_response.startswith("```"):
            lines = cleaned_response.splitlines()
            # Remove first line if it's a fence.
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            # Remove last line if it's a fence.
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned_response = "\n".join(lines).strip()
            print("Cleaned Gemini response:", cleaned_response)

        # Parse the JSON response from Gemini.
        parsed_response = json.loads(cleaned_response)
        answer_text = parsed_response.get("response", "")
        page_number = parsed_response.get("page", None)

        # Prepare a combined string for display in the chat.
        combined_response = f"Answer: {answer_text} (Page {page_number})"
    except Exception as e:
        print("Error parsing Gemini response:", raw_response)
        combined_response = f"Error calling Gemini API or parsing response: {e}"
        page_number = None
    
    return jsonify({'response': combined_response, 'page': page_number})

@app.route('/pdf')
def pdf():
    # Serve the PDF file for the right panel.
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources')
    filename = 'e10894e5-eb42-4ac6-aa7d-afee1e87f8af.pdf'
    return send_from_directory(directory, filename)

if __name__ == '__main__':
    app.run(debug=True)
