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
You are an expert at drafting engaging and well-formatted Discord posts about technical documents in the Ethereum Ecosystem. Given the following JSON array of documents (each document includes the fields "id", "title", "short_description" [or "description" as a fallback], "authors", and optionally "date"), generate for each document a Discord post in markdown exactly in the following format:

## EF x [Document Title] ([Formatted Date])

**Participants:** EF → [Author from the Ethereum Foundation], [Partner Organization] → [All other authors]

**About:** [Short description of the document]

**Highlights**
- [Highlight 1]
- [Highlight 2]
- [Highlight 3]

**Products**
- [Product 1]
- [Product 2]

**Challenges**
- [Challenge 1]
- [Challenge 2]
- [Challenge 3]

If a section has no content, omit that section or leave it empty. Format the date as “Mon D, YYYY” (e.g. “Apr 1, 2025”). Use markdown formatting exactly as shown.

Return your answer as a JSON array where each element is an object with the keys "id" and "discord_post", where "id" is the document id and "discord_post" is the complete markdown string for that document.

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

TEAM_RELEVANCE_PROMPT = """
You are an expert at determining team relevance within the Ethereum Foundation. You are given a document analysis and a mapping of Ethereum Foundation teams to the topics they care about.

Document Analysis:
Overall Summary: {overall_summary}
Key Topics & Themes: {key_topics}

Team Topics Mapping:
{team_topics_json}

Based on the above, identify which Ethereum Foundation teams would find this document most relevant. For each team, list the specific topics from the document analysis that match the topics they care about. Return your answer as a JSON object where each key is a team name and its value is a list of matched topics.
"""

TEAM_RELEVANCE_CHUNKS_PROMPT = """
You are an expert in analyzing document content and linking it to relevant Ethereum Foundation teams. You are given:
Overall Summary: {overall_summary}
Key Topics & Themes: {key_topics}

Team Topics Mapping:
{team_topics_json}

For each Ethereum Foundation team that is relevant, identify specific segments of the document that illustrate that relevance. For each segment, provide:
- The page number where the segment occurs.
- A short snippet (no more than 200 characters) from that page that captures the relevant content.
- The matched topics from the document that triggered this relevance.

Return your answer as a JSON object where each key is a team name and its value is an array of objects with the following keys:
  "page": <page number as an integer>,
  "snippet": "<short snippet of the document text>",
  "matched_topics": ["<topic 1>", "<topic 2>", ...]
"""

TOPIC_FLOW_PROMPT = """
You are an expert in document analysis. Your task is to segment the attached PDF document into a sequential topic flow.
Please divide the document into a series of semantic chunks based on the topics being discussed. For each chunk, provide:
- The page number where the chunk starts (as an integer).
- A concise title summarizing the topic of that chunk.
- A short snippet (up to 200 characters) that captures the essence of the chunk.
Return your answer as a JSON array of objects, each with the keys:
  "page", "title", "snippet".
Ensure that the segments cover the document in sequence from beginning to end.
"""

TEAM_RELEVANCE_FOR_CHUNKS_PROMPT = """
You are an expert in linking document content to relevant Ethereum Foundation teams and assessing the urgency of the content.
You are given:
1. A list of document chunks. Each chunk is an object with the following fields:
   - Page: The starting page number of the chunk.
   - Title: A concise title summarizing the topic of the chunk.
   - Snippet: A short excerpt (up to 200 characters) that captures the essence of the chunk.
2. A mapping of Ethereum Foundation teams to the topics they care about, provided as JSON:
{team_topics_json}

For each chunk, determine:
   - The "matched_team": the Ethereum Foundation team most directly relevant to the chunk based on the provided mapping, or "none" if no team is directly relevant.
   - The "matched_topics": a list of topics from the mapping that are present in the chunk (or an empty list if none).
   - The "escalation_level": an integer from 1 to 5, where 5 indicates highly urgent, emotionally charged, or action-oriented content, and 1 indicates general discussion with minimal urgency.

Return your answer as a JSON array of objects (one per chunk) with the following keys:
   "page", "matched_team", "matched_topics", "escalation_level".

Sort the array in ascending order by page number.
"""

TEAM_ACTION_POINTS_PROMPT = """
You will be given two documents:
1. A JSON mapping of Ethereum Teams to the topics they focus on.
2. A PDF document containing technical details and context about a technical topic in the Ethereum Ecosystem. The title of the document is: {document_title}

Your task is as follows:
- Read the PDF document thoroughly.
- Instead of identifying actionable recommendations, scan the document for any snippets of text that clearly express a negative emotion such as disappointment, confusion, anger, or regret.
- For every snippet that exhibits any of these negative emotions, return an entry using the same JSON structure as for action points.
- For each identified snippet, set the "team" field to "Negative Emotion" and the "action" field to the exact snippet from the document.
- If no such snippets are found, return a single entry with the "team" field set to "Negative Emotion" and the "action" field set to "No relevant actions or teams found".

Return your answer as a JSON object with the following structure:

{{
    "title": "<Document Title>",
    "action_points": [
         {{
            "team": "<For each snippet, use 'Negative Emotion'>",
            "action": "<The snippet of text that shows negative emotion>"
         }},
         ...
    ]
}}

Team Topics Mapping:
{team_topics_json}
"""
