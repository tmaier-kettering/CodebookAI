# Batch Processing Guide

Batch Processing in CodebookAI leverages OpenAI's Batch API to process large datasets cost-effectively. This method offers significant cost savings (up to 50% off standard rates) and is perfect for processing hundreds or thousands of text samples.

## 🎯 What is Batch Processing?

Batch Processing submits large jobs to OpenAI's batch processing system, which processes them asynchronously at reduced rates. This approach offers:

- **Cost Savings**: Up to 50% off standard API rates
- **Large Scale**: Handle thousands of text samples efficiently  
- **Asynchronous**: Submit jobs and retrieve results later
- **Resource Efficiency**: OpenAI optimizes processing during off-peak times

> 💰 **Cost Comparison**: Processing 1,000 text snippets with batch processing can cost ~$0.75 instead of ~$1.50 with live processing (using gpt-4o-mini).

## 📋 When to Use Batch Processing

### Perfect For
- **Large Datasets**: 500+ text samples
- **Non-Urgent Projects**: Can wait 2-24 hours for results
- **Budget-Conscious Research**: Maximize your API budget
- **Production Workflows**: Regular, scheduled processing

### Not Ideal For
- **Small Datasets**: < 100 samples (overhead not worth it)
- **Immediate Results**: When you need results right now
- **Interactive Testing**: Better to use [Live Processing](Live-Processing.md)
- **Iterative Development**: When refining labels frequently

## 🔄 Available Batch Processing Methods

### 1. Single Label Text Classification
Assign exactly one label from your predefined set to each text snippet.

### 2. Multi-Label Text Classification  
Assign multiple relevant labels to each text snippet.

Both methods use the same workflow but with different output structures.

---

## 📦 Batch Processing Workflow

### Overview of the Process
1. **Prepare Data**: Format your labels and text files
2. **Create Batch**: Generate JSONL batch file and submit to OpenAI
3. **Monitor Status**: Track batch job progress
4. **Retrieve Results**: Download and process completed results
5. **Analyze Data**: Use built-in tools for analysis

### Detailed Steps

#### Step 1: Data Preparation
Identical to Live Processing - prepare your labels and text files as described in the [Live Processing Guide](Live-Processing.md#data-preparation).

#### Step 2: Create and Submit Batch

1. **Navigate to Batch Processing**:
   - **Single Label**: LLM Tools > Batch Methods > Single Label Text Classification
   - **Multi-Label**: LLM Tools > Batch Methods > Multi-Label Text Classification

2. **Import Data**:
   - Select labels file (same process as live processing)
   - Select text data file
   - Choose appropriate columns and settings

3. **Batch Creation**:
   - CodebookAI generates a JSONL file with all requests
   - File is automatically uploaded to OpenAI
   - You receive a Batch Job ID for tracking

4. **Submission Confirmation**:
   - Job ID is displayed and saved
   - Estimated completion time provided
   - Job status shows as "validating" then "in_progress"

#### Step 3: Monitor Batch Status

CodebookAI provides several ways to check on your batch jobs:

1. **Main Interface**:
   - Recent batches shown in main window
   - Status updates: validating → in_progress → completed
   - Estimated and actual completion times

2. **Batch Management**:
   - View all submitted batches
   - Check detailed status information
   - Cancel jobs if needed (while in queue)

3. **Automatic Monitoring**:
   - CodebookAI checks status periodically
   - Notifications when jobs complete
   - Automatic result retrieval available

#### Step 4: Retrieve Results

When your batch job completes:

1. **Automatic Notification**:
   - CodebookAI detects completion
   - Results are automatically downloaded
   - Processing begins immediately

2. **Manual Retrieval**:
   - Click on completed batch in main interface
   - Select "Download Results"
   - Choose save location for processed data

3. **Data Processing**:
   - JSONL results converted to CSV format
   - Error handling for failed individual requests
   - Statistics summary provided

---

## 📊 Understanding Batch Results

### Result Structure

#### Single Label Results
```csv
id,quote,label,batch_id,request_id
1,"Great product, highly recommend!",positive,batch_123,req_001
2,"Terrible service, never again",negative,batch_123,req_002
3,"It's okay, nothing special",neutral,batch_123,req_003
```

#### Multi-Label Results
```csv
id,quote,label,batch_id,request_id
1,"Urgent financial report due","['urgent', 'financial', 'quarterly']",batch_456,req_001
2,"Positive customer feedback","['positive', 'customer_service']",batch_456,req_002
```

### Additional Metadata
- **batch_id**: Unique identifier for the batch job
- **request_id**: Individual request identifier within the batch
- **processing_time**: Timestamp information
- **error_info**: Details for any failed requests

### Success Rates
- **Typical Success Rate**: 95-99% of requests process successfully
- **Common Failures**: Malformed text, API errors, timeout issues
- **Error Handling**: Failed requests are logged separately
- **Retry Options**: Resubmit failed requests if needed

---

## 💰 Cost Analysis and Optimization

### Cost Breakdown

#### Batch vs Live Processing Costs (Example: 1,000 text snippets)

| Method | Model | Approximate Cost | Time | Best For |
|--------|-------|------------------|------|----------|
| Live | gpt-4o-mini | ~$1.50 | 10-30 mins | Testing, small datasets |
| Batch | gpt-4o-mini | ~$0.75 | 2-24 hours | Large datasets, non-urgent |
| Live | gpt-4o | ~$7.50 | 10-30 mins | High quality, immediate |
| Batch | gpt-4o | ~$3.75 | 2-24 hours | High quality, cost-conscious |

### Optimization Strategies

#### Choose the Right Model
- **gpt-4o-mini**: Best cost-effectiveness for most tasks
- **gpt-4o**: When you need higher accuracy or complex reasoning
- **Test First**: Use live processing to validate model choice

#### Efficient Data Preparation
- **Clean Text**: Remove unnecessary formatting and content
- **Optimal Length**: Aim for 50-200 tokens per text snippet
- **Clear Labels**: Reduce processing complexity with unambiguous labels

#### Batch Size Considerations
- **Minimum Viable**: 100+ items to justify batch processing
- **Sweet Spot**: 500-5,000 items for optimal cost/time balance
- **Large Scale**: 10,000+ items benefit most from batch pricing

---

## 🕐 Timing and Scheduling

### Processing Times

#### Typical Batch Processing Timeline
1. **Validation**: 1-10 minutes (checking format, quotas)
2. **Queue Time**: 5 minutes - 2 hours (depending on load)
3. **Processing**: 30 minutes - 12 hours (depending on size)
4. **Total Time**: Usually 2-24 hours from submission

#### Factors Affecting Speed
- **Batch Size**: Larger batches take proportionally longer
- **OpenAI Load**: Peak times may have longer queues
- **Model Choice**: Some models process faster than others
- **Request Complexity**: Simpler tasks complete faster

### Planning Your Batch Jobs

#### Best Practices for Timing
- **Submit Early**: Start jobs at beginning of day
- **Plan Buffer Time**: Allow extra time for unexpected delays
- **Weekend Processing**: Often faster processing on weekends
- **Monitor Holidays**: OpenAI processing may be slower

#### Managing Multiple Batches
- **Stagger Submissions**: Don't submit all jobs simultaneously
- **Priority Management**: Submit most important jobs first
- **Resource Planning**: Consider your API quota limits

---

## 🛠️ Advanced Batch Features

### Batch Management Interface

#### Job Tracking
- **Real-time Status**: Current status of all submitted batches
- **Progress Estimates**: Estimated completion times
- **History**: Complete record of all batch jobs
- **Filtering**: Sort by status, date, or dataset name

#### Error Management
- **Failed Request Analysis**: Detailed error reports
- **Partial Success**: Process successful items even if some fail
- **Resubmission**: Easy retry of failed requests
- **Error Patterns**: Identify common failure causes

### Advanced Configuration

#### Custom Batch Settings
- **Timeout Configuration**: Adjust request timeout limits
- **Retry Logic**: Configure automatic retry behavior
- **Notification Settings**: Email/desktop notifications for completion
- **Auto-Download**: Automatically retrieve completed results

#### Integration Features
- **Export Options**: Multiple format support (CSV, Excel, JSON)
- **Analysis Pipeline**: Automatic feeding to data analysis tools
- **Workflow Automation**: Chain batch jobs with analysis

---

## 🔍 Troubleshooting Batch Processing

### Common Issues

#### "Batch Validation Failed"
**Causes**:
- Malformed JSONL file
- Invalid characters in text
- Quota or billing issues

**Solutions**:
- Check text for special characters
- Verify OpenAI account billing status
- Review error logs for specific issues

#### "Job Stuck in Queue"
**Causes**:
- High OpenAI system load
- Large batch size
- API quota limits

**Solutions**:
- Wait longer (jobs can take 24+ hours)
- Check OpenAI status page
- Consider splitting into smaller batches

#### "Partial Results Only"
**Causes**:
- Some requests failed processing
- Text encoding issues
- API timeout on complex requests

**Solutions**:
- Review error report for failed requests
- Resubmit failed items
- Simplify problematic text samples

### Performance Optimization

#### Speed Up Processing
- **Smaller Batches**: Consider 500-1000 items per batch
- **Simple Text**: Remove complex formatting
- **Off-Peak Submission**: Submit during less busy periods

#### Improve Success Rates
- **Text Cleaning**: Remove unusual characters and formatting
- **Length Management**: Keep text under 2000 tokens
- **Encoding**: Ensure proper UTF-8 encoding

---

## 📈 Monitoring and Analytics

### Built-in Monitoring

#### Batch Dashboard
- **Active Jobs**: Current status of running batches
- **Completion Statistics**: Success rates and timing data
- **Cost Tracking**: Estimated and actual costs
- **Historical Data**: Trends and patterns over time

#### Success Metrics
- **Processing Rate**: Items per hour/day
- **Error Rate**: Percentage of failed requests
- **Cost Efficiency**: Cost per successfully processed item
- **Time Predictions**: Improving estimates based on history

### Integration with Analysis Tools

#### Automatic Analysis Pipeline
- **Results Processing**: Automatic conversion to analysis-ready formats
- **Quality Validation**: Built-in quality checks and statistics
- **Visualization**: Direct integration with correlogram and reliability tools
- **Export Options**: Seamless export to various formats

---

## 🔗 Integration Workflow

### From Development to Production

#### 1. Development Phase
- Use [Live Processing](Live-Processing.md) for initial testing
- Refine labels and validate approach
- Test with small samples (10-50 items)

#### 2. Validation Phase  
- Run small batch jobs (100-200 items)
- Compare results with ground truth
- Optimize labels and parameters

#### 3. Production Phase
- Submit large batch jobs (1000+ items)
- Monitor progress and results
- Use [Data Analysis Tools](Data-Analysis-Tools.md) for insights

### Post-Processing Options

#### Statistical Analysis
- **Reliability Statistics**: Compare with other coders
- **Correlogram Analysis**: Visualize label relationships
- **Export Reports**: Generate comprehensive summaries

#### Data Management
- **Result Storage**: Organize and archive results
- **Version Control**: Track different classification runs
- **Sharing**: Export results for external analysis

---

## 📋 Batch Processing Checklist

### Pre-Submission
- [ ] Data files prepared and validated
- [ ] Labels tested with live processing
- [ ] OpenAI account has sufficient credits
- [ ] Batch size is optimal (500+ items)
- [ ] Expected timeline communicated to stakeholders

### During Processing
- [ ] Monitor batch status regularly
- [ ] Check for error notifications
- [ ] Plan follow-up analysis steps
- [ ] Prepare for result processing

### Post-Processing
- [ ] Download and verify results
- [ ] Review error reports
- [ ] Conduct quality validation
- [ ] Archive raw results
- [ ] Proceed with statistical analysis

---

## 🎓 Next Steps

- **Need statistical analysis?** Check out [Data Analysis Tools](Data-Analysis-Tools.md)
- **Want to compare results?** Try [Reliability Statistics](Data-Analysis-Tools.md#reliability-statistics)
- **Looking for visualization?** See [Correlogram Analysis](Data-Analysis-Tools.md#correlograms)
- **Need best practices?** Read [Best Practices](Best-Practices.md)

---

*Ready to analyze your batch processing results? Learn about [Data Analysis Tools](Data-Analysis-Tools.md) for comprehensive statistical analysis and visualization!*