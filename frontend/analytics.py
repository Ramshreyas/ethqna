import os
import json
from datetime import datetime
import logging
from collections import defaultdict, Counter
from LLM.providers.google.service import LLMService
import hashlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def load_documents():
    """Load documents from documents.json."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    documents_path = os.path.join(base_dir, "..", "data", "pdf_sources", "documents.json")
    logger.debug("Loading documents from: %s", documents_path)
    try:
        with open(documents_path, "r") as f:
            docs = json.load(f)
        return docs
    except Exception as e:
        logger.error("Error loading documents: %s", e)
        return {}

def filter_documents(docs, selected_sources, start_date=None, end_date=None):
    """
    Filters the loaded documents based on selected_sources and optional date range.
    Returns a list of documents.
    """
    filtered = []
    for doc in docs.values():
        # Filter by source.
        source = (doc.get("source") or "").strip()
        if selected_sources:
            if source.lower() not in [s.lower() for s in selected_sources]:
                continue

        # Filter by date range.
        date_str = doc.get("date") or ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception as e:
            logger.debug("Error parsing date '%s': %s", date_str, e)
            continue

        if start_date and dt < start_date:
            continue
        if end_date and dt > end_date:
            continue

        filtered.append(doc)
    return filtered

def get_summary_data(selected_sources, start_date=None, end_date=None):
    """
    Returns aggregated data for analytics:
      - summary: dict with total_docs, unique_authors_count, earliest_date, latest_date.
      - time_series: list of {date, count} objects sorted by date.
      - word_cloud: list of {tag, count} objects.
    """
    docs = load_documents()
    filtered_docs = filter_documents(docs, selected_sources, start_date, end_date)
    logger.debug("Filtered documents count: %d", len(filtered_docs))
    
    # Build summary.
    total_docs = len(filtered_docs)
    authors = set()
    dates = []
    for doc in filtered_docs:
        for author in doc.get("authors") or []:
            authors.add(author)
        date_str = doc.get("date") or ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(dt)
        except Exception as e:
            logger.debug("Error parsing date '%s': %s", date_str, e)
    
    unique_authors_count = len(authors) if authors else "-"
    earliest_date = min(dates).strftime("%Y-%m-%d") if dates else "-"
    latest_date = max(dates).strftime("%Y-%m-%d") if dates else "-"
    summary = {
        "total_docs": total_docs if total_docs > 0 else "-",
        "unique_authors_count": unique_authors_count,
        "earliest_date": earliest_date,
        "latest_date": latest_date
    }
    
    # Build time series: count docs per date.
    date_counts = defaultdict(int)
    for dt in dates:
        date_str = dt.strftime("%Y-%m-%d")
        date_counts[date_str] += 1
    time_series = [{"date": date, "count": count} for date, count in sorted(date_counts.items())]
    
    # Build word cloud: count frequency of tags.
    tag_counter = Counter()
    for doc in filtered_docs:
        tags = doc.get("tags") or []
        tag_counter.update(tags)
    word_cloud = [{"tag": tag, "count": count} for tag, count in tag_counter.items()]
    
    logger.debug("Summary: %s", summary)
    logger.debug("Time series: %s", time_series)
    logger.debug("Word cloud: %s", word_cloud)
    
    return {
        "summary": summary,
        "time_series": time_series,
        "word_cloud": word_cloud
    }

def get_analytics_summary(selected_sources, start_date=None, end_date=None):
    """
    Returns a summary including total_docs, unique_authors_count, earliest_date, latest_date.
    """
    docs = load_documents()
    filtered_docs = filter_documents(docs, selected_sources, start_date, end_date)
    logger.debug("Filtered documents count: %d", len(filtered_docs))
    
    total_docs = len(filtered_docs)
    authors = set()
    dates = []
    for doc in filtered_docs:
        for author in doc.get("authors") or []:
            authors.add(author)
        date_str = doc.get("date") or ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(dt)
        except Exception as e:
            logger.debug("Error parsing date '%s': %s", date_str, e)
            continue
    summary = {
        "total_docs": total_docs if total_docs > 0 else "-",
        "unique_authors_count": len(authors) if authors else "-",
        "earliest_date": min(dates).strftime("%Y-%m-%d") if dates else "-",
        "latest_date": max(dates).strftime("%Y-%m-%d") if dates else "-"
    }
    
    logger.debug("Analytics summary computed: %s", summary)
    return summary

def get_document_analysis_data(selected_sources, start_date=None, end_date=None):
    docs = load_documents()
    filtered_docs = filter_documents(docs, selected_sources, start_date, end_date)
    
    # Prepare input for clustering: only include documents with a description.
    clustering_input = []
    for doc in filtered_docs:
        if doc.get("description"):
            clustering_input.append({
                "title": doc.get("title") or "Untitled",
                "description": doc.get("description")
            })
    
    # Serialize the input in a deterministic way (sorted keys)
    documents_json = json.dumps(clustering_input, sort_keys=True)
    
    # Compute a hash for the input configuration
    input_hash = hashlib.md5(documents_json.encode('utf-8')).hexdigest()
    
    # Determine the cache file path (ensure the analytics cache directory exists)
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "analytics")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = os.path.join(cache_dir, f"clusters_{input_hash}.json")
    
    # Check if the cache file exists; if so, load and return the cached clusters.
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                clusters = json.load(f)
            return {"clusters": clusters}
        except Exception as e:
            # If there's an error reading the cache, proceed to run inference.
            print(f"Error reading cache file: {e}")
    
    # Call the LLM service to cluster documents if no cached result exists.
    try:
        llm = LLMService()
        from LLM.providers.google.prompts import DOCUMENT_CLUSTERING_PROMPT
        prompt = DOCUMENT_CLUSTERING_PROMPT.format(documents_json=documents_json)
        clusters = llm.cluster_documents(documents_json, prompt)
    except Exception as e:
        clusters = {"error": f"Clustering failed: {e}"}
    
    # Cache the inference result for future use.
    try:
        with open(cache_file, "w") as f:
            json.dump(clusters, f)
    except Exception as e:
        print(f"Error writing cache file: {e}")
    
    return {"clusters": clusters}
