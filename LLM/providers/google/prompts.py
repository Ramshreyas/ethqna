SYSTEM_PROMPT = (
    "You are a helpful document processing and analysis assistant. "
    "You will act upon text provided to you according to the instructions given below. "
    "The text will follow the instruction provided below."
)

SUMMARIZATION_PROMPT = (
    "Summarize the following PDF according to these instructions:\n"
    "1. List the top 5 topics discussed in the document.\n"
    "2. Briefly describe the discussion for each topic.\n"
    "3. Provide a more detailed description for each topic."
)

# This prompt is used to select and rank documents based on a user query.
# It takes the entire documents metadata (in JSON format) and a user query,
# and returns the top 5 documents with their metadata and a relevance score.
# The expected output is a JSON array of objects following this schema:
# {
#   "id": string,
#   "url": string,
#   "pdf_file": string,
#   "content_hash": string,
#   "description": string,
#   "relevance": number   // a relevance score between 0 and 1
# }

QUERY_DOCUMENTS_PROMPT = """
You are given a corpus of document metadata in JSON format:
{documents_json}

And a user query:
"{query}"

Using the above information, select and rank the top 5 documents that best match the query.
Return the result as a JSON array of objects, where each object follows this schema:
{{
  "id": string,
  "url": string,
  "pdf_file": string,
  "content_hash": string,
  "description": string,
  "relevance": number
}}

Ensure that the output is valid JSON.
"""

