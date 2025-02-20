SYSTEM_PROMPT = (
    "You are a helpful document processing and analysis assistant. "
    "You will act upon text provided to you according to the instructions given below. "
    "The text will follow the instruction provided below."
)

METADATA_PROMPT = (
  """
  Task: Extract structured metadata from the following PDF document. Return the metadata in a valid JSON format.

Instructions:
Analyze the document and extract the following fields:

    Title - The document’s title, if available.
    Date - The date the document was created or published. If not explicitly mentioned, infer the most likely date from the content.
    Authors - The names of the authors, creators, or organizations responsible for the document.
    Short Description - A concise summary (2-3 sentences) describing the main purpose or key insights of the document.
    Tags - A list of relevant topics, themes, or keywords extracted from the document. Use concise, meaningful words.

Example Output:

{
  "title": "Ethereum Scaling Strategies: A Research Overview",
  "date": "2023-10-15",
  "authors": ["Vitalik Buterin", "Ethereum Foundation Research Team"],
  "short_description": "This paper explores various scaling solutions for Ethereum, including rollups, sharding, and data availability layers. It discusses their trade-offs and future research directions.",
  "tags": ["Ethereum", "scaling", "rollups", "sharding", "data availability"]
}

Ensure the output follows this JSON format and accurately reflects the content of the document. If any field is missing, infer the best possible answer or leave it as null.
"""
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
