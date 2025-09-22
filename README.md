# CodebookAI

CodebookAI is a powerful text classification application that leverages OpenAI's advanced language models to automatically categorize text snippets into predefined labels. The application supports both batch processing for large datasets and real-time processing for immediate results.

## Features

### 🚀 Batch Processing
- **Efficient Large-Scale Processing**: Submit hundreds or thousands of text snippets for classification using OpenAI's batch API
- **Cost-Effective**: Batch processing offers significant cost savings compared to individual API calls
- **Background Processing**: Jobs run in the background with 24-hour completion windows
- **Status Monitoring**: Track ongoing and completed batch jobs with real-time status updates
- **Easy Result Export**: Download classification results as CSV files with confidence scores

### ⚡ Live Processing
- **Real-Time Classification**: Process text snippets immediately using OpenAI's API
- **Interactive Workflow**: Perfect for smaller datasets or when immediate results are needed
- **Progress Tracking**: Monitor processing status for each text snippet

### 🛠 User-Friendly Interface
- **Intuitive GUI**: Clean, modern interface built with tkinter
- **Tabbed Organization**: Separate views for ongoing and completed batch jobs
- **Context Menus**: Right-click actions for batch management (cancel, download, retry)
- **Tooltips**: Helpful hover text explains button functions
- **CSV Import**: Easy import of labels and text data from CSV files

### 🔐 Secure Configuration
- **Secure API Key Storage**: API keys stored safely in your system's keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Configurable Settings**: Customize AI model, batch limits, and timezone preferences
- **No Hardcoded Secrets**: Sensitive data never stored in configuration files

## Installation

### Prerequisites
- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### System Dependencies
CodebookAI requires tkinter for the graphical interface:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk
```

**CentOS/RHEL:**
```bash
sudo yum install tkinter
```

**macOS/Windows:**
tkinter is included with Python installations

### Python Dependencies
1. Clone or download this repository
2. Install required Python packages:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. First Launch
Run the application:
```bash
python ui/main_window.py
```

### 2. Configure API Key
1. Click the **Settings** button (⚙) in the top-right corner
2. Enter your OpenAI API key
3. Optionally adjust other settings (model, timezone, etc.)
4. Click **Save**

### 3. Prepare Your Data
Create two CSV files:
- **Labels CSV**: One column containing your classification categories
- **Quotes CSV**: One column containing text snippets to classify

Example labels.csv:
```csv
label
Positive
Negative
Neutral
```

Example quotes.csv:
```csv
text
"This product is amazing!"
"I hate this service"
"It's okay, nothing special"
```

### 4. Run Classification

#### For Batch Processing (Recommended for large datasets):
1. Click the **Add** button (＋) to create a new batch
2. Select your labels CSV file
3. Select your quotes CSV file
4. Monitor progress in the "Ongoing Batches" tab
5. Download results when complete

#### For Live Processing (Small datasets):
1. Click the **Tools** button (🛠)
2. Select "Live Process"
3. Select your labels and quotes CSV files
4. Wait for processing to complete
5. Save results when prompted

## Usage Guide

### Understanding the Interface

- **Tools Button (🛠)**: Access live processing and other utilities
- **Settings Button (⚙)**: Configure API key, model, and preferences  
- **Add Button (＋)**: Create new batch classification jobs
- **Refresh Button (↻)**: Update batch job status lists

### Batch Processing Workflow

1. **Create Batch**: Click Add (＋) and select your CSV files
2. **Monitor Progress**: Watch status in "Ongoing Batches" tab
3. **Check Completion**: Completed jobs move to "Done Batches" tab
4. **Download Results**: Right-click completed batches and select "Download"

### Managing Batch Jobs

- **Cancel**: Right-click ongoing batches to cancel if needed
- **Download**: Right-click completed batches to save results
- **Refresh**: Click refresh (↻) to update status information

### CSV Format Requirements

- **Headers**: First row can be headers (will be skipped automatically)
- **Single Column**: Only the first column is used for data
- **Text Format**: Ensure text is properly quoted if it contains commas
- **Encoding**: UTF-8 encoding recommended

## Configuration

### Settings Options

- **API Key**: Your OpenAI API key (stored securely)
- **Model**: AI model to use (default: o3)
- **Max Batches**: Number of recent batches to display (default: 4)
- **Timezone**: Timezone for displaying batch creation times

### Supported Models

CodebookAI works with OpenAI's latest models:
- **o3** (default): Most capable reasoning model
- **gpt-4o**: Fast and capable general model
- **gpt-4**: Highly capable general model

## Output Format

Classification results are saved as CSV files with these columns:
- **quote**: The original text that was classified
- **label**: The assigned classification label
- **confidence**: Confidence score (0.0 to 1.0)

Example output:
```csv
quote,label,confidence
"This product is amazing!",Positive,0.95
"I hate this service",Negative,0.92
"It's okay, nothing special",Neutral,0.87
```

## Troubleshooting

### Common Issues

**API Key Errors**:
- Verify your API key is correct and has sufficient credits
- Check that your key has access to the selected model

**CSV Import Problems**:
- Ensure CSV files are properly formatted
- Check file encoding (UTF-8 recommended)
- Verify files aren't corrupted or locked by other applications

**Batch Processing Delays**:
- Batch jobs can take up to 24 hours to complete
- Large batches take longer than small ones
- Check OpenAI's status page for service issues

**UI Freezing During Live Processing**:
- This is expected behavior - live processing blocks the UI
- Use batch processing for large datasets
- Consider breaking large datasets into smaller chunks

### Getting Help

If you encounter issues:
1. Check the application's error messages
2. Verify your CSV file format
3. Ensure your API key is valid and has credits
4. Check your internet connection

## Privacy & Security

- **API Keys**: Stored securely in your system's native keyring
- **Data**: Text data is sent to OpenAI for processing according to their privacy policy
- **Local Storage**: No sensitive data stored in application files
- **Network**: HTTPS connections used for all API communications

## Development

CodebookAI is built with:
- **Python 3.9+**: Core application
- **tkinter**: GUI framework  
- **OpenAI Python SDK**: API integration
- **pandas**: Data manipulation
- **keyring**: Secure credential storage

### Project Structure
```
CodebookAI/
├── ui/                     # User interface modules
│   ├── main_window.py     # Main application window
│   └── settings_window.py # Settings configuration dialog
├── batch_processing/       # Batch job management
│   └── batch_method.py    # OpenAI batch API integration
├── live_processing/        # Real-time processing
│   ├── live_method.py     # Live processing workflow
│   └── response_calls.py  # API response handling
├── file_handling/          # Data import/export
│   ├── csv_handling.py    # CSV file operations
│   └── json_handling.py   # JSON schema and batch files
├── settings/              # Configuration management
│   ├── config.py          # Non-sensitive settings
│   └── secrets_store.py   # Secure credential storage
└── requirements.txt       # Python dependencies
```

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with OpenAI's usage policies when using this application.

---

**Note**: This application requires an OpenAI API key and will incur costs based on your usage. Batch processing typically offers significant cost savings compared to individual API calls. Please monitor your usage and costs through the OpenAI dashboard.