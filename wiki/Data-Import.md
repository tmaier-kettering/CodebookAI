# Data Import Guide

CodebookAI provides flexible data import capabilities that support multiple file formats and data structures. This guide covers everything you need to know about getting your data into CodebookAI efficiently.

## 📋 Supported File Formats

### Spreadsheet Formats
- **CSV** (`.csv`) - Comma-separated values
- **TSV** (`.tsv`) - Tab-separated values  
- **TXT** (`.txt`) - Text files with delimiters
- **Excel** (`.xlsx`, `.xls`, `.xlsm`) - Microsoft Excel workbooks

### Format-Specific Notes
- **CSV/TSV**: Automatic delimiter detection
- **TXT Files**: Intelligent delimiter sniffing (comma, tab, semicolon)
- **Excel**: Reads first worksheet by default
- **Encoding**: Automatic UTF-8 detection and conversion

## 🎯 Data Structure Requirements

### General Principles
- **Tabular Data**: All data should be in rows and columns
- **Text Column**: At least one column containing text to be analyzed
- **Label Column**: For classification tasks, a column with labels/categories
- **Headers**: Optional but recommended for clarity
- **Consistency**: Same structure across all files in a project

### Minimum Requirements

#### For Text Classification
- **Text Column**: The content to be classified
- **Optional ID Column**: Unique identifier for each row
- **Optional Label Column**: For comparison with AI results

#### For Label Sets
- **Single Column**: One label per row, or
- **Header Row**: Labels in first row of any column

---

## 📊 Import Process Overview

### Universal Import Wizard

CodebookAI uses a consistent import wizard across all features:

1. **File Selection**: Choose your data file
2. **Format Detection**: Automatic format and delimiter detection
3. **Header Configuration**: Specify if file has headers
4. **Preview**: See first 5 rows of your data
5. **Column Selection**: Choose relevant columns
6. **Nickname Assignment**: Name your dataset
7. **Import Confirmation**: Finalize the import

### Import Wizard Features

#### Intelligent Detection
- **File Type**: Automatic detection from extension
- **Delimiter**: Smart detection of CSV/TSV separators
- **Encoding**: Handles various text encodings
- **Headers**: Suggests header presence based on content

#### Data Preview
- **Live Preview**: Shows first 5 rows during import
- **Column Headers**: Displays detected or synthetic column names
- **Data Types**: Preview shows how data will be interpreted
- **Error Detection**: Highlights potential formatting issues

---

## 📁 Data Preparation Best Practices

### File Preparation

#### Text Data Files
```csv
text,id,category,date
"Customer service was excellent today",1,review,2024-01-15
"Product quality has declined recently",2,review,2024-01-16
"Shipping was faster than expected",3,review,2024-01-17
```

#### Label Files
**Option 1: Single Column (No Headers)**
```
positive
negative
neutral
```

**Option 2: With Headers**
```csv
label
positive
negative
neutral
```

#### Multi-Label Files
```csv
label
urgent
financial
positive_sentiment
quarterly_results
```

### Data Quality Guidelines

#### Text Content
- **Readable Text**: Ensure content is meaningful and complete
- **Consistent Encoding**: Use UTF-8 for special characters
- **Length Limits**: Keep individual texts under 2000 tokens (~1500 words)
- **Clean Formatting**: Remove excessive whitespace and formatting codes

#### Label Quality
- **Distinct Labels**: Each label should be clearly different from others
- **Consistent Naming**: Use consistent capitalization and spacing
- **No Duplicates**: Remove duplicate labels from label sets
- **Meaningful Names**: Use descriptive, unambiguous label names

#### Structural Integrity
- **Complete Rows**: Avoid missing data in key columns
- **Consistent Columns**: Same number of columns in all rows
- **Proper Escaping**: Quote text fields containing delimiters
- **No Mixed Data Types**: Keep columns consistently typed

---

## 🔧 Import Wizard Detailed Guide

### Step 1: File Selection

#### Choosing Files
1. **Browse Button**: Opens standard file dialog
2. **File Filters**: Shows only supported file types
3. **Multi-Select**: Not supported - choose one file at a time
4. **Path Display**: Shows selected file path

#### File Validation
- **Size Limits**: Files up to 100MB supported
- **Format Check**: Validates file extension
- **Access Check**: Ensures file is readable
- **Encoding Detection**: Handles various text encodings

### Step 2: Header Configuration

#### "File has headers" Toggle
- **Checked**: First row treated as column names
- **Unchecked**: Synthetic headers created (Col 1, Col 2, etc.)
- **Preview Updates**: Shows effect of toggle immediately
- **Smart Default**: System suggests appropriate setting

#### Impact on Column Names
**With Headers**:
```
text | id | category
"Sample text..." | 1 | positive
```

**Without Headers**:
```
Col 1 | Col 2 | Col 3
text | id | category
"Sample text..." | 1 | positive
```

### Step 3: Data Preview

#### Preview Features
- **First 5 Rows**: Shows data structure
- **Column Headers**: Displays detected names
- **Data Types**: Shows how data will be interpreted
- **Scrollable**: Navigate through columns if many exist

#### What to Check
- **Correct Delimiter**: Data properly separated into columns
- **Header Detection**: Column names make sense
- **Data Integrity**: Values appear in correct columns
- **Special Characters**: Text displays properly

### Step 4: Column Selection

#### For Classification Tasks

##### TEXT Column Selection
- **Radio Buttons**: Choose one column containing text to classify
- **Preview**: Shows sample content from selected column
- **Validation**: Ensures column contains readable text
- **Required**: Must select exactly one TEXT column

##### LABEL Column Selection
- **Optional**: For comparison with AI classifications
- **Radio Buttons**: Choose one column with existing labels
- **Validation**: Checks for consistent label format
- **Preview**: Shows sample labels from selected column

#### For Label Sets
- **Single Selection**: Choose column containing labels
- **Content Validation**: Ensures labels are text values
- **Duplicate Detection**: Warns about repeated labels
- **Empty Value Handling**: Filters out empty cells

### Step 5: Dataset Nickname

#### Nickname Options
1. **File Name**: Uses the filename without extension
2. **Column Header**: Uses selected column name (if headers exist)
3. **Custom**: Enter any descriptive name

#### Nickname Best Practices
- **Descriptive**: "Customer_Reviews" vs. "data"
- **Consistent**: Use naming convention across project
- **No Spaces**: Use underscores or camelCase
- **Version Info**: Include date or version if relevant

### Step 6: Import Confirmation

#### Final Review
- **File Path**: Confirms source file
- **Selected Columns**: Shows TEXT and LABEL selections
- **Dataset Name**: Displays chosen nickname
- **Row Count**: Shows number of rows to be imported

#### Import Process
- **Data Loading**: Reads entire file into memory
- **Validation**: Checks for data integrity
- **Processing**: Prepares data for analysis
- **Success Confirmation**: Reports successful import

---

## 🛠️ Troubleshooting Import Issues

### Common Import Problems

#### "File Cannot Be Read"
**Causes**:
- File is open in another application
- Insufficient permissions
- Corrupted file
- Unsupported encoding

**Solutions**:
- Close file in Excel/other applications
- Check file permissions
- Re-save file in supported format
- Convert to UTF-8 encoding

#### "No Columns Detected"
**Causes**:
- File is completely empty
- No delimiter detected
- Binary file incorrectly selected
- Encoding issues

**Solutions**:
- Verify file contains data
- Check delimiter characters
- Ensure file is text-based
- Try different encoding

#### "Import Failed" Error
**Causes**:
- Malformed CSV/Excel file
- Memory limitations with very large files
- Special characters causing parsing errors
- Mixed data types in columns

**Solutions**:
- Validate file structure
- Split large files into smaller chunks
- Clean special characters
- Ensure consistent column data types

#### "Preview Shows Garbled Text"
**Causes**:
- Encoding mismatch
- Binary data in text file
- Wrong delimiter detection
- File corruption

**Solutions**:
- Save file as UTF-8 CSV
- Check for binary content
- Manually specify delimiter if needed
- Re-create file from source

### Format-Specific Issues

#### CSV Files
- **Delimiter Confusion**: Comma vs. semicolon in different locales
- **Quote Escaping**: Text containing commas not properly quoted
- **Line Breaks**: Text containing newlines breaking row structure
- **BOM Issues**: Byte Order Mark causing column name problems

#### Excel Files
- **Multiple Worksheets**: Only first sheet is read
- **Merged Cells**: Can cause column misalignment
- **Formulas**: Only calculated values are imported, not formulas
- **Date Formatting**: May import as numbers instead of text

#### TSV Files
- **Tab Characters**: Actual tabs vs. multiple spaces
- **Mixed Delimiters**: Tabs and spaces used inconsistently
- **Special Characters**: Unicode characters in tab-delimited files
- **Trailing Tabs**: Empty columns at end of rows

---

## 📈 Advanced Import Techniques

### Large File Handling

#### Memory Management
- **File Size Limits**: ~100MB practical limit for most systems
- **Progressive Loading**: Large files loaded in chunks
- **Preview Limitations**: Only first 1000 rows analyzed for preview
- **Memory Optimization**: Efficient pandas processing

#### Strategies for Large Datasets
- **Split Files**: Divide into smaller, manageable chunks
- **Sample First**: Test import with subset before processing full file
- **Batch Processing**: Use batch methods for very large datasets
- **Clean Data**: Remove unnecessary columns and rows

### Data Transformation

#### Text Cleaning
CodebookAI automatically handles:
- **Whitespace**: Removes leading/trailing spaces
- **Encoding**: Converts to UTF-8
- **Line Breaks**: Preserves or normalizes as appropriate
- **Special Characters**: Handles Unicode correctly

#### Label Standardization
- **Case Normalization**: Option to standardize case
- **Duplicate Removal**: Automatic deduplication
- **Empty Value Filtering**: Removes blank labels
- **Validation**: Checks for valid label characters

### Multi-File Workflows

#### Consistent Structure
When importing multiple related files:
- **Same Column Names**: Use consistent headers across files
- **Same Data Types**: Maintain consistency in column content
- **Same Encoding**: Use UTF-8 throughout
- **Same Format**: Standardize on CSV or Excel

#### Project Organization
- **File Naming**: Use descriptive, consistent names
- **Version Control**: Include dates or versions in filenames  
- **Documentation**: Keep notes on data sources and transformations
- **Backup**: Maintain copies of original data files

---

## 💡 Data Import Best Practices

### Pre-Import Checklist

#### File Preparation
- [ ] Data is in supported format (CSV, TSV, TXT, Excel)
- [ ] Text encoding is UTF-8 or compatible
- [ ] File size is reasonable (<100MB)
- [ ] No binary or corrupted data

#### Data Structure
- [ ] Consistent column structure throughout file
- [ ] Text column contains meaningful content
- [ ] Label column has clear, distinct labels
- [ ] Headers are present and descriptive
- [ ] No completely empty rows

#### Quality Validation
- [ ] Text content is clean and readable
- [ ] Labels are consistent and unambiguous
- [ ] No missing data in critical columns
- [ ] Special characters display correctly

### Post-Import Validation

#### Immediate Checks
- [ ] Row count matches expectations
- [ ] Column selection appears correct
- [ ] Preview shows expected data
- [ ] No error messages during import

#### Quality Assessment
- [ ] Sample text content looks appropriate
- [ ] Labels are what you expected
- [ ] Dataset nickname is descriptive
- [ ] Ready to proceed with analysis

### Efficiency Tips

#### Streamlining Imports
- **Consistent Format**: Standardize all project files
- **Prepared Labels**: Create master label files for reuse
- **Template Files**: Use consistent structure across datasets
- **Batch Preparation**: Prepare multiple files before importing

#### Time-Saving Techniques
- **Default Settings**: Learn wizard defaults for faster navigation
- **File Organization**: Keep related files in same directory
- **Naming Convention**: Use systematic file naming
- **Documentation**: Record successful import settings

---

## 🔗 Integration with Analysis Features

### From Import to Analysis

#### Classification Workflow
1. **Import Labels**: Load your label definitions
2. **Import Text**: Load text data to classify
3. **Run Analysis**: Use Live or Batch Processing
4. **Export Results**: Save classifications for further analysis

#### Comparison Workflow
1. **Import Dataset 1**: Load first classification set
2. **Import Dataset 2**: Load second classification set  
3. **Run Reliability**: Compare agreement between datasets
4. **Generate Reports**: Export statistical analysis

#### Visualization Workflow
1. **Import Classifications**: Load labeled data
2. **Run Correlogram**: Visualize label relationships
3. **Customize Display**: Adjust colors and formatting
4. **Save Visualizations**: Export images for presentations

### Data Pipeline Integration

#### Preparation → Processing → Analysis
- **Consistent Structure**: Maintain compatibility throughout pipeline
- **Quality Control**: Validate at each step
- **Version Tracking**: Document transformations and analyses
- **Result Archival**: Save intermediate and final results

---

## 🆘 Getting Help with Import Issues

### Self-Help Resources
- **Preview Function**: Use preview to diagnose issues
- **Error Messages**: Read error details carefully
- **Format Examples**: Check sample data in this guide
- **File Validation**: Use external tools to validate CSV/Excel files

### External Tools for Data Preparation
- **Excel**: For data cleaning and formatting
- **Google Sheets**: For collaborative data preparation
- **Text Editors**: For CSV validation and encoding conversion
- **Online CSV Validators**: For format checking

### When to Seek Support
- Persistent import failures after following troubleshooting steps
- Unusual data formats not covered in documentation
- Performance issues with reasonably-sized files
- Encoding issues with non-English text

---

*Ready to start analyzing your imported data? Check out [Live Processing](Live-Processing.md) for immediate results or [Batch Processing](Batch-Processing.md) for cost-effective large-scale analysis!*