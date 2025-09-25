# Batch Processing Guide

Batch Processing in CodebookAI leverages OpenAI's Batch API to process large datasets cost-effectively. However, batches can take up to 24 hours to complete. For pricing see [OpenAI's pricing documentation](https://platform.openai.com/docs/pricing).

## 📋 When to Use Batch Processing

### Perfect For
- **Large Datasets**: 500+ text samples
- **Non-Urgent Projects**: Can wait up to 24 hours for results
- **Budget-Conscious Research**: Maximize your API budget

### Not Ideal For
- **Immediate Results**: When you need results right now
- **Interactive Testing**: Better to use [Live Processing](Live-Processing.md)
- **Iterative Development**: When refining labels frequently

## 🔄 Available Batch Processing Methods

### 1. Single Label Text Classification
Assign exactly one label from your predefined set to each text snippet.

### 2. Multi-Label Text Classification  
Assign multiple relevant labels to each text snippet.

### 3. Keyword Extraction
Identify the main keywords in a text snippet.

---

## 📦 Batch Processing Workflow

### Overview of the Process
1. **Prepare Data**: Format your labels and text files
2. **Create Batch**: Generate JSONL batch file and submit to OpenAI
3. **Monitor Status**: Track batch job progress (table must be manually refreshed)
4. **Retrieve Results**: Download and process completed results
5. **Analyze Data**: Use built-in tools for analysis

---
