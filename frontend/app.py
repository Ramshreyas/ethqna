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
    g
)
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
import logging
from logging.handlers import RotatingFileHandler

# Import the prompt builder
from LLM.providers.google.prompts import build_chat_prompt
from LLM.providers.google.service import LLMService

# Load environment variables from the project root .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path)

# Load configuration from config/config.yaml
def load_config(config_file='config/config.yaml'):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

# Get LLM provider from config
def get_llm_provider():
    """
    Dynamically load and return an instance of LLMService based on the config.
    Each provider module should export a concrete class named 'LLMService'
    that implements summarize(text: str) -> str.
    """
    config = load_config()
    provider_name = config.get("long_context_llm", "dummy").lower()
    module_path = f"LLM.providers.{provider_name}.service"
    try:
        provider_module = importlib.import_module(module_path)
        provider_class = getattr(provider_module, "LLMService")
        return provider_class()
    except Exception as e:
        raise Exception(f"Error loading LLM provider '{provider_name}': {e}")

llm_service = get_llm_provider()

# Set development mode flag (set DEV_MODE=1 in your environment for local testing)
DEV_MODE = os.environ.get('DEV_MODE', '0') == '1'

app = Flask(__name__)
app.secret_key = "supersekrit"  # Replace with a secure key in production

# Force Flask to generate HTTPS URLs and trust reverse-proxy headers.
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set up logging to a file stored in the data folder (mounted volume)
usage_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'usage.log')
handler = RotatingFileHandler(usage_log_path, maxBytes=1_000_000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

@app.before_request
def log_request_info():
    # Default to unauthenticated
    user_email = "unauthenticated"
    try:
        # Attempt to fetch Google user info only if the blueprint is ready.
        from flask_dance.contrib.google import google
        if google.authorized:
            resp = google.get("/oauth2/v2/userinfo")
            if resp.ok:
                user_info = resp.json()
                user_email = user_info.get("email", "unknown")
    except Exception as e:
        app.logger.error(f"Error fetching user info: {e}")
    app.logger.info(f"{request.remote_addr} {request.method} {request.path} by {user_email}")

# Load configuration for Gemini API from config/config.yaml
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
gemini_api_key_env_var = config.get('gemini_api_key_env_var', 'GEMINI_API_KEY')
api_key = os.getenv(gemini_api_key_env_var)

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

@app.route("/sources")
def sources_list():
    sources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sources.json')
    if os.path.exists(sources_path):
        try:
            with open(sources_path, 'r') as f:
                sources = json.load(f)
            return jsonify(sources)
        except Exception as e:
            return jsonify({"error": f"Failed to load sources: {e}"}), 500
    else:
        return jsonify({"error": "Sources file not found"}), 404

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
    if DEV_MODE:
        user_info = {"email": "local@test.com", "name": "Local Tester"}
        return render_template("ethqna.html", user=user_info)
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
    if DEV_MODE:
        user_info = {"email": "local@test.com", "name": "Local Tester"}
        return render_template("index.html", user=user_info)
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
    # Get the document filename from the request; default if not provided.
    doc_filename = data.get("doc", "41dd8407-7914-4978-a078-8dc597d8fb86.pdf")
    print(f"Received chat request: message='{user_message}', doc_filename='{doc_filename}'", flush=True)
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources', doc_filename)
    print(f"Computed PDF path: {pdf_path}", flush=True)
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        print(f"Successfully read PDF file: {doc_filename}", flush=True)
    except Exception as e:
        print(f"Error reading PDF file at {pdf_path}: {e}", flush=True)
        return jsonify({"response": f"Error reading PDF: {e}", "page": None})

    enhanced_prompt = build_chat_prompt(user_message)
    print(f"Built chat prompt: {enhanced_prompt}", flush=True)

    try:
        response = llm_service.chat(pdf_data, enhanced_prompt)
        answer_text = response.get("response", "")
        page_number = response.get("page", None)
        combined_response = f"Answer: {answer_text} (Page {page_number})"
    except Exception as e:
        print("Error in LLM chat service:", e, flush=True)
        combined_response = f"Error calling LLM chat service: {e}"
        page_number = None

    print(f"Returning response: {combined_response}", flush=True)
    return jsonify({'response': combined_response, 'page': page_number})


@app.route("/pdf")
def pdf():
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources')
    pdf_file = request.args.get('doc', '41dd8407-7914-4978-a078-8dc597d8fb86.pdf')
    return send_from_directory(directory, pdf_file)

@app.route("/query/filter_documents", methods=["POST"])
def filter_documents():
    req_data = request.get_json()
    topic = req_data.get("topic", "")
    selected_sources = req_data.get("sources", [])  # expects an array of source names
    doc_count = req_data.get("doc_count", 3)

    # Load documents from the JSON file
    documents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pdf_sources', 'documents.json')
    if not os.path.exists(documents_path):
        return jsonify({"error": "Documents file not found"}), 404
    try:
        with open(documents_path, "r") as f:
            docs = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Error loading documents: {e}"}), 500

    # Filter documents based on the selected sources
    filtered_docs = [doc for doc in docs.values() if doc.get("source", "") in selected_sources]
    documents_json = json.dumps(filtered_docs)

    # Build the prompt using the new prompt constant
    from LLM.providers.google.prompts import FILTER_QUERY_DOCUMENTS_PROMPT
    prompt = FILTER_QUERY_DOCUMENTS_PROMPT.format(
        documents_json=documents_json,
        query=topic,
        doc_count=doc_count
    )

    try:
        result = llm_service.filter_documents(documents_json, prompt)
    except Exception as e:
        return jsonify({"error": f"LLM service error: {e}"}), 500

    return jsonify({"documents": result})

@app.route("/analytics")
def analytics():
    """
    Renders the analytics page (analytics.html).
    Requires user to be logged in with an @ethereum.org email.
    """
    if DEV_MODE:
        user_info = {"email": "local@test.com", "name": "Local Tester"}
        return render_template("analytics.html", user=user_info)

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

    return render_template("analytics.html", user=user_info)


@app.route("/analytics/data", methods=["GET"])
def analytics_data():
    """
    Provides JSON-aggregated analytics from documents.json,
    optionally filtered by 'source'.
    """
    source_filter = request.args.get("source", "")  # e.g. "vitalik.eth.limo"

    documents_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "data",
        "pdf_sources",
        "documents.json"
    )
    if not os.path.exists(documents_path):
        return jsonify({"error": "documents.json not found"}), 404

    try:
        with open(documents_path, "r") as f:
            docs_dict = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Error reading documents.json: {e}"}), 500

    # Convert to list of doc objects
    documents = list(docs_dict.values())

    # If there's a source_filter, only keep docs whose 'source' matches
    if source_filter:
        documents = [d for d in documents if d.get("source", "") == source_filter]

    total_docs = len(documents)

    # Gather all authors
    all_authors = set()
    for doc in documents:
        authors = doc.get("authors", [])
        for a in authors:
            all_authors.add(a)
    unique_authors_count = len(all_authors)

    # Earliest & latest date
    dates = []
    for doc in documents:
        date_str = doc.get("date", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(dt)
        except:
            pass
    earliest = min(dates).strftime("%Y-%m-%d") if dates else "N/A"
    latest = max(dates).strftime("%Y-%m-%d") if dates else "N/A"

    # Return the docs + basic summary
    return jsonify({
        "analytics": {
            "total_docs": total_docs,
            "unique_authors_count": unique_authors_count,
            "earliest_date": earliest,
            "latest_date": latest
        },
        "documents": documents
    })

@app.route('/analytics/<path:filename>')
def analytics_static(filename):
    print(f"Attempting to serve analytics file: {filename}", flush = True)
    return send_from_directory(os.path.join(app.root_path, 'templates', 'analytics'), filename)

@app.route("/fetch_analytics", methods=["POST"])
def api_analytics():
    """
    Expects a JSON payload like: { "sources": ["vitalik.eth.limo", "Reddit AMA"] }
    Reads analytics.json from /data/pdf_sources and returns:
      - available_sources: a list of sources that have analytics panels.
      - visualizations: a de-duplicated list of panel file paths for the selected sources.
    If no sources are provided, returns panels for all available sources.
    """
    data = request.get_json() or {}
    selected_sources = data.get("sources", [])
    
    analytics_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "..", "data", "pdf_sources", "analytics.json"
    )
    if not os.path.exists(analytics_path):
        return jsonify({"error": "analytics.json not found"}), 404
    
    try:
        with open(analytics_path, "r") as f:
            analytics_data = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Error reading analytics.json: {e}"}), 500
    
    # Build available_sources: keys with non-empty lists.
    available_sources = [ key for key, value in analytics_data.items() if value ]
    
    # If no sources selected, default to all available.
    if not selected_sources:
        selected_sources = available_sources

    # Collect panel file paths for the selected sources.
    result = []
    for source in selected_sources:
        result.extend(analytics_data.get(source, []))
    
    # Remove duplicates. If the items are dicts or strings, handle appropriately.
    seen = set()
    unique = []
    for item in result:
        if isinstance(item, dict):
            key = (item.get("title"), item.get("path"))
        else:
            key = item
        if key not in seen:
            seen.add(key)
            unique.append(item)
    result = unique

    return jsonify({
        "available_sources": available_sources,
        "visualizations": result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
