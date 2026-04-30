
![CodebookAI Logo](./assets/BannerNarrow.png)

CodebookAI is a tool designed to assist qualitative researchers in processing large datasets through OpenAI's GPT models (e.g., 4o, 5, o3, etc.). It enables batch processing of text snippets against a set of labels, significantly reducing the cost and time associated with manual coding, as well as a variety of other tools aimed at qualitative data preparation and analysis. 

**New:** CodebookAI now features a modern, responsive UI powered by CustomTkinter with light/dark theme support!

## Getting Started

### Option 1: Download Pre-built Executable (Windows)
- Download the latest .exe ([Get one here](https://github.com/tmaier-kettering/CodebookAI/releases)). This is a standalone application that does not require installation. Just double-click to run. Only tested on Windows 10.

### Option 2: Run from Source (All Platforms)
1. **Requirements:**
   - Python 3.9 or higher
   - tkinter (usually included with Python, but may need separate installation on Linux)

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python main.py
   ```

### Configuration
- CodebookAI requires you to supply an OpenAI API key in the Settings (File > Settings) ([Get one here](https://platform.openai.com/api-keys)). This keeps CodebookAI open-source and free to use. You control your own API key and are responsible for any costs incurred through your usage of OpenAI's services.
- The UI supports light/dark/system theme modes that can be configured in the settings or by modifying `ui/theme_config.py`
- Not sure what CodebookAI can do? Check out the [Example](wiki/Example/Example.md) section.

## System Dependencies

### Linux Users
On Ubuntu/Debian systems, you may need to install tkinter separately:
```bash
sudo apt update && sudo apt install python3-tk
```

On CentOS/RHEL:
```bash
sudo yum install tkinter
```

### macOS & Windows
tkinter is included with Python installations on these platforms.

## Help & Documentation

- [File](./wiki/File/File.md)
- [Data Prep](./wiki/DataPrep/DataPrep.md)
- [LLM Tools](./wiki/LLMTools/LLMTools.md)
- [Data Analysis](./wiki/DataAnalysis/DataAnalysis.md)
- [Help](./wiki/Help/Help.md)
- [Example](wiki/Example/Example.md)

---

## How to Support

[![BuyMeACoffee](./assets/buymeacoffee.png)](https://buymeacoffee.com/professthor)

If you find this tool helpful, consider supporting its development by [buying me a coffee](https://buymeacoffee.com/professthor)! 

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with OpenAI's usage policies when using this application.

## Disclaimer 
This application requires an OpenAI API key and will incur costs based on your usage. Batch processing typically offers significant cost savings compared to individual API calls. Please monitor your usage and costs through the OpenAI dashboard.

Additionally, not all GPT models have been tested and may not work with this software. At this time, the models that have been tested are gpt-4o, gpt-4o-mini, and gpt-5.

---
