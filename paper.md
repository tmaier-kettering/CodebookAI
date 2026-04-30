---
title: "CodebookAI: LLM-powered deductive coding for qualitative research"
tags:
  - python
  - qualitative-research
  - text-classification
  - llm
  - openai
  - deductive-coding
authors:
  - name: "Torsten Maier"
    orcid: "YOUR-ORCID-HERE"
    affiliation: "Kettering University"
date: "2026-04-30"
---

## Summary {#summary}

CodebookAI is a desktop application that automates deductive coding, also known as text classification, for qualitative research workflows using OpenAI's API. Researchers upload text segments (such as interview excerpts or survey responses) along with a deductive codebook defining categories, and the tool classifies each segment by sending context-aware prompts to large language models and parsing the responses into structured output.

Unlike manual coding or rigid keyword-matching tools, CodebookAI leverages LLMs' understanding of context, nuance, and natural language to apply deductive codes consistently at scale. It supports researchers in social sciences, education, and health sciences who need to process large qualitative datasets efficiently. The tool handles tens of thousands of text segments via OpenAI's batch API, delivering results within 24 hours, and exports coded data as spreadsheets ready for analysis in tools like R or SPSS.

The application provides a simple GUI for codebook definition, text import, job submission, and result review, with robust error handling for API failures and malformed responses. CodebookAI lowers the barrier to LLM-assisted qualitative analysis while maintaining researcher control over codes and outputs.

## Statement of need {#statement-of-need}

Manual deductive coding remains labor-intensive for qualitative researchers, often requiring weeks to classify hundreds of text segments. Existing tools either rely on brittle keyword matching or require custom machine learning pipelines that demand data science expertise. Large language models offer a promising alternative through zero-shot classification, but researchers lack accessible, desktop-based interfaces that integrate codebook management, batch processing, and reliable output parsing.

CodebookAI fills this gap by providing a turnkey solution for LLM-powered deductive coding. It targets qualitative researchers who are domain experts but not programmers, enabling them to leverage OpenAI's models without writing prompts or API calls. The tool's batch support addresses scale limitations of interactive APIs, making it practical for real research projects with thousands of segments.

## Design choices {#design-choices}

CodebookAI is implemented in Python using [list GUI framework if applicable, e.g., Tkinter/PyQt/CustomTkinter] for the desktop interface and the OpenAI Python client for API interactions. The architecture separates concerns into three layers: a GUI layer for user input/output, a service layer for prompt construction and response parsing, and a thin API client that can be mocked for testing.

Key design decisions include:
- **Deterministic prompt templates** that incorporate the full codebook and segment context, minimizing LLM hallucination.
- **Structured response parsing** that validates and maps LLM outputs to codes, with fallbacks for ambiguous or malformed responses.
- **Batch API integration** for cost-effective, high-volume processing, with job tracking and retry logic.
- **Offline-first design** where possible, with API calls only for classification.

The application avoids external dependencies beyond OpenAI and standard Python libraries to ensure reproducibility across researcher environments.

## Functionality {#functionality}

Users define a codebook by specifying category names and descriptions, then import text segments from CSV or TXT files. CodebookAI constructs prompts combining the codebook, segment text, and instructions for single-label classification, submits via OpenAI's batch API, and retrieves results after processing (typically 24 hours).

Results are displayed in a spreadsheet-like view with original text, predicted code, confidence (if available), and LLM rationale. Users can review, edit, override predictions, and export to CSV for further analysis. Error logs and partial results ensure no data loss from API issues.

## AI usage disclosure {#ai-usage-disclosure}

GitHub Copilot was used extensively during software development, generating nearly all front-end code and portions of the back-end implementation. The core back-end classification logic and overall architecture were authored by the human developer. All Copilot-generated code was reviewed, validated, debugged, and integrated by the human author, who takes full responsibility for the software's correctness, licensing, and performance.

Perplexity AI (powered by Grok 4.1) was used to draft sections of this paper and assist with JOSS submission requirements. GitHub Copilot was also used to generate automated tests, CI workflows, and the `CONTRIBUTING.md` file. All AI-generated content was reviewed, substantially revised for accuracy, and validated by the author.

## Acknowledgments {#acknowledgments}
(optional — add if relevant)

## References {#references}
(optional — cite key dependencies or prior work)
