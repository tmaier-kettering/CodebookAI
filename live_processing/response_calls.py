
"""
OpenAI API response handling for live text classification.

This module provides functions for making structured API calls to OpenAI's
text classification endpoints with JSON schema validation.
"""

from typing import Any, List, Union, Callable
from pydantic import ValidationError
from settings import config, secrets_store
from openai import OpenAI

# Initialize OpenAI client with stored API key
try:
    OPENAI_API_KEY = secrets_store.load_api_key()
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    # Handle cases where keyring is not available (testing environments)
    OPENAI_API_KEY = None
    client = None


def prompt_response(client: Any, labels: List[str], quote: str, schema: dict) -> Any:
    """
    Send a text classification request to OpenAI with structured output.
    
    This function creates a prompt for classifying text into one of the provided
    labels and requests a JSON response that conforms to the given schema.
    
    Args:
        client: Initialized OpenAI client instance
        labels: List of allowed classification labels
        quote: Text to be classified
        schema: JSON schema dict defining the expected response structure
        
    Returns:
        OpenAI response object containing the classification result
        
    Note:
        Uses GPT-5 model and strict JSON schema validation to ensure
        consistent response format.
    """
    prompt = (
        "Classify the text into exactly one of the allowed labels. Return JSON only."
        f"Allowed labels: {labels}"
        "\n\nText for classification: " f'"{quote}"'
    )
    
    response = client.responses.create(
        model="gpt-5",
        input=[
            {"role": "user", "content": prompt}, 
            {"role": "system", "content": "You are a strict text classifier. Respond ONLY with JSON that matches the provided schema."}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "QuoteClassification",
                "schema": schema,
                "strict": True
            }
        },
    )

    return response


# content_text can be either a template str (with {q}) or a callable that takes q -> str
def parse_quotes(LabeledQuote, quotes, content_text: Union[str, Callable[[str], str]]):
    results: list[LabeledQuote] = []

    for q in quotes:
        # Build the content string for this quote
        if callable(content_text):
            content = content_text(q)              # e.g., lambda q: f"... {q}"
        else:
            content = content_text.format(q=q)     # e.g., ".... {q}"

        try:
            resp = client.responses.parse(         # assumes `client` and `config.model` are in scope
                model=config.model,
                input=[{"role": "user", "content": content}],
                text_format=LabeledQuote,
            )
            results.append(resp.output_parsed)
        except ValidationError as ve:
            print(f"[VALIDATION ERROR] {q[:60]}... -> {ve}")
        except Exception as e:
            print(f"[API ERROR] {q[:60]}... -> {e}")

        # TODO: update progress bar here

    return results