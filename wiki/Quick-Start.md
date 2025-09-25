# Quick Start Guide

Get up and running with CodebookAI in just a few minutes! This guide will walk you through your first text classification project using the included sample dataset.

## 🎯 What You'll Learn

By the end of this guide, you'll know how to:
- Set up your first classification project
- Import data into CodebookAI
- Run live text classification
- Review and export results
- Understand the different processing options

## 📚 Prerequisites

- CodebookAI is [installed](Installation-Guide.md) and running
- OpenAI API key is configured in settings
- You have a basic understanding of text classification concepts

## 🚀 Your First Project: Sentiment Analysis

Let's classify some business news text as positive, negative, or neutral using the included sample data.

### Step 1: Launch CodebookAI

1. **Start the application**
   - Run the executable, or 
   - Execute `python main.py` from the project directory

2. **Verify setup**
   - Check that the main window opens
   - Confirm your API key is configured (File > Settings)

### Step 2: Access Sample Data

CodebookAI includes sample datasets to help you get started:

**Sample Labels** (`sample_dataset/sample_labels.csv`):
```
positive
negative  
neutral
```

**Sample Text** (`sample_dataset/sample_text.csv`):
```
text,id,emotion
"For the last quarter of 2010, Componenta's net sales doubled...",1,positive
"According to the Finnish-Russian Chamber of Commerce...",2,neutral
"SSH COMMUNICATIONS SECURITY CORP... estimates its results to remain at loss...",3,negative
"Kone's net sales rose by some 14% year-on-year...",4,positive
```

### Step 3: Run Live Single-Label Classification

Let's classify the sample text in real-time:

1. **Open Live Processing**
   - Navigate to **LLM Tools > Live Methods > Single Label Classification**

2. **Select Labels Data**
   - Browse to `sample_dataset/sample_labels.csv`
   - Ensure "File has headers" is **unchecked** (labels are one per line)
   - Select the column containing your labels
   - Choose a nickname for this dataset (e.g., "Sentiment Labels")
   - Click "Import"

3. **Select Text Data**
   - Browse to `sample_dataset/sample_text.csv`
   - Ensure "File has headers" is **checked**
   - Preview shows your data with columns: text, id, emotion
   - Select **"text"** as your TEXT column
   - Select **"emotion"** as your LABEL column (for comparison)
   - Choose a nickname (e.g., "Business News")
   - Click "Import"

4. **Watch the Magic Happen!**
   - CodebookAI processes each text snippet
   - Progress bar shows real-time status
   - Each text gets classified as positive, negative, or neutral

5. **Review Results**
   - Processing completes automatically
   - You'll be prompted to save results as CSV
   - Choose a location (e.g., `my_first_results.csv`)

### Step 4: Examine Your Results

Open the saved CSV file. You'll see columns like:
- `id`: Original identifier
- `quote`: The text that was classified  
- `label`: AI-assigned label (positive/negative/neutral)

Compare the AI results with the original `emotion` column to see how accurate the classification was!

## 🔍 Understanding the Results

### What Just Happened?

1. **Data Import**: CodebookAI loaded your labels and text data
2. **API Calls**: Each text snippet was sent to OpenAI with instructions like:
   *"Classify this text as positive, negative, or neutral: [your text]"*
3. **Structured Output**: The AI response was validated against your label set
4. **Export**: Results were formatted and saved to CSV

### Key Concepts

- **Live Processing**: Immediate results, perfect for small datasets or testing
- **Structured Outputs**: AI responses are constrained to your exact label set
- **Progress Tracking**: Visual feedback for longer operations

## 🎛️ Try Different Approaches

### Multi-Label Classification

Now try classifying text with multiple labels simultaneously:

1. **Create Multi-Labels**: Make a file with labels like:
   ```
   urgent
   financial
   positive_news
   merger_acquisition
   quarterly_results
   ```

2. **Run Multi-Label**: Use **LLM Tools > Live Methods > Multi-Label Classification**
3. **Compare Results**: See how the same text can have multiple relevant labels

### Keyword Extraction

Extract key terms from your business news:

1. **Run Keyword Extraction**: Use **LLM Tools > Live Methods > Keyword Extraction**
2. **Select Text Only**: You only need the text data (no labels required)
3. **Review Keywords**: See what terms the AI identifies as most important

### Batch Processing (For Larger Datasets)

For cost efficiency with larger datasets:

1. **Create Batch**: Use **LLM Tools > Batch Methods > Single Label Classification**
2. **Submit Job**: Upload to OpenAI's batch processing service
3. **Cost Savings**: Up to 50% off standard API rates
4. **Retrieve Results**: Check back later for completed results

## 📊 Next: Try Data Analysis Tools

Once you have classification results from multiple sources or raters:

### Reliability Analysis

Compare two different classifications:

1. **Run Reliability**: **Data Analysis > Reliability Statistics**
2. **Select Datasets**: Choose two classification results
3. **Get Statistics**: Cohen's Kappa and percentage agreement
4. **Export Report**: Comprehensive statistical analysis

### Correlogram Visualization

Visualize label relationships:

1. **Run Correlogram**: **Data Analysis > Correlogram**
2. **Select Data**: Use your classification results  
3. **Customize Plot**: Choose colors, normalization, annotations
4. **Interactive Display**: Zoom, pan, and save the visualization

## 💡 Quick Tips for Success

### 🎯 Label Design
- **Be Specific**: "positive_financial_news" vs. "positive"
- **Avoid Overlap**: Ensure labels are mutually exclusive (for single-label)
- **Test Small**: Start with a few examples before processing thousands

### 💰 Cost Management
- **Use Live for Testing**: Perfect for trying different label sets
- **Use Batch for Production**: Significant savings on large datasets
- **Monitor Usage**: Check OpenAI dashboard regularly
- **Choose Model Wisely**: `gpt-4o-mini` for cost, `gpt-4o` for quality

### 📈 Quality Assurance
- **Sample Validation**: Always check a sample of results manually
- **Use Ground Truth**: Compare with known correct classifications
- **Iterate Labels**: Refine your label set based on results

## 🚧 Common Beginner Issues

### "No API Key" Error
- **Solution**: Go to File > Settings and enter your OpenAI API key
- **Check**: Verify key is valid on OpenAI platform

### "Import Failed" Error
- **Check Format**: Ensure CSV files are properly formatted
- **Check Headers**: Toggle "File has headers" setting appropriately
- **Check Encoding**: Save CSV files as UTF-8

### Poor Classification Results
- **Check Labels**: Ensure labels are clear and unambiguous
- **Try Different Model**: Switch from `gpt-4o-mini` to `gpt-4o`
- **Add Examples**: Consider few-shot prompting (advanced feature)

## 🎓 Next Steps

Congratulations! You've completed your first CodebookAI project. Here's what to explore next:

### Learn More Features
- **[Live Processing Guide](Live-Processing.md)**: Deep dive into real-time classification
- **[Batch Processing Guide](Batch-Processing.md)**: Cost-effective large-scale processing  
- **[Data Analysis Tools](Data-Analysis-Tools.md)**: Statistical analysis and visualization

### Real-World Applications
- **[Use Cases](Use-Cases.md)**: See how researchers use CodebookAI
- **[Sample Workflows](Sample-Workflows.md)**: Complete project examples
- **[Best Practices](Best-Practices.md)**: Tips from experienced users

### Advanced Topics
- **[Configuration Guide](Configuration.md)**: Customize settings and preferences
- **[API Reference](API-Reference.md)**: Technical details for power users

## 🆘 Need Help?

- **Check the [FAQ](FAQ.md)** for common questions
- **Review [Troubleshooting](Troubleshooting.md)** for technical issues
- **Visit [GitHub Issues](https://github.com/tmaier-kettering/CodebookAI/issues)** for community support

---

*Ready for more advanced features? Check out the [Live Processing Guide](Live-Processing.md) to unlock CodebookAI's full potential!*