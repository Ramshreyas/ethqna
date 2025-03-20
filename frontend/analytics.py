import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug messages are emitted

def get_analytics_summary(selected_sources):
    """
    Loads documents from documents.json and filters them based on the provided selected_sources.
    Returns a summary including total document count, count of unique authors,
    and the earliest and latest document dates.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    documents_path = os.path.join(base_dir, "..", "data", "pdf_sources", "documents.json")
    logger.debug("Loading documents from: %s", documents_path)
    
    summary = {
        "total_docs": 0,
        "unique_authors_count": 0,
        "earliest_date": "N/A",
        "latest_date": "N/A"
    }
    
    if not os.path.exists(documents_path):
        logger.debug("documents.json not found at: %s", documents_path)
        return summary

    try:
        with open(documents_path, "r") as f:
            docs = json.load(f)
        logger.debug("Loaded documents.json with %d entries", len(docs))
    except Exception as e:
        logger.error("Error reading documents.json: %s", e)
        return summary

    # Filter documents based on selected_sources (if provided)
    filtered_docs = []
    for doc in docs.values():
        if selected_sources:
            if doc.get("source", "") in selected_sources:
                filtered_docs.append(doc)
        else:
            filtered_docs.append(doc)
    logger.debug("Filtered documents count: %d", len(filtered_docs))

    summary["total_docs"] = len(filtered_docs)
    
    # Compute unique authors and collect dates
    authors = set()
    dates = []
    for doc in filtered_docs:
        for author in doc.get("authors", []):
            authors.add(author)
        date_str = doc.get("date", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(dt)
        except Exception as e:
            logger.debug("Error parsing date '%s': %s", date_str, e)
            continue
    summary["unique_authors_count"] = len(authors)
    if dates:
        summary["earliest_date"] = min(dates).strftime("%Y-%m-%d")
        summary["latest_date"] = max(dates).strftime("%Y-%m-%d")
    
    logger.debug("Analytics summary computed: %s", summary)
    return summary
