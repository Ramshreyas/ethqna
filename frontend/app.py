import os
import random
import time
import json
import hashlib
import yaml
import importlib
from datetime import datetime, timedelta
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    make_response,
    send_from_directory,
)
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix  # <-- Add this

# Load environment variables from the project root .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = "supersekrit"  # Replace with a secure key in production

# Ensure Flask generates HTTPS URLs
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Wrap the app with ProxyFix so that Flask respects headers from our reverse proxy.
# This tells Flask to trust the X-Forwarded-Proto and X-Forwarded-Host headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Load configuration for Gemini API from config/config.yaml
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
gemini_api_key_env_var = config.get('gemini_api_key_env_var', 'GEMINI_API_KEY')
api_key = os.getenv(gemini_api_key_env_var)

# Import the prompt builder
from prompts import build_prompt

# --- Google OAuth Setup using Flask-Dance ---
from flask_dance.contrib.google import make_google_blueprint, google

google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_to="index"  # After login, redirect to the index endpoint.
)
app.register_blueprint(google_bp, url_prefix="/login")

# --- Main Application Routes ---

@app.route("/")
def index():
    # If the user is not authorized via Google, render the login page.
    if not google.authorized:
        return render_template("login.html")
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        # Force a re-login if userinfo cannot be retrieved.
        return redirect(url_for("google.login"))
    user_info = resp.json()
    email = user_info.get("email", "")
    # Allow only ethereum.org accounts.
    if not email.endswith("@ethereum.org"):
        return "Access denied: You must use an ethereum.org email", 403
    # User is authenticated; render the main page.
    return render_template("index.html", user=user_info)

@app.route("/logout")
def logout():
    # Clear the OAuth token to log out.
    if google_bp.token:
        del google_bp.token
    return redirect(url_for("index"))

@app.route("/chat", methods=["POST"])
def chat():
    # At this point, we assume the user is authenticated via Google.
    data = request.get_json()
    user_message = data.get("message", "")

    # Read the PDF file.
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources', 'e10894e5-eb42-4ac6-aa7d-afee1e87f8af.pdf')
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
    except Exception as e:
        return jsonify({"response": f"Error reading PDF: {e}", "page": None})

    # Build the prompt for Gemini.
    enhanced_prompt = build_prompt(user_message)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                enhanced_prompt
            ]
        )
        raw_response = response.text
        print("Raw Gemini response:", raw_response)

        # Remove Markdown code fences if present.
        cleaned_response = raw_response
        if cleaned_response.startswith("```"):
            lines = cleaned_response.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned_response = "\n".join(lines).strip()
            print("Cleaned Gemini response:", cleaned_response)

        parsed_response = json.loads(cleaned_response)
        answer_text = parsed_response.get("response", "")
        page_number = parsed_response.get("page", None)
        combined_response = f"Answer: {answer_text} (Page {page_number})"
    except Exception as e:
        print("Error parsing Gemini response:", raw_response)
        combined_response = f"Error calling Gemini API or parsing response: {e}"
        page_number = None

    return jsonify({'response': combined_response, 'page': page_number})

@app.route("/pdf")
def pdf():
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources')
    filename = 'e10894e5-eb42-4ac6-aa7d-afee1e87f8af.pdf'
    return send_from_directory(directory, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
