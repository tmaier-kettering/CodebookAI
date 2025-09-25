# Data Analysis Tools

CodebookAI provides powerful built-in tools for analyzing your text classification results. These tools help you validate classifications, measure inter-rater reliability, and visualize relationships between labels and datasets.

## 🎯 Available Analysis Tools

### 1. Reliability Statistics
Calculate Cohen's Kappa and percentage agreement between two classifications to measure inter-rater reliability.

### 2. Correlogram Visualization
Generate interactive correlation matrices to visualize relationships between different labels and datasets.

Both tools use a convenient wizard interface that makes complex statistical analysis accessible to all users.

---

## 📊 Reliability Statistics

Reliability Statistics help you measure the consistency between two different classifications of the same text data. This is essential for validating AI classifications against human coding or comparing multiple human coders.

### 🎯 When to Use Reliability Statistics

#### Research Validation
- **AI vs Human**: Compare AI classifications with expert human coding
- **Inter-rater Reliability**: Measure agreement between multiple human coders  
- **Model Comparison**: Compare results from different AI models
- **Quality Assurance**: Validate classification consistency over time

#### Use Cases
- **Academic Research**: Ensure coding reliability meets publication standards
- **Content Analysis**: Validate sentiment analysis or thematic coding
- **Quality Control**: Monitor AI performance against gold standard
- **Training Validation**: Assess coder training effectiveness

### 📋 Step-by-Step Process

#### 1. Prepare Your Datasets

You need two datasets with the same text content but potentially different classifications:

**Dataset 1 Example** (AI Classifications):
```csv
text,ai_label
"Great product, highly recommend!",positive
"Terrible service experience",negative
"It's okay, nothing special",neutral
```

**Dataset 2 Example** (Human Classifications):
```csv
text,human_label
"Great product, highly recommend!",positive
"Terrible service experience",negative
"It's okay, nothing special",neutral
```

#### 2. Launch Reliability Analysis

1. **Navigate**: Data Analysis > Reliability Statistics
2. **Two-Dataset Wizard Opens**: Easy step-by-step interface

#### 3. Select First Dataset

1. **Choose File**: Browse to your first dataset (e.g., AI classifications)
2. **File Settings**:
   - Check "File has headers" if appropriate
   - Preview shows first 5 rows
3. **Column Selection**:
   - **TEXT Column**: Select column containing the text content
   - **LABEL Column**: Select column with classifications
4. **Dataset Name**: Give it a meaningful name (e.g., "AI_Classifications")

#### 4. Select Second Dataset

1. **Choose File**: Browse to your second dataset (e.g., human classifications)
2. **Repeat Column Selection**:
   - Select TEXT and LABEL columns
   - TEXT content must match between datasets
3. **Dataset Name**: Name the second dataset (e.g., "Human_Classifications")

#### 5. Automatic Analysis

CodebookAI automatically:
- **Matches Text**: Performs inner join on text content
- **Calculates Statistics**:
  - **Percentage Agreement**: Simple agreement rate
  - **Cohen's Kappa**: Agreement corrected for chance
- **Generates Report**: Comprehensive analysis with statistics

### 📈 Understanding Reliability Results

#### Statistics Explained

##### Percentage Agreement
- **Formula**: (Number of agreements / Total comparisons) × 100
- **Range**: 0% to 100%
- **Interpretation**: 
  - 90%+ = Excellent agreement
  - 80-89% = Good agreement
  - 70-79% = Moderate agreement
  - <70% = Poor agreement

##### Cohen's Kappa (κ)
- **Formula**: (Observed agreement - Expected agreement) / (1 - Expected agreement)
- **Range**: -1 to +1
- **Interpretation**:
  - κ > 0.81 = Almost perfect agreement
  - κ 0.61-0.80 = Substantial agreement
  - κ 0.41-0.60 = Moderate agreement
  - κ 0.21-0.40 = Fair agreement
  - κ 0.00-0.20 = Slight agreement
  - κ < 0.00 = Poor agreement (worse than chance)

#### Sample Results Output

**Statistics Summary**:
```
Dataset 1 Name: AI_Classifications
Dataset 2 Name: Human_Classifications
Number of Rows (after join on text): 150
Percent Agreement: 87.3%
Cohen's Kappa: 0.742
```

**Detailed Breakdown** (saved to Excel):
- **Sheet 1 - Statistics**: Summary metrics and metadata
- **Sheet 2 - Detailed Results**: Item-by-item comparison with agreement flags

### 🎨 Reliability Results Export

#### Excel Output Structure

##### Sheet 1: Statistics
| Metric | Value |
|--------|-------|
| Dataset 1 Name | AI_Classifications |
| Dataset 2 Name | Human_Classifications |
| Number of Rows | 150 |
| Percent Agreement | 87.3% |
| Cohen's Kappa | 0.742 |

##### Sheet 2: Detailed Results
| text | AI_Classifications | Human_Classifications | agreement |
|------|-------------------|----------------------|-----------|
| "Great product..." | positive | positive | True |
| "Terrible service..." | negative | negative | True |
| "It's okay..." | neutral | positive | False |

---

## 📈 Correlogram Visualization

Correlograms create visual correlation matrices showing relationships between labels across different datasets or within multi-label classifications.

### 🎯 When to Use Correlograms

#### Label Relationship Analysis
- **Multi-label Patterns**: See which labels commonly appear together
- **Dataset Comparison**: Compare label distributions between datasets
- **Bias Detection**: Identify unexpected label associations
- **Quality Assessment**: Spot problematic labeling patterns

#### Research Applications
- **Content Analysis**: Visualize thematic relationships in text data
- **Survey Analysis**: Show connections between response categories
- **Social Media**: Analyze hashtag and sentiment relationships
- **Document Classification**: Understand topic interconnections

### 📋 Correlogram Process

#### 1. Prepare Your Data

Correlograms work with datasets containing label classifications:

**Single Dataset Example**:
```csv
text,topic,sentiment,urgency
"Breaking: Stock prices rise",financial,positive,high
"Quarterly report released",financial,neutral,medium
"Customer complaints increase",service,negative,high
```

#### 2. Launch Correlogram Analysis

1. **Navigate**: Data Analysis > Correlogram
2. **Two-Dataset Wizard**: Same interface as reliability statistics

#### 3. Select Datasets

Similar to reliability analysis:
1. **First Dataset**: Choose your primary classification data
2. **Second Dataset**: Can be the same file or different classification
3. **Column Selection**: Select TEXT and LABEL columns for both

#### 4. Customize Visualization

Rich customization options:

##### Visual Options
- **Color Scheme**: Choose from 16+ color palettes
  - Sequential: Blues, Reds, Greens, Purples
  - Diverging: Coolwarm, Spectral
  - Perceptually Uniform: Viridis, Plasma, Inferno
- **Normalization**: 
  - Raw counts
  - Row-wise percentages
  - Column-wise percentages
- **Annotations**: Show correlation values on cells
- **Zero Diagonal**: Option to zero out diagonal values

##### Layout Options
- **Title**: Custom plot title
- **Size**: Automatic sizing based on data
- **Grid**: Show/hide grid lines
- **Labels**: Customize axis labels

#### 5. Interactive Display

The correlogram opens in a new window with:
- **Matplotlib Integration**: Full-featured plotting interface
- **Zoom and Pan**: Navigate large correlation matrices
- **Toolbar**: Save, zoom, configure subplot parameters
- **Persistent Window**: Stays open for analysis

### 🎨 Correlogram Interpretation

#### Visual Elements

##### Color Intensity
- **Darker Colors**: Stronger correlations/higher counts
- **Lighter Colors**: Weaker correlations/lower counts
- **Color Scale**: Legend shows value range

##### Matrix Structure
- **Rows**: First dataset labels
- **Columns**: Second dataset labels
- **Cells**: Correlation strength or count values
- **Diagonal**: Self-correlations (often strongest)

#### Analysis Patterns

##### Strong Positive Correlations
- **Dark cells**: Labels frequently appearing together
- **Diagonal dominance**: Expected self-correlation
- **Block patterns**: Related label clusters

##### Weak or No Correlations
- **Light cells**: Labels rarely co-occurring
- **Sparse patterns**: Independent label dimensions
- **Zero values**: Mutually exclusive categories

##### Unexpected Patterns
- **Off-diagonal strength**: Surprising label associations
- **Asymmetric patterns**: Directional relationships
- **Outlier cells**: Anomalous correlations worth investigating

### 🛠️ Advanced Correlogram Features

#### Customization Options

##### Color Palettes
- **Sequential**: Single-hue progression (Blues, Reds, etc.)
- **Diverging**: Two-hue scale for positive/negative values
- **Qualitative**: Distinct colors for categorical data
- **Perceptually Uniform**: Even visual intensity changes

##### Normalization Methods
- **None**: Raw count values
- **Row-wise**: Each row sums to 100%
- **Column-wise**: Each column sums to 100%
- **Total**: All values sum to 100%

##### Display Options
- **Annotations**: Numerical values overlaid on cells
- **Zero Diagonal**: Remove self-correlations for clarity
- **Grid Lines**: Visual separation between cells
- **Aspect Ratio**: Control plot dimensions

---

## 🔍 Practical Analysis Workflows

### Workflow 1: AI Validation

#### Objective
Validate AI classifications against human expert coding.

#### Steps
1. **Get Human Classifications**: Expert codes sample of data
2. **Run AI Classifications**: Process same data with CodebookAI
3. **Reliability Analysis**: Compare datasets
4. **Interpret Results**:
   - κ > 0.60: AI is ready for production
   - κ 0.40-0.60: Consider refining labels or training
   - κ < 0.40: Significant revision needed

### Workflow 2: Multi-rater Reliability

#### Objective
Measure consistency between multiple human coders.

#### Steps
1. **Multiple Coders**: 2+ people code same dataset
2. **Pairwise Comparison**: Run reliability for each pair
3. **Average Reliability**: Calculate mean κ across pairs
4. **Training Decision**: Retrain if average κ < 0.70

### Workflow 3: Label Relationship Discovery

#### Objective
Understand how different classification dimensions relate.

#### Steps
1. **Multi-dimensional Data**: Classifications on multiple attributes
2. **Correlogram Analysis**: Visualize label interactions
3. **Pattern Recognition**: Identify unexpected relationships
4. **Schema Refinement**: Adjust label definitions based on patterns

### Workflow 4: Temporal Analysis

#### Objective
Track classification consistency over time.

#### Steps
1. **Time-series Data**: Classifications from different time periods
2. **Period Comparison**: Compare early vs. late classifications
3. **Drift Detection**: Look for changes in reliability
4. **Model Monitoring**: Adjust if performance degrades

---

## 💡 Best Practices for Data Analysis

### Data Preparation

#### Text Matching
- **Exact Match**: Ensure identical text between datasets
- **Normalization**: Handle whitespace and encoding consistently
- **Duplicate Detection**: Remove or handle duplicate entries
- **Missing Data**: Plan for incomplete matches

#### Label Consistency
- **Standardization**: Use consistent label formats across datasets
- **Case Sensitivity**: Ensure consistent capitalization
- **Special Characters**: Handle punctuation and symbols uniformly
- **Label Mapping**: Document any label transformations

### Statistical Interpretation

#### Reliability Thresholds
- **Research Grade**: κ > 0.70 for publication-quality work
- **Production Systems**: κ > 0.60 for automated deployment
- **Exploratory Analysis**: κ > 0.40 for initial insights
- **Development Phase**: Any κ > 0.00 shows signal above noise

#### Sample Size Considerations
- **Minimum Size**: 50+ matched pairs for stable κ estimates
- **Recommended Size**: 100+ pairs for reliable statistics
- **Large Sample**: 500+ pairs for precise confidence intervals
- **Power Analysis**: Consider effect size and desired precision

### Visualization Guidelines

#### Correlogram Design
- **Color Choice**: Consider colorblind-friendly palettes
- **Scale Appropriateness**: Match normalization to research question
- **Annotation Density**: Show values only when space permits
- **Title and Labels**: Clear, descriptive text

#### Interpretation Cautions
- **Correlation vs. Causation**: Patterns suggest relationships, not causes
- **Sample Bias**: Consider representativeness of your data
- **Multiple Comparisons**: Many correlations increase false positive risk
- **Domain Knowledge**: Always interpret results in context

---

## 🛠️ Troubleshooting Analysis Tools

### Common Issues

#### "No Matching Text Found"
**Cause**: Text columns don't have exact matches between datasets
**Solutions**:
- Check text formatting (whitespace, encoding)
- Verify column selection
- Use text preprocessing to normalize formats

#### "Empty Results After Join"
**Cause**: No overlapping text content between datasets
**Solutions**:
- Verify datasets contain same source text
- Check for encoding issues
- Review column selection

#### "Correlogram Won't Display"
**Cause**: Graphics backend issues or data problems
**Solutions**:
- Restart CodebookAI
- Check data for non-numeric values
- Try different color scheme

### Performance Optimization

#### Large Datasets
- **Memory Usage**: Be cautious with datasets >10,000 rows
- **Processing Time**: Large correlograms may take several minutes
- **Display Limits**: Very large matrices may be hard to read

#### Visualization Performance
- **Color Complexity**: Simpler palettes render faster
- **Annotation Density**: Skip annotations for large matrices
- **Window Management**: Close unused correlogram windows

---

## 🔗 Integration with Other Tools

### From Classification to Analysis

#### Live Processing → Analysis
1. Complete live classification tasks
2. Save results as CSV
3. Use saved files as input for reliability/correlogram analysis

#### Batch Processing → Analysis
1. Retrieve completed batch results
2. Export to CSV format
3. Compare with other classifications or visualize patterns

### Export and Sharing

#### Excel Integration
- **Reliability Results**: Automatically saved as multi-sheet workbooks
- **Statistical Summaries**: Professional formatting for reports
- **Raw Data**: Detailed breakdowns for further analysis

#### External Analysis
- **CSV Export**: Standard format for R, Python, SPSS
- **Statistical Software**: Import reliability results for meta-analysis
- **Visualization**: Export correlogram images for presentations

---

## 📋 Data Analysis Checklist

### Pre-Analysis
- [ ] Datasets prepared with consistent text formatting
- [ ] Column structures verified and documented
- [ ] Sample size adequate for reliable statistics
- [ ] Research questions clearly defined

### During Analysis
- [ ] Column selections verified in preview
- [ ] Dataset names meaningful and documented
- [ ] Customization options chosen appropriately
- [ ] Results validated against expectations

### Post-Analysis
- [ ] Statistics interpreted in context
- [ ] Results documented with methodology
- [ ] Visualizations saved and annotated
- [ ] Follow-up analyses planned if needed

---

## 🎓 Next Steps

- **Need more classification data?** Try [Batch Processing](Batch-Processing.md) for large-scale analysis
- **Want to improve classifications?** Check [Best Practices](Best-Practices.md) for optimization tips
- **Looking for examples?** See [Sample Workflows](Sample-Workflows.md) for complete projects
- **Have questions?** Visit the [FAQ](FAQ.md) for common issues

---

*Ready to dive deeper into advanced features? Check out [Best Practices](Best-Practices.md) for expert tips on getting the most from CodebookAI!*