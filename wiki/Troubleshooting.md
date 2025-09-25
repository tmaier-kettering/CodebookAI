# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with CodebookAI. If you can't find a solution here, check the [FAQ](FAQ.md) or [report an issue](https://github.com/tmaier-kettering/CodebookAI/issues/new) on GitHub.

## 🚨 Quick Diagnostic Steps

Before diving into specific issues, try these general troubleshooting steps:

1. **Restart CodebookAI**: Closes and reopens the application
2. **Check Internet Connection**: Verify you can access the internet
3. **Check OpenAI Status**: Visit [OpenAI Status Page](https://status.openai.com/)
4. **Review Error Messages**: Note exact error text for troubleshooting
5. **Check API Credits**: Verify account balance in OpenAI dashboard

---

## 🔑 API and Authentication Issues

### "API Key Not Found" Error

#### Symptoms
- Error on startup or when trying to process data
- Settings show empty API key field
- Cannot connect to OpenAI services

#### Diagnosis
1. **Check Settings**: File > Settings > API Key field
2. **Verify Key Format**: Should start with `sk-` followed by characters
3. **Test Key**: Try using key in OpenAI playground
4. **System Keyring**: Check if system credential manager is working

#### Solutions

##### Method 1: Re-enter API Key
1. Go to File > Settings
2. Clear existing API Key field
3. Paste fresh key from OpenAI dashboard
4. Click Save and restart CodebookAI

##### Method 2: Clear Keyring Entry
**Windows**:
1. Open Control Panel > Credential Manager
2. Find CodebookAI entry
3. Delete old entry
4. Re-enter key in CodebookAI settings

**macOS**:
1. Open Keychain Access
2. Search for CodebookAI
3. Delete old entry
4. Re-enter key in CodebookAI settings

**Linux**:
1. Clear keyring: `secret-tool clear service CodebookAI`
2. Re-enter key in CodebookAI settings

### "Invalid API Key" Error

#### Symptoms  
- Key appears in settings but API calls fail
- Error message mentions authentication failure
- Cannot process any data

#### Diagnosis
1. **Key Validity**: Check if key works in OpenAI playground
2. **Key Permissions**: Verify key has necessary permissions
3. **Account Status**: Check OpenAI account is active
4. **Credit Balance**: Ensure sufficient credits available

#### Solutions
1. **Generate New Key**: Create fresh API key in OpenAI dashboard
2. **Check Permissions**: Ensure key has API access rights
3. **Verify Account**: Confirm OpenAI account is in good standing
4. **Add Credits**: Top up account balance if needed

### Rate Limiting Issues

#### Symptoms
- "Rate limit exceeded" errors
- Slow processing or timeouts
- Intermittent failures during large jobs

#### Solutions
1. **Reduce Concurrent Requests**: Lower processing speed in settings
2. **Use Batch Processing**: Switch to batch API for large jobs
3. **Upgrade Plan**: Consider higher OpenAI tier for more requests
4. **Retry Logic**: Enable automatic retries in settings

---

## 📁 File and Data Import Issues

### "File Cannot Be Read" Error

#### Symptoms
- Import fails with file access error
- Preview shows no data
- Cannot select file in wizard

#### Diagnosis
1. **File Permissions**: Check if file is readable
2. **File Lock**: Verify file not open in another application
3. **File Corruption**: Test opening file in Excel/text editor
4. **File Size**: Check if file is too large (>100MB)

#### Solutions
1. **Close Other Applications**: Ensure file not open elsewhere
2. **Copy File**: Make a copy and try importing the copy
3. **Check Permissions**: Ensure read access to file
4. **Reduce File Size**: Split large files into smaller chunks

### "No Columns Detected" Error

#### Symptoms
- Import wizard shows empty preview
- Column selection options not available
- File appears to load but no data shown

#### Diagnosis
1. **File Format**: Verify file is CSV, TSV, or Excel
2. **Delimiter Detection**: Check if correct delimiter used
3. **Encoding Issues**: Look for garbled text in preview
4. **Empty File**: Confirm file contains actual data

#### Solutions
1. **Check Delimiter**: Try different delimiters (comma, tab, semicolon)
2. **Save as UTF-8**: Re-save file with UTF-8 encoding
3. **Remove Empty Rows**: Delete blank rows at top of file
4. **Validate Format**: Open in Excel to verify structure

### "Import Failed" Error

#### Symptoms
- Import starts but fails partway through
- Memory errors during import
- Corrupted or incomplete data

#### Solutions
1. **Reduce File Size**: Split large files into smaller parts
2. **Clean Data**: Remove special characters and formatting
3. **Free Memory**: Close other applications to free RAM
4. **Restart Application**: Clear memory and try again

### Text Encoding Problems

#### Symptoms
- Special characters appear as question marks or boxes
- Foreign language text displays incorrectly
- Import succeeds but text is garbled

#### Solutions
1. **Save as UTF-8**: Re-save file with UTF-8 encoding in Excel
2. **Use Text Editor**: Open in Notepad++ and convert encoding
3. **Check Source**: Verify original data encoding
4. **Clean Characters**: Remove problematic characters if needed

---

## ⚡ Processing and Performance Issues

### Slow Live Processing

#### Symptoms
- Processing takes much longer than expected
- Progress bar moves very slowly
- Individual requests timeout

#### Diagnosis
1. **Model Choice**: Check if using slower/more expensive model
2. **Network Speed**: Test internet connection speed
3. **Text Length**: Verify text snippets aren't too long
4. **API Load**: Check if OpenAI experiencing high demand

#### Solutions
1. **Switch Models**: Try gpt-4o-mini for faster processing
2. **Shorten Text**: Trim lengthy text snippets
3. **Retry Later**: Try processing during off-peak hours
4. **Check Network**: Use wired connection if possible

### Batch Processing Stuck

#### Symptoms
- Batch job shows "in_progress" for >24 hours
- No status updates from OpenAI
- Cannot retrieve results

#### Solutions
1. **Wait Longer**: Batch jobs can take up to 48 hours
2. **Check OpenAI Dashboard**: View job status directly
3. **Contact OpenAI**: Report stuck jobs to OpenAI support
4. **Resubmit**: Cancel and resubmit if necessary

### Memory Errors

#### Symptoms
- Application crashes during processing
- "Out of memory" error messages
- System becomes unresponsive

#### Solutions
1. **Reduce Dataset Size**: Process smaller chunks at a time
2. **Close Other Apps**: Free up available memory
3. **Restart Computer**: Clear all memory usage
4. **Add RAM**: Consider upgrading system memory

### Timeout Errors

#### Symptoms
- Requests fail with timeout messages
- Processing stops unexpectedly
- Connection errors during API calls

#### Solutions
1. **Increase Timeout**: Adjust timeout settings in configuration
2. **Check Network**: Verify stable internet connection
3. **Retry Failed Items**: Process failed items separately
4. **Use Batch Processing**: Switch to batch API for reliability

---

## 🖥️ User Interface Issues

### Window Won't Open

#### Symptoms
- CodebookAI starts but no window appears
- Process running but no interface visible
- Window appears off-screen

#### Solutions
1. **Check Task Manager**: Verify process is running
2. **Alt+Tab**: Try switching to CodebookAI window
3. **Reset Window Position**: Delete configuration file to reset
4. **Multi-Monitor**: Check other displays if using multiple monitors

### Interface Elements Missing

#### Symptoms
- Menus or buttons not visible
- Text cut off or overlapping
- Controls outside window boundaries

#### Solutions
1. **Adjust Window Size**: Try maximizing window
2. **Check Display Scaling**: Adjust system display settings
3. **Reset Interface**: Delete configuration file
4. **Update Graphics Drivers**: Ensure drivers are current

### Settings Won't Save

#### Symptoms
- Changes in settings revert after restart
- Cannot modify configuration values
- Error when clicking Save button

#### Solutions
1. **Check Permissions**: Ensure write access to config directory
2. **Free Disk Space**: Verify sufficient storage available
3. **Run as Administrator**: Try elevated permissions (Windows)
4. **Reset Configuration**: Delete config file and start fresh

---

## 📊 Data Analysis Tool Issues

### Reliability Statistics Errors

#### Symptoms
- "No matching text found" error
- Empty results after analysis
- Incorrect statistics calculations

#### Diagnosis
1. **Text Matching**: Verify identical text between datasets
2. **Column Selection**: Check correct columns selected
3. **Data Format**: Ensure consistent data formatting
4. **Encoding**: Check for character encoding issues

#### Solutions
1. **Exact Text Match**: Ensure text columns have identical content
2. **Clean Data**: Remove extra whitespace and formatting
3. **Check Headers**: Verify "has headers" setting correct
4. **Preview Data**: Use preview to verify column contents

### Correlogram Display Problems

#### Symptoms
- Correlogram window won't open
- Blank or corrupted visualization
- Error messages during plot generation

#### Solutions
1. **Graphics Backend**: Restart application to reset graphics
2. **Reduce Data Size**: Try with smaller dataset
3. **Change Color Scheme**: Try different color palette
4. **System Graphics**: Update graphics drivers

### Export Issues

#### Symptoms
- Cannot save analysis results
- Excel files corrupted or won't open
- Missing data in exported files

#### Solutions
1. **File Permissions**: Check write permissions to target directory
2. **Close Excel**: Ensure Excel not running when saving
3. **Try Different Location**: Save to different folder
4. **Rename File**: Use different filename to avoid conflicts

---

## 🌐 Network and Connectivity Issues

### Cannot Connect to OpenAI

#### Symptoms
- Network errors during API calls
- "Connection refused" messages
- Timeouts on all requests

#### Diagnosis
1. **Internet Access**: Test general internet connectivity
2. **Firewall**: Check if firewall blocking CodebookAI
3. **Proxy Settings**: Verify proxy configuration if applicable
4. **DNS Issues**: Try different DNS servers

#### Solutions
1. **Check Firewall**: Allow CodebookAI through firewall
2. **Proxy Configuration**: Set proxy settings if behind corporate firewall
3. **Use Different Network**: Try mobile hotspot or different WiFi
4. **Contact IT**: Check with IT department about restrictions

### SSL/Certificate Errors

#### Symptoms
- Certificate validation errors
- SSL handshake failures
- Security warnings during API calls

#### Solutions
1. **Update System**: Ensure OS and certificates are current
2. **Check Date/Time**: Verify system clock is accurate
3. **Corporate Network**: Contact IT about certificate policies
4. **Bypass Validation**: Temporarily disable SSL verification (not recommended)

---

## 🔧 Installation and Startup Issues

### Application Won't Start

#### Symptoms
- Double-click executable but nothing happens
- Error messages on startup
- Application crashes immediately

#### Diagnosis
1. **System Requirements**: Verify Python 3.9+ and dependencies
2. **Missing Libraries**: Check for tkinter and other requirements
3. **Antivirus**: Check if antivirus blocking application
4. **File Corruption**: Verify executable integrity

#### Solutions
1. **Install Dependencies**: Run `pip install -r requirements.txt`
2. **Antivirus Exception**: Add CodebookAI to antivirus whitelist
3. **Re-download**: Download fresh copy of application
4. **Run from Terminal**: Execute from command line to see errors

### Python Environment Issues

#### Symptoms
- "Python not found" errors
- Module import failures
- Version compatibility warnings

#### Solutions
1. **Check Python Version**: Ensure Python 3.9 or higher
2. **Virtual Environment**: Use virtual environment for dependencies
3. **Reinstall Packages**: Reinstall requirements.txt packages
4. **Path Issues**: Add Python to system PATH

### Permission Errors

#### Symptoms
- "Access denied" when starting application
- Cannot write to configuration directory
- Keyring access failures

#### Solutions
1. **Run as Administrator**: Try elevated permissions (Windows)
2. **Check Folder Permissions**: Verify write access to application folder
3. **User Account**: Ensure using account with appropriate permissions
4. **Antivirus**: Check if antivirus interfering with file access

---

## 🐛 Debugging and Logging

### Enabling Debug Mode

To get more detailed error information:

1. **Configuration File**: Edit config.json to enable debug mode
2. **Command Line**: Run with debug flags if available
3. **Log Files**: Check application logs for detailed errors
4. **Verbose Output**: Enable verbose logging in settings

### Log File Locations

#### Windows
```
%APPDATA%\CodebookAI\logs\
```

#### macOS
```
~/Library/Application Support/CodebookAI/logs/
```

#### Linux
```
~/.config/CodebookAI/logs/
```

### What to Include in Bug Reports

When reporting issues:

1. **Error Messages**: Exact text of error messages
2. **Steps to Reproduce**: Detailed steps to recreate issue
3. **System Information**: OS version, Python version, etc.
4. **Log Files**: Relevant portions of log files
5. **Data Examples**: Sample data that causes issues (anonymized)

---

## 📞 Getting Additional Help

### Self-Help Resources

1. **[FAQ](FAQ.md)**: Common questions and answers
2. **[Configuration Guide](Configuration.md)**: Settings and preferences
3. **[Best Practices](Best-Practices.md)**: Tips for optimal usage
4. **[GitHub Issues](https://github.com/tmaier-kettering/CodebookAI/issues)**: Known issues and solutions

### Community Support

1. **GitHub Discussions**: Community Q&A and tips
2. **Issue Tracker**: Report bugs and request features
3. **Documentation**: Comprehensive guides and references
4. **Examples**: Sample workflows and use cases

### Reporting Bugs

When creating a GitHub issue:

1. **Search First**: Check if issue already reported
2. **Clear Title**: Descriptive title summarizing the problem
3. **Detailed Description**: Complete description with steps to reproduce
4. **System Info**: Operating system, Python version, CodebookAI version
5. **Logs**: Include relevant error messages and log excerpts
6. **Data**: Provide sample data if relevant (remove sensitive information)

### Feature Requests

For suggesting new features:

1. **Check Existing**: Search for similar feature requests
2. **Use Case**: Explain why feature would be valuable
3. **Details**: Provide specific description of desired functionality
4. **Examples**: Give examples of how feature would be used
5. **Alternatives**: Mention any current workarounds

---

## 🔄 Recovery Procedures

### Complete Reset

If CodebookAI is completely broken:

1. **Backup Data**: Save any important results or configurations
2. **Uninstall**: Remove current installation
3. **Clean Configuration**: Delete configuration directories
4. **Fresh Install**: Download and install latest version
5. **Restore Data**: Import backed up data and reconfigure

### Configuration Reset

To reset just settings:

1. **Locate Config**: Find configuration file location
2. **Backup Current**: Save copy of current configuration
3. **Delete Config**: Remove configuration file
4. **Restart App**: Launch CodebookAI to create fresh config
5. **Reconfigure**: Re-enter settings and preferences

### Selective Recovery

To fix specific issues:

1. **Identify Problem**: Determine specific component causing issues
2. **Backup Working Parts**: Save functional configurations
3. **Reset Problem Area**: Clear problematic settings only
4. **Test Fix**: Verify issue is resolved
5. **Restore Preferences**: Restore non-problematic settings

---

*Still having issues? Check the [FAQ](FAQ.md) for common questions or [report an issue](https://github.com/tmaier-kettering/CodebookAI/issues/new) on GitHub for personalized help.*