# LLM Tools

## Accessing the Task Builder
**Navigate**: LLM Tools > New Task (blank) or LLM Tools > Presets > *a starting point*

CodebookAI no longer ships six separate fixed tools. Instead there is one **Task Builder** window where you define exactly what you want the model to do, then run it either live or as a batch. The old Single-Label, Multi-Label, and Keyword Extraction tools are now **presets** -- one-click starting points that pre-fill the builder with an editable prompt and output shape, rather than separate menu items.

## What a Task is

A task has four parts, all editable in the builder:

- **Input** -- import one table (CSV/TSV/TXT/Excel). Every column becomes available as a `{placeholder}`.
- **Prompt** -- your own text. Anywhere you write `{column_name}`, that column's value is substituted per row; anywhere you write `{list_name}`, a constant value set is substituted (the same every row). An optional, hidden-by-default "system instructions" box is available for advanced use. Toggle **Preview** to see the exact rendered prompt for any row before you run anything.
- **Lists** -- named, reusable value sets (e.g. your labels), either typed directly (`positive, negative, neutral`) or imported from a file column. A list can be dropped into the prompt *and* bound to an output field at the same time, so the values shown to the model and the values it's constrained to are always identical -- edit the list once, both places update.
- **Output fields** -- the shape of the response, and the columns of your result CSV. Each field has a type:
  - **Choice** -- exactly one value from a List (this is what enforces "never a hallucinated label" -- a strict schema, not free text)
  - **Multi-choice** -- one or more values from a List
  - **Text list** -- free-form list of strings (e.g. extracted keywords)
  - **Free text** -- a single free-form string (e.g. a one-line justification)
  - **Number** / **Yes-No** -- numeric or boolean output

  You can define more than one output field per run -- e.g. a label *and* a free-text reason in the same request.
- **Carry to output** -- input columns that ride into the result CSV untouched, independent of whether they're used in the prompt. This is how an existing ID column follows your results back out even though it's never shown to the model.

## Live vs. Batch

Once a task is built, run it either way from the same window:

### Live
Requests are sent one at a time and you see results immediately. More expensive per request. Useful for small datasets, quick checks, and testing a task before committing to a full batch run.

### Batch
All requests are submitted together via OpenAI's Batch API and processed within 24 hours. Substantially cheaper for large datasets. Check progress in the Batches table on the main window; download results once the job is marked Done.

## Pricing
For pricing by model see OpenAI's [pricing page](https://platform.openai.com/docs/pricing).

---
