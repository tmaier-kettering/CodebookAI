# Sampler Tool

## Accessing Sampler Tool
**Navigate**: Data Prep > Sample

## Sampler Purpose
The sample tool allows you to create a random smaller subset of your dataset for testing and experimentation.
This can be useful to randomly select a proportion of a dataset to manually label and compare to LLM results to check reliability.
Additionally, it can be used to create a smaller dataset to experiment with LLM tools before scaling up to the full dataset.

## Using the Sampler
1. **Select Dataset**: Choose the dataset you want to sample from (accepted file types: csv, tsv, Excel, and Parquet)
2. **Select the Sampling Method**: By rows will return the exact number of rows specified, while by percent will return the closest whole number of rows based on the proportion specified.
3. **Hit Ok**: You will be prompted to save the sampled dataset as a csv. The default name is the original dataset name appended with "_sample".

---