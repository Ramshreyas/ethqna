def build_prompt(user_message: str) -> str:
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

Ensure that your output is valid JSON and nothing else.
"""
    return prompt.strip()
