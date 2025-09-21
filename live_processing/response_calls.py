
def prompt_response(client, labels, quote, schema):
    prompt = (
            "Classify the text into exactly one of the allowed labels. Return JSON only."
            f"Allowed labels: {labels}"
            "\n\nText for classification: " f'"{quote}"'
    )
    response = client.responses.create(
        model="gpt-5",
        input=[{"role": "user", "content": prompt}, {"role": "system", "content": "You are a strict text classifier. Respond ONLY with JSON that matches the provided schema."}],
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

