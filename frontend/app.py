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
from werkzeug.middleware.proxy_fix import ProxyFix
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables from the project root .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = "supersekrit"  # Replace with a secure key in production

# Force Flask to generate HTTPS URLs and trust reverse-proxy headers.
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set up logging to a file in the data folder (mounted volume)
usage_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'usage.log')
handler = RotatingFileHandler(usage_log_path, maxBytes=1_000_000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

@app.before_request
def log_request_info():
    # Determine user identity if available
    user_email = "unauthenticated"
    if google.authorized:
        try:
            resp = google.get("/oauth2/v2/userinfo")
            if resp.ok:
                user_info = resp.json()
                user_email = user_info.get("email", "unknown")
        except Exception as e:
            app.logger.error("Error fetching user info: %s", e)
    # Build the log message with method, path, query string, and remote IP.
    log_message = f"User: {user_email} - {request.remote_addr} - {request.method} {request.path}"
    if request.query_string:
        log_message += "?" + request.query_string.decode('utf-8')
    app.logger.info(log_message)
    
    # For POST/PUT requests, log a summary of the request activity only.
    if request.method in ("POST", "PUT"):
        if request.content_type and "multipart/form-data" in request.content_type:
            app.logger.info("POST/PUT request with file upload: body omitted.")
        else:
            if request.data:
                try:
                    app.logger.info(f"Request body: {request.data.decode('utf-8')}")
                except Exception:
                    app.logger.info("Request body: <non-decodable content>")

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
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to="index"  # After login, redirect to the index endpoint.
)
app.register_blueprint(google_bp, url_prefix="/login")

# --- New Endpoint for PDF Documents ---
@app.route("/documents")
def documents_list():
    documents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources', 'documents.json')
    print("Looking for documents.json at:", documents_path, flush=True)
    if os.path.exists(documents_path):
        try:
            with open(documents_path, 'r') as f:
                docs_dict = json.load(f)
            docs_list = sorted(list(docs_dict.values()), key=lambda d: d.get("relevance", 0), reverse=True)
            return jsonify({"documents": docs_list})
        except Exception as e:
            return jsonify({"documents": [], "error": f"Failed to load documents: {e}"}), 500
    else:
        return jsonify({"documents": []})

@app.route("/ethqna")
def ethqna():
    if not google.authorized:
        return render_template("login.html")
    try:
        resp = google.get("/oauth2/v2/userinfo")
    except TokenExpiredError:
        return redirect(url_for("google.login"))
    except Exception:
        return redirect(url_for("google.login"))
    if not resp.ok:
        return redirect(url_for("google.login"))
    user_info = resp.json()
    email = user_info.get("email", "")
    if not email.endswith("@ethereum.org"):
        return "Access denied: You must use an ethereum.org email", 403
    return render_template("ethqna.html", user=user_info)

# --- Main Application Routes ---
@app.route("/")
def index():
    if not google.authorized:
        return render_template("login.html")
    try:
        resp = google.get("/oauth2/v2/userinfo")
    except TokenExpiredError:
        return redirect(url_for("google.login"))
    except Exception:
        return redirect(url_for("google.login"))
    if not resp.ok:
        return redirect(url_for("google.login"))
    user_info = resp.json()
    email = user_info.get("email", "")
    if not email.endswith("@ethereum.org"):
        return "Access denied: You must use an ethereum.org email", 403
    return render_template("index.html", user=user_info)

@app.route("/logout")
def logout():
    if google_bp.token:
        del google_bp.token
    return redirect(url_for("index"))

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources', '41dd8407-7914-4978-a078-8dc597d8fb86.pdf')
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
    except Exception as e:
        return jsonify({"response": f"Error reading PDF: {e}", "page": None})
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
    pdf_file = request.args.get('doc', '41dd8407-7914-4978-a078-8dc597d8fb86.pdf')
    return send_from_directory(directory, pdf_file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
