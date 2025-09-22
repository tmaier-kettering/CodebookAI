
"""
OpenAI API response handling for live text classification.

This module provides functions for making structured API calls to OpenAI's
text classification endpoints with JSON schema validation.
"""

from typing import Any, List


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
