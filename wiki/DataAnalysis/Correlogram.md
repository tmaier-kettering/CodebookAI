# Correlogram Tool

## Accessing Correlogram Tool
**Navigate**: Data Analysis > Correlogram

## Correlogram Purpose
This tool plots a correlation matrix. For qualitative data, it is used to visualize the agreement between two different categorizations of the same data with the same categories.
For example, for a new labeling schema, it may be critical to understand how well a particular OpenAI model agrees with human-generated labels. The correlogram can help visualize this agreement.

## Using the Correlogram Tool
**Create Dataset 1**: Choose the dataset file. You must select two columns:
- The TEXT column is the text column containing the items to be compared. The tool will compare this TEXT column to the TEXT column in Dataset 2. TEXT entries that appear in both datasets will be used to calculate agreement statistics.
- The LABEL column is the categorical column containing the labels assigned to each item.
- The Dataset Name is defaults to the file name (minus the file extension) but can be changed to any name you choose. It is used to create the output file name.

**Create Dataset 2**: Choose the second dataset file, following the same settings selection as Dataset 1.

## WARNINGS 
- The TEXT columns in both datasets must contain identical entries for the agreement statistics to be calculated. If there are no matching TEXT entries, the tool will return an error.
- The LABEL columns in both datasets must contain categorical data. If either LABEL column contains non-categorical data (e.g., continuous numerical data), the tool will return an error.
- If selecting both datasets from the same file, you must choose a different name for one of the two datasets or the tool will return an error.

---