# CodebookAI

CodebookAI is a powerful text classification application that leverages OpenAI's language models to perform a variety of tasks - primarily to automatically categorize text snippets into predefined labels. The application supports both batch processing for large datasets and real-time processing for immediate results.

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

## Configuration

### Settings Options

- **API Key**: Your OpenAI API key (stored securely)
- **Model**: AI model to use (default: o3)
- **Max Batches**: Number of recent batches to display (default: 4)
- **Timezone**: Timezone for displaying batch creation times

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with OpenAI's usage policies when using this application.

---

**Note**: This application requires an OpenAI API key and will incur costs based on your usage. Batch processing typically offers significant cost savings compared to individual API calls. Please monitor your usage and costs through the OpenAI dashboard.
