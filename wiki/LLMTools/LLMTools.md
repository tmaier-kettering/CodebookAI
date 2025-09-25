# LLM Tools

## Tools

- [Live Methods](./LiveMethods/LiveMethods.md) - Real-time API calls for quick responses.
- [Batch Methods](./BatchMethods/BatchMethods.md) - Cost-effective processing for large datasets.

## Overview

When working with OpenAI's API there are two primary modes of operation: live and batch. Each mode has its own advantages and disadvantages, and the choice between them depends on the specific use case and requirements.

## Live Mode
In live mode, requests are sent to the API in real-time, and responses are received quickly. However, it is more expensive than batch mode.
Useful for:
- Small datasets
- Quick responses
- Testing and experimentation before batching

## Batch Mode
In batch mode, requests are grouped together and sent to the API in a single call. This is more cost-effective for large datasets but takes up to 24 hours to process.
Useful for:
- Large datasets
- Cost efficiency
- Non-urgent processing

## Pricing
For pricing by model see OpenAI's [pricing page](https://platform.openai.com/docs/pricing).

---