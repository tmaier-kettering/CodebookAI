---
title: "CodebookAI: LLM-powered deductive coding for qualitative research"
tags:
  - python
  - qualitative-research
  - text-classification
  - large-language-models
  - openai
  - deductive-coding
  - inter-rater-reliability
authors:
  - name: "Torsten Maier"
    orcid: "0000-0000-0000-0000"
    affiliation: 1
affiliations:
  - name: Kettering University, United States
    index: 1
date: 30 April 2026
bibliography: paper.bib
---

## Summary

CodebookAI is a desktop application for qualitative researchers that automates deductive coding—the systematic assignment of predefined category labels to text segments—using large language models (LLMs). Researchers in social sciences, education, health sciences, and related disciplines routinely analyze interview transcripts, open-ended survey responses, and similar text by applying codes from a structured codebook [@saldana2021]. This process is labor-intensive when datasets contain hundreds or thousands of segments.

CodebookAI provides a Tkinter-based graphical interface through which researchers upload a codebook (a flat list of category names) and text segments from CSV, TSV, Excel, or Parquet files. The application constructs structured prompts, enforces codebook-fidelity through JSON-schema-constrained outputs validated by Pydantic, and returns coded results as spreadsheets ready for analysis in tools such as R, SPSS, or Excel.

The application supports two processing modes—**batch** and **live**—and four primary workflows:

1. **Single-label classification**: assign exactly one codebook category to each text segment.
2. **Multi-label classification**: assign one or more categories to each segment.
3. **Keyword extraction**: extract free-form keyword lists from text without a predefined codebook.
4. **Inter-rater reliability analysis**: compute percent agreement and Cohen's kappa [@cohen1960] between two independently coded datasets, with export to Excel.

A **correlogram** tool visualizes pairwise co-occurrence between two sets of codes as a heatmap, and a **data preparation** module enables stratified random sampling to create representative coding subsets for pilot studies.

## Statement of Need

Deductive qualitative coding is a methodological cornerstone of qualitative content analysis [@mayring2000] and systematic qualitative inquiry more broadly. The process requires trained coders to evaluate each text segment against a codebook, and typically involves two or more coders to establish inter-rater reliability. For datasets of several hundred to several thousand items, this represents a significant investment of researcher time—often weeks per study.

Existing computational tools address this challenge inadequately. Keyword-matching approaches fail on semantically complex text. Supervised machine-learning pipelines require labeled training data, data-science expertise, and large datasets before they achieve acceptable accuracy. Commercial qualitative data analysis software (e.g., NVivo, ATLAS.ti, MAXQDA) supports manual coding workflows but does not integrate LLM-based classification. General-purpose LLM chat interfaces such as ChatGPT do not provide the structured outputs, batch processing, or codebook integration that systematic research requires.

LLMs demonstrate strong zero-shot text classification capabilities—assigning labels to previously unseen text without task-specific training [@brown2020]. CodebookAI operationalizes this capability in a researcher-facing tool that requires no programming knowledge. It enforces codebook fidelity through a JSON schema derived at runtime from the user-defined codebook, so the model is structurally prevented from producing labels outside the allowed set [@openai2024]. The **batch processing** mode (via OpenAI's Batch API) reduces costs by up to 50% compared to synchronous calls and scales to tens of thousands of segments per job with results typically available within 24 hours. The integrated reliability module closes the qualitative workflow loop by enabling immediate quantitative comparison of LLM-generated codes with human-generated codes.

## Functionality

Users launch CodebookAI without installing dependencies beyond the single-file Windows executable (or a standard `pip install` for source users). After entering an OpenAI API key in **File → Settings**, the workflow proceeds as follows:

**Classification (batch or live).** A file import wizard accepts CSV, TSV, Excel, and Parquet files. The user selects the column containing text segments; a second import selects the column containing codebook labels. CodebookAI builds a Pydantic model at runtime that treats the label list as a strict enumeration, derives a JSON schema from it, and passes the schema to the OpenAI API as a structured-output constraint. In batch mode, all requests are bundled into a single JSONL file and submitted to OpenAI's Batch API; the main window displays job status and allows one-click result retrieval. In live mode, segments are classified sequentially with a progress bar. Results are exported as CSV.

**Multi-label classification** follows the same workflow but uses an array-typed JSON schema, requiring at least one label per segment.

**Keyword extraction** submits each text segment with a prompt requesting a list of key terms, returning results in the same batch or live modes.

**Reliability analysis.** The inter-rater reliability module accepts two coded datasets and joins them on a shared text column. It computes the number of matched rows, percent agreement, and Cohen's kappa over the union of label sets, then exports a two-sheet Excel workbook with summary statistics and per-row agreement flags.

**Correlogram.** Given two coded datasets, this tool computes a cross-tabulation matrix between the label columns and renders it as a customizable heatmap (with options for row, column, or global normalization, colormap selection, and cell annotation).

**Data preparation.** A random sampler draws a user-specified number of rows from any imported dataset, enabling researchers to create pilot subsets before committing to full-dataset API costs.

## AI Usage Disclosure

GitHub Copilot was used extensively during software development, generating the majority of front-end code and portions of the back-end implementation. The core classification logic, structured-output schema generation, and overall architecture were authored by the human developer. All Copilot-generated code was reviewed, validated, debugged, and integrated by the human author, who takes full responsibility for the software's correctness, licensing, and performance. GitHub Copilot was also used to generate automated tests, CI workflows, and the `CONTRIBUTING.md` file. All AI-generated content was reviewed and substantially revised for accuracy by the author.

## Acknowledgments

The author thanks the students and research collaborators at Kettering University whose qualitative research needs motivated the development of this tool.

## References
