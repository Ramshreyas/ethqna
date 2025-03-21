import os
import json
from datetime import datetime
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_summary_data(selected_sources):
    """
    Loads and filters documents from documents.json based on selected_sources.
    Returns:
      - summary: a dict with total_docs, unique_authors_count, earliest_date, latest_date.
      - time_series: a list of {date, count} objects sorted by date.
      - word_cloud: a list of {tag, count} objects.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    documents_path = os.path.join(base_dir, "..", "data", "pdf_sources", "documents.json")
    logger.debug("Loading documents from: %s", documents_path)
    
    try:
        with open(documents_path, "r") as f:
            docs = json.load(f)
    except Exception as e:
        logger.error("Error loading documents: %s", e)
        return {
            "summary": {},
            "time_series": [],
            "word_cloud": []
        }
    
    # Filter documents by selected_sources if provided.
    filtered_docs = []
    for doc in docs.values():
        # Use case-insensitive comparison; if the "source" field is None, treat it as empty string.
        source = doc.get("source") or ""
        if selected_sources:
            if source.lower() in [s.lower() for s in selected_sources]:
                filtered_docs.append(doc)
        else:
            filtered_docs.append(doc)
    logger.debug("Filtered documents count: %d", len(filtered_docs))
    
    # Build summary.
    total_docs = len(filtered_docs)
    authors = set()
    dates = []
    for doc in filtered_docs:
        # If "authors" is None, default to empty list.
        for author in doc.get("authors") or []:
            authors.add(author)
        # If "date" is None, default to empty string.
        date_str = doc.get("date") or ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(dt)
        except Exception as e:
            logger.debug("Error parsing date '%s': %s", date_str, e)
    
    # If there are no authors, show '-' instead of 0.
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
        # If "tags" is None, default to an empty list.
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
        "total_docs": "-",
        "unique_authors_count": "-",
        "earliest_date": "-",
        "latest_date": "-"
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
        source = doc.get("source") or ""
        if selected_sources:
            if source.lower() in [s.lower() for s in selected_sources]:
                filtered_docs.append(doc)
        else:
            filtered_docs.append(doc)
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
    summary["total_docs"] = total_docs if total_docs > 0 else "-"
    summary["unique_authors_count"] = len(authors) if authors else "-"
    if dates:
        summary["earliest_date"] = min(dates).strftime("%Y-%m-%d")
        summary["latest_date"] = max(dates).strftime("%Y-%m-%d")
    
    logger.debug("Analytics summary computed: %s", summary)
    return summary
