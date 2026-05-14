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
    orcid: "0000-0003-2538-4592"
    affiliation: 1
affiliations:
  - name: Kettering University, United States
    index: 1
date: 30 April 2026
bibliography: paper.bib
---

# Summary

CodebookAI is a desktop application for qualitative researchers that automates deductive coding—the systematic assignment of predefined category labels to text segments—using large language models (LLMs). Researchers in social sciences, education, health sciences, and related disciplines routinely analyze interview transcripts, open-ended survey responses, and similar text by applying codes from a structured codebook [@saldana2021]. This process is labor-intensive when datasets contain hundreds or thousands of segments.

CodebookAI provides a Tkinter-based graphical interface through which researchers upload a codebook (a flat list of category names) and text segments from CSV, TSV, Excel, or Parquet files. The application constructs structured prompts, enforces codebook fidelity through JSON-schema-constrained outputs validated by Pydantic, and returns coded results as spreadsheets ready for analysis in tools such as R, SPSS, or Excel.

The application supports two processing modes—**batch** and **live**—and four primary workflows: single-label classification, multi-label classification, keyword extraction, and inter-rater reliability analysis. A **correlogram** tool visualizes pairwise co-occurrence between two sets of codes as a heatmap, and a **data preparation** module enables stratified random sampling to create representative coding subsets for pilot studies.

# Statement of need

Deductive qualitative coding is a methodological cornerstone of qualitative content analysis [@mayring2022] and systematic qualitative inquiry more broadly. The process requires trained coders to evaluate each text segment against a codebook, and often involves two or more coders to establish inter-rater reliability. For datasets of several hundred to several thousand items, this represents a substantial investment of researcher time.

CodebookAI addresses this problem by giving researchers a graphical tool that applies LLM-based classification to user-defined codebooks without requiring programming knowledge. It is intended for researchers who need structured, reproducible assistance with coding large collections of text segments while preserving a codebook-driven workflow. The software supports both exploratory pilot work on small samples and large-scale studies involving tens of thousands of segments processed through batch inference.

# State of the field

Researchers currently have several imperfect options for deductive coding assistance. Manual coding in qualitative data analysis platforms such as NVivo, ATLAS.ti, and MAXQDA supports established research workflows, but these tools are centered on human coding rather than LLM-based automated classification. General-purpose LLM interfaces such as ChatGPT can classify text, but they do not provide integrated codebook management, structured export, batch submission workflows, or built-in reliability analysis suitable for systematic research projects.

Other computational alternatives also have important limitations. Keyword-based approaches are brittle for semantically complex text, especially when categories depend on context rather than explicit vocabulary. Supervised machine-learning approaches can be effective, but they require labeled training data, model development expertise, and a different workflow from the zero-shot or instruction-based classification that LLMs make possible. CodebookAI’s contribution is to bridge this gap by combining a researcher-facing desktop interface with structured-output constraints, batch and live processing, spreadsheet-oriented import/export, and post-classification reliability tools in a single application.

# Software design

CodebookAI is implemented as a Tkinter-based desktop application designed for researchers who may not have programming experience but still need transparent and repeatable coding workflows. A central design choice is the separation between the user interface, the prompt-and-schema generation logic, and the API interaction layer. This structure supports both interactive use and testability while allowing the software to expose a simple GUI.

A second major design choice is the use of runtime-generated structured outputs. Rather than allowing the model to return arbitrary free text, CodebookAI builds a Pydantic model from the user-supplied codebook, derives a JSON schema from that model, and uses the schema to constrain outputs from the API [@openai2024]. This design reduces invalid labels and keeps the model aligned with the researcher’s predefined category set.

The software also supports both **live** and **batch** execution modes because these modes serve different research needs. Live mode is useful for smaller jobs and iterative exploration, while batch mode is better suited for large studies where lower cost and higher throughput are more important than immediate responses. Additional modules for inter-rater reliability, correlograms, and random sampling were included so that the application supports more of the end-to-end research workflow rather than limiting itself to a single classification step.

## Functionality

Users launch CodebookAI without installing dependencies beyond the single-file Windows executable, or alternatively from source in a standard Python environment. After entering an OpenAI API key in **File → Settings**, the workflow proceeds through data import, codebook selection, model execution, and export of results.

For classification, a file import wizard accepts CSV, TSV, Excel, and Parquet files. The user selects the column containing text segments and imports a codebook as a flat list of labels. CodebookAI builds a Pydantic model at runtime that treats the label list as a strict enumeration, derives a JSON schema from it, and passes the schema to the API as a structured-output constraint. In batch mode, requests are bundled into a JSONL file and submitted through OpenAI’s Batch API; in live mode, segments are classified sequentially with progress reporting. Results are exported as CSV.

The same general workflow supports **multi-label classification** and **keyword extraction**, while the **inter-rater reliability** module compares two coded datasets and computes matched rows, percent agreement, and Cohen’s kappa [@cohen1960], exporting results to Excel. The **correlogram** tool visualizes cross-dataset code relationships as a heatmap, and the **data preparation** module supports random sampling to create pilot subsets before running full-scale coding jobs.

# Research impact statement

CodebookAI has already been used to support published research. In particular, the software was used in the study *Examining the Reliability of ChatGPT: A Quantitative Comparison of Human and LLM Emotion Classification*, published through the American Society for Engineering Education (ASEE) proceedings, which investigated the reliability of large language models in an emotion-classification task [@asee2025]. This provides direct evidence that the software has moved beyond a prototype and has already supported an actual research workflow and scholarly output.

The software is designed to be useful in additional research settings where investigators need to classify large collections of open-ended text with a predefined codebook and then evaluate agreement or downstream patterns. Its support for spreadsheet-based inputs and outputs, structured classification constraints, and integrated reliability analysis lowers the practical barrier for researchers who want to incorporate LLM-assisted coding into empirical studies without building custom software pipelines.

# AI usage disclosure

GitHub Copilot was used extensively during software development, generating the majority of front-end code and portions of the back-end implementation. The core classification logic, structured-output schema generation, and overall architecture were authored by the human developer. All Copilot-generated code was reviewed, validated, debugged, and integrated by the human author, who takes full responsibility for the software's correctness, licensing, and performance.

GitHub Copilot was also used to generate automated tests, CI workflows, and the `CONTRIBUTING.md` file. All AI-generated content was reviewed and substantially revised for accuracy by the author.

# Acknowledgments

The author thanks the students and research collaborators at Kettering University whose qualitative research needs motivated the development of this tool.

# References
