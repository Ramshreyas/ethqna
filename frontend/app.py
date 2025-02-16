import os
import random
import time
import json
from datetime import datetime, timedelta
import yaml

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

# Load environment variables from the project root .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = "supersekrit"  # Replace with a secure key in production

# Load configuration for Gemini API from config/config.yaml
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
gemini_api_key_env_var = config.get('gemini_api_key_env_var', 'GEMINI_API_KEY')
api_key = os.getenv(gemini_api_key_env_var)

# Import the prompt builder
from prompts import build_prompt

# Persistent store file for pending verification codes
PENDING_VERIFICATIONS_FILE = os.path.join(app.root_path, 'pending_verifications.json')

def load_pending_verifications():
    if not os.path.exists(PENDING_VERIFICATIONS_FILE):
        return {}
    try:
        with open(PENDING_VERIFICATIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading pending verifications:", e)
        return {}

def save_pending_verifications(data):
    try:
        with open(PENDING_VERIFICATIONS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print("Error saving pending verifications:", e)

# --- Authentication Endpoints ---

@app.route("/")
def index():
    # If not authenticated, redirect to the auth page.
    if not request.cookies.get("auth"):
        return redirect(url_for("auth"))
    return render_template("index.html")

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/send-code", methods=["POST"])
def send_code():
    data = request.get_json()
    email_handle = data.get("email_handle", "").strip()
    if not email_handle:
        return jsonify({"status": "error", "message": "Email handle is required."}), 400

    full_email = f"{email_handle}@ethereum.org"
    code = str(random.randint(100000, 999999))
    expiry = time.time() + 5 * 60  # 5 minutes expiry

    pending = load_pending_verifications()
    pending[full_email] = {"code": code, "expiry": expiry}
    save_pending_verifications(pending)

    # For demonstration, we print the code.
    print(f"Sending verification code to {full_email}: {code}")
    return jsonify({"status": "sent", "message": "Verification code sent."})

@app.route("/verify-code", methods=["POST"])
def verify_code():
    data = request.get_json()
    email_handle = data.get("email_handle", "").strip()
    code_submitted = data.get("code", "").strip()
    if not email_handle or not code_submitted:
        return jsonify({"status": "error", "message": "Email handle and code are required."}), 400

    full_email = f"{email_handle}@ethereum.org"
    pending = load_pending_verifications()
    if full_email not in pending:
        return jsonify({"status": "error", "message": "No code sent to this email."}), 400

    stored_data = pending.get(full_email)
    stored_code = stored_data.get("code")
    expiry = stored_data.get("expiry")
    if time.time() > expiry:
        pending.pop(full_email, None)
        save_pending_verifications(pending)
        return jsonify({"status": "error", "message": "Verification code expired."}), 400

    if code_submitted != stored_code:
        return jsonify({"status": "error", "message": "Incorrect verification code."}), 400

    # Verification successful; remove the pending entry.
    pending.pop(full_email, None)
    save_pending_verifications(pending)

    # Set an auth cookie valid for one month.
    resp = make_response(jsonify({"status": "verified", "message": "Email verified."}))
    expire_date = datetime.now() + timedelta(days=30)
    resp.set_cookie("auth", full_email, expires=expire_date, httponly=True)
    return resp

# --- Main Application Endpoints ---

@app.route("/chat", methods=["POST"])
def chat():
    # Ensure the user is authenticated.
    if not request.cookies.get("auth"):
        return jsonify({"response": "Not authenticated", "page": None}), 401

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
