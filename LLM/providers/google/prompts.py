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

FILTER_QUERY_DOCUMENTS_PROMPT = """
You are given a corpus of document metadata in JSON format:
{documents_json}

And a user query:
"{query}"

Using the above information, select and rank the top {doc_count} documents that best match the query.
Return the result as a JSON array of objects, where each object follows this schema:
{{
  "id": string,
  "url": string,
  "pdf_file": string,
  "title": string,
  "content_hash": string,
  "description": string,
  "relevance": number
}}

Ensure that the output is valid JSON.
"""


def build_chat_prompt(user_message: str) -> str:
    """
    Build the prompt to instruct Gemini to generate a JSON response with two fields:
    - "response": the answer text.
    - "page": the relevant page number, or 1 if the answer is not specific to any page.
    """
    prompt = f"""
      {user_message}

      Based on the content of the provided PDF document, please provide a detailed answer to the query.
      Return the answer in JSON format following the schema below EXACTLY:

      {{
        "response": "<Your answer as text>",
        "page": <Relevant page number as an integer. If the answer is not specific to any page, return 1>
      }}

      Use markdown to better format the 'response' part.

      Ensure that your output is valid JSON and nothing else.
    """
    return prompt.strip()


DOCUMENT_CLUSTERING_PROMPT = """ 
You are an expert in the Ethereum Ecosystem sectors. Given the following JSON array of documents, 
where each document has a "title" and a "description" field, perform a detailed clustering of the 
documents based on the sector, vertical, or domain of the Ethereum Ecosystem that they pertain to. 
For each cluster, please provide:

- A concise label that best describes the sector.

- A list of document titles that belong to that cluster.

- 1–3 key common takeaways that capture useful signals or trends from the documents in that cluster. 
    
Only include takeaways that are clearly supported by the document descriptions. Ensure that every 
document in the input appears in your output. If any document does not clearly belong to a specific 
cluster, assign it to an "Other" cluster. Additionally, include a key "unassigned" that lists any 
document titles not assigned to a cluster (this should be empty if all documents are properly assigned), 
and include a summary count that confirms the total number of documents processed matches the input. 
Return your answer as a JSON object where each key is a cluster label and its value is an object with 
two keys: 

"documents": a list of document titles, 
"takeaways": a list of key common takeaways. 

JSON input: {documents_json} """

DOCUMENT_UPDATES_PROMPT = """
You are an expert at drafting engaging and well-formatted Discord posts about technical documents in the Ethereum Ecosystem. Given the following JSON array of documents, where each document has the fields "title", "short_description" (or "description" as a fallback), and "authors", generate for each document a Discord post.
For each document, create a post with:
- A title in the format "Conversation with [title]". If the document title is missing, use "Conversation" on its own.
- A short description that summarizes the document.
- Up to 3 key takeaways that capture important insights from the document.
- A section explaining who this document is relevant to and why.
- A "Vibe check" represented by a single emoji that best describes the overall feeling or mood of the document.
If any details are missing, leave the corresponding section empty.
Return your answer as a JSON array where each element is an object with the following keys:
    "post_title": string,
    "description": string,
    "takeaways": array of strings,
    "relevance": string,
    "vibe": string
JSON input:
{documents_json}
"""

OVERALL_SUMMARY_AND_TOPICS_PROMPT = """
You are a document analysis expert. Analyze the attached PDF document and provide a concise overall summary and identify the key topics and themes present in the document.

Instructions:
1. Overall Summary: Write a short, clear narrative that captures the main idea and flow of the document.
2. Key Topics & Themes: Identify and list the central themes, subjects, or recurring topics that appear in the document.

Return your answer as a JSON object exactly in the following format:

{
  "overall_summary": "<Your overall summary text>",
  "key_topics_and_themes": ["<topic 1>", "<topic 2>", ...]
}
"""
