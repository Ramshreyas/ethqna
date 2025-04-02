import os
import json
import time
import requests
from requests.auth import HTTPBasicAuth

# Configuration
GITHUB_CONTENT_URL = "https://api.github.com/repos/ethereum/EIPs/contents/EIPS"
INGEST_ENDPOINT = "http://localhost:8000/documents/from_url"
BASIC_AUTH_USERNAME = "admin"  # Replace with your username
BASIC_AUTH_PASSWORD = "kghr589jkbffjknfd57imbg9nm"  # Replace with your password
PROCESSED_FILE = "processed_files.json"
MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # seconds

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return json.load(f)
    return {}

def save_processed(processed):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed, f, indent=2)

def fetch_github_files():
    response = requests.get(GITHUB_CONTENT_URL)
    response.raise_for_status()
    files = response.json()
    # Filter for markdown files (optional) and files only
    return [f for f in files if f.get("type") == "file" and f.get("name", "").endswith(".md")]

def ingest_file(file_name):
    # Construct the GitHub URL in the format expected by your endpoint
    file_url = f"https://github.com/ethereum/EIPs/blob/master/EIPS/{file_name}"
    payload = {
        "url": file_url,
        "source": "EIPs"
    }
    headers = {"Content-Type": "application/json"}
    
    retries = 0
    backoff = INITIAL_BACKOFF
    while retries < MAX_RETRIES:
        try:
            response = requests.post(INGEST_ENDPOINT,
                                     json=payload,
                                     headers=headers,
                                     auth=HTTPBasicAuth(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
                                     timeout=100)
            # Check for HTTP success (200-299)
            if response.status_code >= 200 and response.status_code < 300:
                print(f"Successfully ingested {file_name}")
                return True
            else:
                print(f"Error ingesting {file_name}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception ingesting {file_name}: {e}")
        
        retries += 1
        print(f"Retrying in {backoff} seconds... (Attempt {retries+1}/{MAX_RETRIES})")
        time.sleep(backoff)
        backoff *= 2  # Exponential backoff

    print(f"Failed to ingest {file_name} after {MAX_RETRIES} attempts.")
    return False

def main():
    processed = load_processed()
    try:
        files = fetch_github_files()
    except Exception as e:
        print("Error fetching GitHub files:", e)
        return

    for file_info in files:
        file_name = file_info.get("name")
        if file_name in processed and processed[file_name] == "complete":
            print(f"Skipping {file_name} (already processed).")
            continue

        print(f"Processing {file_name} ...")
        success = ingest_file(file_name)
        processed[file_name] = "complete" if success else "pending"
        save_processed(processed)

if __name__ == "__main__":
    main()
