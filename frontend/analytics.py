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
    
    # Build a mapping of document title to its pdf_file.
    title_to_pdf = {}
    for doc in filtered_docs:
        if doc.get("description") and doc.get("pdf_file"):
            title = doc.get("title") or "Untitled"
            title_to_pdf[title] = doc.get("pdf_file")
    
    import json
    clustering_input = []
    for doc in filtered_docs:
        if doc.get("description"):
            clustering_input.append({
                "title": doc.get("title") or "Untitled",
                "description": doc.get("description")
            })
    
    # Serialize input deterministically and compute a hash.
    documents_json = json.dumps(clustering_input, sort_keys=True)
    import hashlib
    input_hash = hashlib.md5(documents_json.encode('utf-8')).hexdigest()
    
    import os
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "analytics")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = os.path.join(cache_dir, f"clusters_{input_hash}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                clusters = json.load(f)
            return {"clusters": clusters, "pdf_mapping": title_to_pdf}
        except Exception as e:
            print(f"Error reading cache file: {e}")
    
    # Call LLM service for clustering if no cached result exists.
    try:
        llm = LLMService()
        from LLM.providers.google.prompts import DOCUMENT_CLUSTERING_PROMPT
        prompt = DOCUMENT_CLUSTERING_PROMPT.format(documents_json=documents_json)
        clusters = llm.cluster_documents(documents_json, prompt)
    except Exception as e:
        clusters = {"error": f"Clustering failed: {e}"}
    
    try:
        with open(cache_file, "w") as f:
            json.dump(clusters, f)
    except Exception as e:
        print(f"Error writing cache file: {e}")
    
    return {"clusters": clusters, "pdf_mapping": title_to_pdf}

def get_updates_analysis_data(selected_sources, start_date=None, end_date=None):
    docs = load_documents()
    filtered_docs = filter_documents(docs, selected_sources, start_date, end_date)
    
    # Build a mapping from document title to its pdf_file.
    title_to_pdf = {}
    for doc in filtered_docs:
        if doc.get("pdf_file") and doc.get("title"):
            title_to_pdf[doc.get("title")] = doc.get("pdf_file")
    
    # Build the input for the Updates analysis.
    # Use "short_description" if available, otherwise fall back to "description".
    updates_input = []
    for doc in filtered_docs:
        updates_input.append({
            "title": doc.get("title") or "",
            "short_description": doc.get("short_description") or doc.get("description") or "",
            "authors": doc.get("authors") or []
        })
    
    import json
    documents_json = json.dumps(updates_input, sort_keys=True)
    
    import hashlib
    input_hash = hashlib.md5(documents_json.encode('utf-8')).hexdigest()
    
    import os
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "analytics")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = os.path.join(cache_dir, f"updates_{input_hash}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                posts = json.load(f)
            return {"posts": posts, "pdf_mapping": title_to_pdf}
        except Exception as e:
            print(f"Error reading cache file: {e}")
    
    try:
        llm = LLMService()
        from LLM.providers.google.prompts import DOCUMENT_UPDATES_PROMPT
        prompt = DOCUMENT_UPDATES_PROMPT.format(documents_json=documents_json)
        posts = llm.cluster_documents(documents_json, prompt)
    except Exception as e:
        posts = {"error": f"Updates analysis failed: {e}"}
    
    try:
        with open(cache_file, "w") as f:
            json.dump(posts, f)
    except Exception as e:
        print(f"Error writing cache file: {e}")
    
    return {"posts": posts, "pdf_mapping": title_to_pdf}

def get_pdf_overall_summary_and_topics(pdf_path):
    """
    Given the path to a PDF file, returns an analysis containing:
      - overall_summary: A concise narrative capturing the document's main idea and flow.
      - key_topics_and_themes: A list of central themes and recurring topics.
    
    Uses caching based on the PDF file's binary content.
    """
    import hashlib, json, os
    # Compute a hash based on the PDF's binary content.
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        return {"error": f"Error reading PDF file: {e}"}
    input_hash = hashlib.md5(pdf_bytes).hexdigest()
    
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "analytics")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = os.path.join(cache_dir, f"overall_summary_{input_hash}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                result = json.load(f)
            return result
        except Exception as e:
            print(f"Error reading cache file: {e}")
    
    # Use the prompt without any document text injection since we are sending the PDF directly.
    from LLM.providers.google.prompts import OVERALL_SUMMARY_AND_TOPICS_PROMPT
    prompt = OVERALL_SUMMARY_AND_TOPICS_PROMPT
    
    try:
        llm = LLMService()
        result = llm.analyze_pdf(pdf_path, prompt)
    except Exception as e:
        result = {"error": f"Error generating overall summary: {e}"}
    
    try:
        with open(cache_file, "w") as f:
            json.dump(result, f)
    except Exception as e:
        print(f"Error writing cache file: {e}")
    
    return result
