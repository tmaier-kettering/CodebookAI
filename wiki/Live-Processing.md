# Live Processing Guide

Live Processing in CodebookAI provides real-time text analysis with immediate results. This is perfect for smaller datasets, testing label sets, or when you need results right away.

## 🎯 What is Live Processing?

Live Processing sends each text snippet to OpenAI's API individually and returns results immediately. This approach offers:

- **Instant Results**: See classifications as they happen
- **Interactive Feedback**: Monitor progress in real-time
- **Quick Testing**: Perfect for validating label sets or approaches
- **Small Datasets**: Ideal for up to a few hundred text samples

> 💡 **When to Use Live vs. Batch**: Use Live for testing and small datasets (< 500 items). Use [Batch Processing](Batch-Processing.md) for larger datasets to save up to 50% on costs.

## 🔄 Available Live Processing Methods

### 1. Single Label Classification
Assign exactly one label from your predefined set to each text snippet.

### 2. Multi-Label Classification  
Assign multiple relevant labels to each text snippet.

### 3. Keyword Extraction
Extract meaningful keywords and phrases from text data.

---

## 🏷️ Single Label Classification

Perfect for categorization tasks where each text belongs to exactly one category.

### When to Use
- **Sentiment Analysis**: positive, negative, neutral
- **Topic Classification**: sports, politics, entertainment
- **Priority Levels**: high, medium, low
- **Document Types**: email, memo, report

### Step-by-Step Process

#### 1. Prepare Your Labels
Create a text file with one label per line (no headers):
```
positive
negative
neutral
```

Or use a CSV with labels in one column:
```
label
positive
negative
neutral
```

#### 2. Prepare Your Text Data
CSV format with headers:
```
text,id,other_data
"Great product, highly recommend!",1,review
"Terrible service, never again",2,review
"It's okay, nothing special",3,review
```

#### 3. Start Live Processing
1. **Navigate**: LLM Tools > Live Methods > Single Label Classification
2. **Select Labels**: 
   - Browse to your labels file
   - Check/uncheck "File has headers" as appropriate
   - Select the column with labels
   - Give the dataset a nickname
3. **Select Text**:
   - Browse to your text file
   - Ensure "File has headers" is checked
   - Select TEXT column (the text to classify)
   - Optionally select LABEL column (for comparison)
   - Give the dataset a nickname
4. **Process**: Click OK and watch the progress

#### 4. Review Results
Results include:
- `id`: Original row identifier
- `quote`: The text that was classified
- `label`: AI-assigned label (constrained to your label set)

### Pro Tips for Single Label
- **Clear Labels**: Use unambiguous, distinct labels
- **Balanced Examples**: Test with examples from each category
- **Validation**: Compare results with known correct labels

---

## 🏷️ Multi-Label Classification

Assign multiple relevant labels to each text snippet simultaneously.

### When to Use
- **News Categorization**: politics, economics, international, urgent
- **Product Features**: durable, affordable, user-friendly, innovative
- **Research Themes**: methodology, findings, limitations, implications
- **Email Tagging**: action-required, informational, urgent, project-alpha

### Key Differences from Single Label
- Each text can have 1 or more labels
- No mutual exclusivity requirement
- More comprehensive categorization

### Step-by-Step Process

#### 1. Prepare Multi-Labels
Create labels that can coexist:
```
urgent
financial
positive_sentiment
quarterly_results
merger_acquisition
regulatory_compliance
```

#### 2. Follow Single Label Process
The setup is identical to Single Label Classification:
1. Navigate to **LLM Tools > Live Methods > Multi-Label Classification**
2. Select labels and text data using the same wizard
3. Process and review results

#### 3. Understand Multi-Label Results
Results show arrays of labels:
```
id,quote,label
1,"Stock prices rose after merger announcement","['positive_sentiment', 'merger_acquisition', 'financial']"
2,"Urgent: Quarterly report due tomorrow","['urgent', 'quarterly_results', 'financial']"
```

### Best Practices for Multi-Label
- **Comprehensive Labels**: Cover all relevant aspects
- **Test Combinations**: Verify sensible label combinations
- **Review Patterns**: Look for unexpected label associations

---

## 🔑 Keyword Extraction

Extract meaningful keywords and phrases from text data using AI.

### When to Use
- **Content Analysis**: Identify key themes in documents
- **SEO Optimization**: Find important terms for web content
- **Research Coding**: Extract key concepts from interview transcripts
- **Document Summarization**: Identify main topics quickly

### Unique Features
- **No Labels Required**: Only needs text data
- **Flexible Output**: Extracts variable number of keywords
- **Context Aware**: Understands importance within context

### Step-by-Step Process

#### 1. Prepare Text Data
Only text data is required:
```
text,source,date
"The quarterly financial report shows significant growth...",annual_report,2024-01-15
"Customer feedback indicates satisfaction with new features...",survey,2024-01-20
```

#### 2. Start Keyword Extraction
1. **Navigate**: LLM Tools > Live Methods > Keyword Extraction
2. **Select Text**:
   - Browse to your text file
   - Select the TEXT column
   - Choose dataset nickname
   - No labels needed!
3. **Process**: Click OK and let AI extract keywords

#### 3. Review Extracted Keywords
Results include:
```
id,quote,keywords
1,"The quarterly financial report...","['quarterly', 'financial', 'growth', 'revenue', 'performance']"
2,"Customer feedback indicates...","['customer', 'satisfaction', 'features', 'feedback', 'improvement']"
```

### Advanced Keyword Extraction Tips
- **Long Texts**: Works better with substantial text content
- **Context Matters**: Keywords reflect the specific context
- **Variable Count**: Number of keywords adapts to content complexity

---

## 🎛️ Live Processing Interface

### Progress Tracking
- **Real-time Updates**: See each item as it processes
- **Progress Bar**: Visual indicator of completion
- **Item Counter**: "Processing item X of Y"
- **Error Handling**: Skip problematic items and continue

### Error Handling
Live Processing gracefully handles errors:
- **API Errors**: Temporary connectivity issues
- **Validation Errors**: When AI response doesn't match expected format
- **Rate Limits**: Automatic retry with backoff
- **Continuation**: Processing continues despite individual failures

### Stopping and Resuming
- **Cancel Anytime**: Stop processing if needed
- **Partial Results**: Save what's been processed so far
- **No Resume**: Live processing starts fresh each time

---

## 💰 Cost Considerations

### Live Processing Costs
- **Per-Request Pricing**: Each text item is a separate API call
- **No Batch Discount**: Standard OpenAI API rates apply
- **Model Choice Impact**: 
  - `gpt-4o-mini`: Most cost-effective
  - `gpt-4o`: Balanced cost/quality
  - `gpt-4-turbo`: Highest quality, highest cost

### Cost Optimization Tips
1. **Test with Mini**: Use `gpt-4o-mini` for initial testing
2. **Small Samples**: Test with 10-20 items before processing hundreds
3. **Efficient Labels**: Fewer, clearer labels = better results
4. **Batch for Scale**: Switch to batch processing for large datasets

### Cost Example
Processing 100 text snippets with `gpt-4o-mini`:
- Input tokens: ~50 tokens per text = 5,000 tokens
- Output tokens: ~10 tokens per response = 1,000 tokens  
- Approximate cost: $0.003 (varies with current pricing)

---

## 🛠️ Troubleshooting Live Processing

### Common Issues

#### "API Key Not Found"
- **Check Settings**: File > Settings > API Key
- **Verify Key**: Ensure key is valid on OpenAI platform
- **Restart App**: Sometimes required after key changes

#### "No Text Selected" Error
- **Check Column Selection**: Ensure TEXT column is selected
- **Verify Headers**: Toggle "File has headers" setting
- **Check File Format**: Ensure CSV is properly formatted

#### Classification Results Look Wrong
- **Check Labels**: Ensure labels are clear and distinct
- **Try Different Model**: Switch from mini to full model
- **Verify Text Quality**: Ensure text is readable and meaningful

#### Slow Processing
- **API Limits**: OpenAI may throttle requests
- **Network Issues**: Check internet connection
- **Model Busy**: Popular models may have slower response times

### Performance Tips

#### Optimize for Speed
- **Use `gpt-4o-mini`**: Faster and cheaper
- **Shorter Text**: Trim unnecessary content
- **Clear Labels**: Reduce AI confusion

#### Improve Accuracy
- **Use `gpt-4o`**: Better understanding of nuanced text
- **Better Labels**: More specific and unambiguous
- **Clean Text**: Remove formatting artifacts

---

## 🔗 Integration with Other Features

### Moving to Batch Processing
- **Export Label Set**: Save your tested labels
- **Scale Up**: Use same labels in batch processing for larger datasets
- **Cost Savings**: Significant reduction in per-item cost

### Using Results in Data Analysis
- **Reliability Analysis**: Compare live results with other classifications
- **Correlogram**: Visualize label relationships
- **Statistical Export**: Generate comprehensive reports

### Iterative Improvement
- **Test → Refine → Scale**: Perfect workflow
- **Live Testing**: Quick validation of label sets
- **Batch Production**: Large-scale processing

---

## 📋 Live Processing Checklist

### Before You Start
- [ ] OpenAI API key configured
- [ ] Labels file prepared (clear, distinct labels)
- [ ] Text data formatted properly (CSV with headers)
- [ ] Model selected based on cost/quality needs
- [ ] Small test sample ready

### During Processing
- [ ] Monitor progress for errors
- [ ] Check sample results for quality
- [ ] Note any patterns in misclassification
- [ ] Cancel if results look problematic

### After Processing  
- [ ] Review and validate results
- [ ] Save results to appropriate location
- [ ] Compare with any ground truth data
- [ ] Document lessons learned for next iteration

---

## 🎓 Next Steps

- **Ready for larger datasets?** Check out [Batch Processing](Batch-Processing.md)
- **Want to analyze results?** See [Data Analysis Tools](Data-Analysis-Tools.md)
- **Need to compare classifications?** Try [Reliability Statistics](Data-Analysis-Tools.md#reliability-statistics)
- **Looking for best practices?** Read [Best Practices](Best-Practices.md)

---

*Want to process larger datasets more cost-effectively? Learn about [Batch Processing](Batch-Processing.md) for significant cost savings!*