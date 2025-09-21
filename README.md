# Codebook - Professional Text Classification Tool

A professional, enterprise-grade text classification application built with Python and OpenAI's API. This tool provides both live and batch processing capabilities with comprehensive error handling, logging, and user-friendly interfaces.

## 🚀 Features

### Core Capabilities
- **Live Classification**: Immediate processing with real-time results
- **Batch Processing**: Cost-effective bulk processing (50% savings)
- **Multi-format Support**: CSV input/output with flexible column handling
- **GUI Integration**: User-friendly file selection dialogs
- **Progress Tracking**: Real-time progress updates for long operations

### Professional Standards
- **Robust Error Handling**: Comprehensive exception hierarchy with clear error messages
- **Secure Configuration**: Environment-based configuration with validation
- **Comprehensive Logging**: Structured logging for debugging and monitoring
- **Type Safety**: Full type hints throughout the codebase
- **Data Validation**: Input validation and sanitization at all levels
- **Resource Management**: Proper cleanup and resource handling

### Enterprise Features
- **API Usage Monitoring**: Track requests, tokens, and costs
- **Batch Job Management**: Submit, monitor, and retrieve batch jobs
- **Retry Logic**: Automatic retry with exponential backoff
- **Configuration Validation**: Startup validation of all configuration values
- **Extensible Architecture**: Modular design for easy customization

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- OpenAI API key with active credits
- tkinter (usually included with Python)

### Python Dependencies
```
openai>=1.0.0,<2.0.0
python-dotenv>=1.0.0
```

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Codebook
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key:**
   ```bash
   cp .env.example .env
   # Edit .env and set your OPENAI_API_KEY
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
OPENAI_ORG_ID=your_org_id_here
DEFAULT_MODEL=gpt-4-turbo-preview
BATCH_COMPLETION_WINDOW=24h
BATCH_DESCRIPTION=text_classification
MAX_RETRIES=3
REQUEST_TIMEOUT=60
DEBUG=false
```

### Configuration Validation

The application validates all configuration at startup:
- ✅ API key format verification
- ✅ Model availability checking
- ✅ Parameter range validation
- ✅ Connection testing

## 📊 Usage

### Interactive Mode

Run the application and follow the interactive menu:

```bash
python main.py
```

The application provides:
1. **Live Classification** - Immediate processing
2. **Batch Classification** - Submit jobs for later processing
3. **Batch Management** - Check status, retrieve results, cancel jobs
4. **Usage Statistics** - Monitor API usage and costs

### File Formats

#### Labels CSV
```csv
positive
negative
neutral
```

#### Texts CSV
```csv
text,id,metadata
"This is a great product!",1,sample
"The service was terrible.",2,sample
"It's okay, nothing special.",3,sample
```

### Command Line Options

```bash
python main.py --help          # Show help
python main.py --debug         # Enable debug logging
python main.py --version       # Show version
```

## 🏗️ Architecture

### Project Structure
```
Codebook/
├── core/                      # Core configuration and exceptions
│   ├── __init__.py
│   ├── config.py             # Secure configuration management
│   └── exceptions.py         # Custom exception hierarchy
├── models/                    # Data models and validation
│   ├── __init__.py
│   └── classification.py     # Classification data models
├── services/                  # Business logic services
│   ├── __init__.py
│   ├── openai_service.py     # OpenAI API integration
│   └── classification_service.py  # High-level classification service
├── file_handling/            # File I/O operations
│   ├── __init__.py
│   ├── csv_handler.py        # Professional CSV handling
│   └── json_handler.py       # JSON/JSONL processing
├── main.py                   # Professional CLI interface
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
└── README.md               # This documentation
```

### Design Principles

1. **Separation of Concerns**: Clear boundaries between components
2. **Dependency Injection**: Services receive dependencies explicitly
3. **Error Handling**: Comprehensive exception hierarchy
4. **Configuration Management**: Environment-based, validated configuration
5. **Type Safety**: Full type hints and validation
6. **Resource Management**: Proper cleanup and context managers
7. **Logging**: Structured logging throughout the application

## 📈 Performance & Costs

### Live vs Batch Processing

| Feature | Live | Batch |
|---------|------|-------|
| Cost | Standard rate | 50% discount |
| Speed | Immediate | Up to 24h |
| Best for | < 100 texts | 100+ texts |
| Feedback | Real-time | Asynchronous |

### Usage Monitoring

The application tracks:
- API requests made
- Tokens consumed
- Estimated costs
- Error rates
- Processing times

## 🔧 Development

### Code Quality

The codebase follows professional standards:
- **PEP 8** compliant formatting
- **Type hints** on all functions
- **Comprehensive docstrings** with examples
- **Error handling** at all levels
- **Unit testing** ready structure
- **Logging** throughout the application

### Extending the Application

The modular architecture makes it easy to:
- Add new classification models
- Implement additional file formats
- Create custom processing pipelines
- Add new output formats
- Integrate with other APIs

### Testing

While not included in this version, the architecture supports:
- Unit tests for all components
- Integration tests for API interactions
- Mock testing for external dependencies
- Performance testing for large datasets

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify your API key is correct
   - Check your OpenAI account has sufficient credits
   - Ensure the key has appropriate permissions

2. **File Format Issues**
   - Ensure CSV files are properly formatted
   - Check for special characters or encoding issues
   - Verify column structure matches expectations

3. **Batch Job Issues**
   - Monitor batch status regularly
   - Large jobs may take several hours
   - Check OpenAI dashboard for detailed error information

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
python main.py --debug
```

### Log Files

Application logs include:
- Configuration loading
- API request/response details
- File processing steps
- Error traces with context

## 🤝 Contributing

This codebase demonstrates professional software engineering practices:
- Clear architecture with separation of concerns
- Comprehensive error handling and logging
- Type safety and input validation
- Modular, extensible design
- Professional documentation

## 📄 License

This project is provided as a demonstration of professional software engineering practices. Please review the license terms before use.

## 🙋‍♂️ Support

For issues or questions:
1. Check this README for common solutions
2. Review the application logs for detailed error information
3. Verify your OpenAI API configuration and credits
4. Check the OpenAI API status page for service issues

---

**Codebook v2.0** - Transforming beginner code into professional, enterprise-grade software.