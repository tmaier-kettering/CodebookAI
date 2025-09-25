# Installation Guide

This guide will walk you through the process of installing and setting up CodebookAI on your system.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Python**: Version 3.9 or higher with tkinter support
- **Memory**: At least 4GB RAM (8GB recommended for large datasets)
- **Storage**: 500MB free space for installation

### OpenAI API Key
You'll need an OpenAI API key to use CodebookAI:
1. Visit [OpenAI's API Keys page](https://platform.openai.com/api-keys)
2. Create an account or log in
3. Generate a new API key
4. Keep this key secure - you'll need it during setup

> ⚠️ **Important**: Monitor your API usage and costs through the [OpenAI dashboard](https://platform.openai.com/usage). Batch processing offers significant cost savings compared to individual API calls.

## 🚀 Installation Options

### Option 1: Pre-built Executable (Recommended)

1. **Download the latest release**:
   - Go to [GitHub Releases](https://github.com/tmaier-kettering/CodebookAI/releases)
   - Download `CodebookAI-v1.0.0.exe` (or latest version)

2. **Run the application**:
   - Double-click the downloaded `.exe` file
   - The application will launch directly
   - Follow the first-time setup wizard

### Option 2: Python Installation (Advanced Users)

#### Step 1: Install Python
Make sure you have Python 3.9+ installed:

```bash
python --version
```

If you need to install Python:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: Use Homebrew: `brew install python3`
- **Linux**: Use your package manager: `sudo apt install python3 python3-pip python3-tk`

#### Step 2: Install tkinter (Linux only)
On Ubuntu/Debian:
```bash
sudo apt update && sudo apt install python3-tk
```

On CentOS/RHEL:
```bash
sudo yum install tkinter
```

#### Step 3: Clone the Repository
```bash
git clone https://github.com/tmaier-kettering/CodebookAI.git
cd CodebookAI
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Run the Application
```bash
python main.py
```

## ⚙️ First-Time Setup

When you launch CodebookAI for the first time:

### 1. API Key Configuration
- The settings window will automatically open
- Paste your OpenAI API key in the **API Key** field
- The key is stored securely using your system's keyring

### 2. Model Selection
- Choose your preferred AI model (default: `gpt-4o`)
- Available models:
  - `gpt-4o` - Best balance of capability and cost
  - `gpt-4o-mini` - Most cost-effective option
  - `gpt-4-turbo` - High performance
  - `o1-preview` - Advanced reasoning (where available)

### 3. Timezone Settings
- Set your timezone for accurate batch processing timestamps
- This affects how completion times are displayed

### 4. Other Preferences
- **Max Batches**: Number of recent batches to display (default: 4)
- Other settings can be adjusted later

## ✅ Verify Installation

1. **Launch CodebookAI**
2. **Check the main window** - you should see:
   - CodebookAI title and subtitle
   - Menu bar with File, Data Prep, LLM Tools, Data Analysis, and Help

3. **Test API Connection**:
   - Go to **File > Settings**
   - Verify your API key is saved
   - Try a small live processing task to confirm connectivity

## 🔧 Troubleshooting Installation Issues

### Common Issues

#### "Python not found" Error
- Ensure Python 3.9+ is installed and in your PATH
- On Windows, check "Add Python to PATH" during installation

#### "No module named tkinter" Error
- **Linux**: Install tkinter: `sudo apt install python3-tk`
- **macOS**: Reinstall Python from python.org (includes tkinter)
- **Windows**: Tkinter is included with Python

#### Dependencies Installation Fails
```bash
# Try upgrading pip first
pip install --upgrade pip

# Install dependencies one by one if batch fails
pip install openai>=1.100.0
pip install pandas>=2.0.0
pip install pydantic>=2.0.0
pip install openpyxl>=3.1.0
pip install keyring>=25.0.0
```

#### Application Won't Start
1. Check Python version: `python --version`
2. Verify all dependencies: `pip list | grep -E "(openai|pandas|pydantic|openpyxl|keyring)"`
3. Run with verbose error output: `python -v main.py`

### Platform-Specific Notes

#### Windows
- Use Command Prompt or PowerShell
- Some antivirus software may flag the executable - add an exception if needed
- Ensure you have the Microsoft Visual C++ Redistributable installed

#### macOS
- You may need to allow the app in Security & Privacy settings
- If using Homebrew Python, ensure tkinter is available: `python3 -m tkinter`

#### Linux
- Ensure you have the X11 display server running for GUI applications
- Some distributions require additional packages for full functionality

## 🔄 Updating CodebookAI

### For Executable Users
1. Download the latest release from GitHub
2. Replace the old executable with the new one
3. Your settings and data are preserved

### For Python Installation Users
```bash
cd CodebookAI
git pull origin main
pip install -r requirements.txt --upgrade
```

## 📁 File Locations

### Settings and Configuration
- **Windows**: `%APPDATA%\CodebookAI\`
- **macOS**: `~/Library/Application Support/CodebookAI/`
- **Linux**: `~/.config/CodebookAI/`

### API Key Storage
API keys are stored securely in your system's credential manager:
- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring, KWallet, etc.)

## 🆘 Getting Help

If you encounter issues during installation:

1. **Check the [Troubleshooting Guide](Troubleshooting.md)**
2. **Search existing [GitHub Issues](https://github.com/tmaier-kettering/CodebookAI/issues)**
3. **Create a new issue** with:
   - Your operating system and version
   - Python version
   - Complete error message
   - Steps to reproduce the problem

## 🎉 Next Steps

Once installation is complete:
1. **Read the [Quick Start Guide](Quick-Start.md)** for your first project
2. **Explore [Sample Workflows](Sample-Workflows.md)** to understand capabilities
3. **Check out the [Live Processing Guide](Live-Processing.md)** for immediate results

---

*Installation complete? Great! Ready to start your first text classification project? Head to the [Quick Start Guide](Quick-Start.md).*
