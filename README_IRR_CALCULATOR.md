# Inter-Rater Reliability Calculator

## Overview

The Inter-Rater Reliability Calculator is a comprehensive GUI tool for calculating agreement between two raters/annotators. It provides a 4-page wizard interface that guides users through selecting data files, configuring options, and calculating reliability metrics.

## Features

### 🧙‍♂️ 4-Page Wizard Interface
- **Page 1**: Dataset 1 - Text Column Selection
- **Page 2**: Dataset 1 - Labels Column Selection  
- **Page 3**: Dataset 2 - Text Column Selection
- **Page 4**: Dataset 2 - Labels Column Selection

### 📁 File Format Support
- CSV files (`.csv`)
- Excel files (`.xlsx`, `.xls`)
- TSV files (`.tsv`)
- Text files (`.txt`)
- Automatic delimiter detection for text files

### 📊 Data Preview & Selection
- Interactive file browser
- Scrollable data preview (first 5 rows)
- Header checkbox with dynamic preview updates
- Horizontal scrollable radio buttons for column selection
- Real-time column header display

### ✅ Data Validation
- Ensures matching lengths between text and label datasets
- Validates shared text entries between datasets
- Prevents progression with invalid data

### 📈 Reliability Calculations
- **Percent Agreement**: Simple percentage of matching labels
- **Cohen's Kappa**: Robust inter-rater reliability metric accounting for chance agreement
- Manual implementation (no external ML library dependencies)

### 💾 Export Functionality
- Save final dataset as CSV or Excel
- Dataset includes: text, label1, label2, agreement columns
- File dialog with format selection

### 🎯 Integration
- Seamlessly integrated into CodebookAI Tools menu
- Follows application UI patterns and styling
- Consistent with existing import dialogs

## Usage

### From CodebookAI Main Application
1. Launch CodebookAI (`python main.py`)
2. Click the Tools button (🛠) in the top-left
3. Select "Calculate Interrater Reliability"

### Standalone Usage
```python
import interrater_reliability
interrater_reliability.calculate_interrater_reliability()
```

## Workflow

### Step 1: Dataset 1 Text Selection
- Select file containing text data for the first rater
- Choose whether file has headers
- Preview data in scrollable table
- Select the text column using radio buttons

### Step 2: Dataset 1 Labels Selection
- Select file containing label data for the first rater
- Must have same number of rows as text data
- Select the labels column

### Step 3: Dataset 2 Text Selection
- Select file containing text data for the second rater
- Select the text column (should contain overlapping text)

### Step 4: Dataset 2 Labels Selection
- Select file containing label data for the second rater
- Must have same number of rows as Dataset 2 text
- Select the labels column

### Step 5: Results & Export
- View calculated metrics in popup dialog
- Option to save merged dataset with agreement analysis

## Calculations

### Percent Agreement
```
Percent Agreement = (Number of Agreements / Total Cases) × 100
```

### Cohen's Kappa
Cohen's Kappa accounts for chance agreement:
```
κ = (Po - Pe) / (1 - Pe)
```
Where:
- `Po` = Observed agreement
- `Pe` = Expected agreement by chance

### Interpretation Scale
- **< 0.20**: Poor agreement
- **0.21-0.40**: Fair agreement
- **0.41-0.60**: Moderate agreement
- **0.61-0.80**: Good agreement
- **0.81-1.00**: Very good agreement

## Technical Implementation

### Core Components
- `IRRWizard`: Main wizard class managing the multi-page interface
- `_calculate_cohens_kappa()`: Manual implementation of Cohen's kappa
- File loading with pandas for robust format support
- Tkinter GUI with ttk styling

### Data Processing
1. Load and preview data files
2. Extract selected columns from each dataset
3. Merge datasets on shared text entries (inner join)
4. Calculate agreement boolean column
5. Compute reliability metrics
6. Export final dataset

### Error Handling
- File loading errors with user-friendly messages
- Data validation with clear error descriptions
- Graceful handling of edge cases (empty datasets, single categories)

## Testing

The implementation includes comprehensive tests covering:

✅ **Data Loading**: CSV, TSV, Excel file support  
✅ **Processing Logic**: Data merging and agreement calculation  
✅ **Cohen's Kappa**: Edge cases (perfect, no agreement, single category)  
✅ **File Formats**: Multiple delimiter detection  
✅ **Integration**: Main application menu integration  

### Test Results
```
🧪 Running IRR Calculator Comprehensive Tests

Testing data loading...
✓ CSV loading works
✓ Data loading test passed

Testing processing logic...
Dataset 1: 5 text, 5 labels
Dataset 2: 5 text, 5 labels
Shared text entries: 4
Shared data:
  'The cat sat on the mat': positive vs negative
  'Hello world': neutral vs positive
  'Python is great': positive vs positive
  'Machine learning rocks': positive vs positive

Results:
Total cases: 4
Agreements: 2
Percent agreement: 50.00%
Cohen's kappa: -0.1429

✓ Processing logic test passed
✓ Cohen's kappa edge cases passed
✓ File format support test passed

🎉 All tests passed! The IRR Calculator is working correctly.
```

## Sample Data Format

### Dataset 1 Text (dataset1_text.csv)
```csv
text_column,other_column
"The cat sat on the mat","data1"
"Hello world","data2"
"Python is great","data3"
"Machine learning rocks","data4"
"The weather is nice","data5"
```

### Dataset 1 Labels (dataset1_labels.csv)
```csv
label_column,extra_column
"positive","info1"
"neutral","info2"
"positive","info3"
"positive","info4"
"neutral","info5"
```

### Final Output Dataset
```csv
text,label1,label2,agreement
"The cat sat on the mat","positive","positive",True
"Hello world","neutral","neutral",True
"Python is great","positive","positive",True
"Machine learning rocks","positive","positive",True
```

## Dependencies

- `tkinter` (Python standard library)
- `pandas` (for robust file loading)
- `pathlib` (Python standard library)
- `csv` (Python standard library)

No external machine learning libraries required - Cohen's kappa is implemented manually.

## Authors

Generated for CodebookAI as a comprehensive inter-rater reliability analysis tool.