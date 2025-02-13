import os
import uuid
import json
import hashlib
import yaml
import importlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List
from playwright.sync_api import sync_playwright
from . import map as fc_map  # Import map.py from the same package

app = FastAPI(
    title="Q&A Web App Backend API",
    description="API for managing documents (PDF conversion, content hashing, and mapping) and generating summaries via LLM.",
    version="0.4.0",
)

# PDFs and metadata are stored in data/pdf_sources.
PDF_DIR = os.path.join("data", "pdf_sources")
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

DOCUMENTS_FILE = os.path.join(PDF_DIR, "documents.json")

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

# Load stored documents from documents.json
documents = load_json(DOCUMENTS_FILE)

def load_config(config_file='config/config.yaml'):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def get_llm_provider():
    """
    Dynamically load and return an instance of LLMService based on the config.
    Each provider module should export a concrete class named 'LLMService'
    that implements the summarize(pdf_path: str, prompt: str) -> str method.
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

# Instantiate our LLM provider using configuration.
llm_service = get_llm_provider()

# Pydantic models for documents
class Document(BaseModel):
    id: str
    url: HttpUrl
    pdf_file: str
    content_hash: str
    description: str = ""  # Field for the summary/description

class DocumentCreate(BaseModel):
    url: HttpUrl

def convert_url_to_pdf(url: HttpUrl, pdf_path: str):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/101.0.4951.67 Safari/537.36"
            )
            page = context.new_page()
            page.goto(str(url), wait_until="networkidle", timeout=60000)
            page.pdf(path=pdf_path)
            browser.close()
    except Exception as e:
        raise Exception(f"Error converting URL to PDF: {str(e)}")

def get_page_content_hash(url: HttpUrl) -> str:
    """
    Returns the hash of the HTML content of the page at the given URL.
    (This is still used for caching purposes.)
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/101.0.4951.67 Safari/537.36"
            )
            page = context.new_page()
            page.goto(str(url), wait_until="networkidle", timeout=60000)
            content = page.content()
            browser.close()
            return hashlib.sha256(content.encode("utf-8")).hexdigest()
    except Exception as e:
        raise Exception(f"Error computing content hash: {str(e)}")

def process_page(url: str):
    existing_doc = None
    for d in documents.values():
        if d["url"] == str(url):
            existing_doc = d
            break

    new_hash = get_page_content_hash(url)
    if existing_doc:
        if existing_doc["content_hash"] == new_hash:
            return "unchanged", existing_doc["id"]
        else:
            pdf_path = os.path.join(PDF_DIR, existing_doc["pdf_file"])
            try:
                convert_url_to_pdf(url, pdf_path)
            except Exception as e:
                return "error", str(e)
            existing_doc["content_hash"] = new_hash
            existing_doc["description"] = llm_service.summarize(os.path.join(PDF_DIR, existing_doc["pdf_file"]))
            return "updated", existing_doc["id"]
    else:
        doc_id = str(uuid.uuid4())
        pdf_filename = f"{doc_id}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        try:
            convert_url_to_pdf(url, pdf_path)
        except Exception as e:
            return "error", str(e)
        new_doc = {
            "id": doc_id,
            "url": str(url),
            "pdf_file": pdf_filename,
            "content_hash": new_hash,
            "description": llm_service.summarize(pdf_path),
        }
        documents[doc_id] = new_doc
        return "added", doc_id

@app.get("/documents", response_model=List[Document], summary="List all documents")
def get_documents():
    return list(documents.values())

@app.post("/documents", response_model=Document, summary="Add or update a document")
def add_document(doc: DocumentCreate):
    existing_doc = None
    for d in documents.values():
        if d["url"] == str(doc.url):
            existing_doc = d
            break

    new_hash = get_page_content_hash(doc.url)
    if existing_doc:
        if existing_doc["content_hash"] == new_hash:
            return existing_doc
        else:
            pdf_path = os.path.join(PDF_DIR, existing_doc["pdf_file"])
            try:
                convert_url_to_pdf(doc.url, pdf_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            existing_doc["content_hash"] = new_hash
            existing_doc["description"] = llm_service.summarize(os.path.join(PDF_DIR, existing_doc["pdf_file"]))
            save_json(DOCUMENTS_FILE, documents)
            return existing_doc
    else:
        doc_id = str(uuid.uuid4())
        pdf_filename = f"{doc_id}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        try:
            convert_url_to_pdf(doc.url, pdf_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        new_doc = {
            "id": doc_id,
            "url": str(doc.url),
            "pdf_file": pdf_filename,
            "content_hash": new_hash,
            "description": llm_service.summarize(pdf_path),
        }
        documents[doc_id] = new_doc
        save_json(DOCUMENTS_FILE, documents)
        return new_doc

@app.delete("/documents/{doc_id}", response_model=dict, summary="Delete a document")
def delete_document(doc_id: str):
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    pdf_filename = documents[doc_id]["pdf_file"]
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    del documents[doc_id]
    save_json(DOCUMENTS_FILE, documents)
    return {"detail": "Document deleted successfully"}

@app.post("/map-sources", summary="Map sources from config using firecrawl")
def map_sources_endpoint():
    config = load_config("config/config.yaml")
    sources_to_map = config.get("sources", [])
    api_key_env_var = config.get("firecrawl_api_key_env_var", "FIRECRAWL_API_KEY")
    if not sources_to_map:
        raise HTTPException(status_code=400, detail="No sources available for mapping in config.")
    try:
        map_results = fc_map.map_sources(
            sources=sources_to_map,
            storage_path=PDF_DIR,
            api_key_env_var=api_key_env_var
        )
        return map_results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
