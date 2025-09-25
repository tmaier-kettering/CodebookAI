# Configuration Guide

CodebookAI offers extensive configuration options to customize your experience and optimize performance for your specific research needs. This guide covers all settings, from basic API configuration to advanced preferences.

## ⚙️ Accessing Settings

### Settings Window
1. **Navigate**: File > Settings
2. **Keyboard Shortcut**: Ctrl+, (Windows/Linux) or Cmd+, (macOS)
3. **First Launch**: Settings automatically open when no API key is configured

### Settings Categories
- **API Configuration**: OpenAI API key and model selection
- **Processing Preferences**: Batch limits and timeout settings  
- **Display Options**: Timezone and interface preferences
- **Advanced Settings**: Developer and debugging options

---

## 🔑 API Configuration

### OpenAI API Key

#### Setting Your API Key
1. **Obtain Key**: Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. **Copy Key**: Starts with `sk-` followed by alphanumeric characters
3. **Paste in Settings**: API Key field in CodebookAI settings
4. **Secure Storage**: Key stored in system keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)

#### API Key Security
- **Local Storage**: Keys never leave your system
- **Encrypted**: Stored using OS-level encryption
- **No Logging**: Keys never appear in logs or error messages
- **Revocable**: Can be changed/revoked anytime from OpenAI dashboard

#### Troubleshooting API Keys
**"Invalid API Key" Error**:
- Verify key is copied correctly (no extra spaces)
- Check key is active in OpenAI dashboard
- Ensure sufficient credits in OpenAI account
- Try regenerating key if issues persist

**"API Key Not Found"**:
- Re-enter key in settings
- Restart CodebookAI after setting key
- Check system keyring permissions

### Model Selection

#### Available Models

##### GPT-4o (Recommended)
- **Best Balance**: Optimal mix of capability and cost
- **Use For**: General text classification, most research tasks
- **Strengths**: Good accuracy, reasonable cost, fast processing
- **Cost**: Moderate (varies by OpenAI pricing)

##### GPT-4o-mini (Budget Option)
- **Most Economical**: Lowest cost option
- **Use For**: Simple classifications, large datasets, testing
- **Strengths**: Very low cost, fast processing, good for basic tasks
- **Cost**: Lowest (typically 60-80% less than GPT-4o)

##### GPT-4-turbo (High Performance)
- **Highest Capability**: Best reasoning and nuance understanding
- **Use For**: Complex classifications, nuanced text analysis
- **Strengths**: Superior accuracy, complex reasoning, large context
- **Cost**: Highest (premium pricing)

##### o1-preview (Advanced Reasoning)
- **Specialized**: Advanced reasoning capabilities
- **Use For**: Complex analytical tasks requiring deep reasoning
- **Strengths**: Sophisticated problem solving, multi-step reasoning
- **Cost**: Premium (limited availability)

#### Model Selection Guidelines

##### For Different Use Cases
- **Academic Research**: GPT-4o for balance of quality and cost
- **Large-Scale Content Analysis**: GPT-4o-mini for cost efficiency
- **High-Stakes Classification**: GPT-4-turbo for maximum accuracy
- **Complex Analytical Tasks**: o1-preview when available

##### Testing Strategy
1. **Start with mini**: Test label sets and data quality
2. **Validate with 4o**: Confirm results meet quality standards
3. **Scale production**: Use appropriate model for full dataset
4. **Cost monitoring**: Track usage and adjust model choice

---

## 🎛️ Processing Preferences

### Batch Processing Settings

#### Max Batches Display
- **Default**: 4 recent batches
- **Range**: 1-20 batches
- **Purpose**: Controls how many recent batch jobs show in main interface
- **Impact**: More batches = more memory usage, but better history visibility

#### Timeout Settings
- **Request Timeout**: Maximum wait time for individual API calls
- **Default**: 120 seconds
- **Range**: 30-600 seconds
- **Considerations**: Longer timeouts handle larger texts but may hang on errors

#### Retry Configuration
- **Auto-Retry**: Automatic retry on temporary failures
- **Retry Count**: Number of automatic retry attempts
- **Backoff Strategy**: Progressive delay between retries
- **Error Handling**: How to handle persistent failures

### Live Processing Settings

#### Progress Updates
- **Update Frequency**: How often progress bar updates
- **Status Messages**: Verbosity of processing messages
- **Error Reporting**: Level of detail in error reports
- **Completion Notifications**: Desktop notifications for task completion

#### Processing Limits
- **Concurrent Requests**: Number of simultaneous API calls
- **Rate Limiting**: Respect OpenAI rate limits
- **Queue Management**: How requests are queued and processed
- **Memory Usage**: Optimize for available system memory

---

## 🌐 Display and Interface Options

### Timezone Settings

#### Importance of Timezone
- **Batch Timestamps**: When batch jobs were submitted and completed
- **Result Metadata**: Creation and modification times
- **Logging**: All time-stamped events in logs
- **Collaboration**: Consistent timing across team members

#### Setting Your Timezone
1. **Auto-Detection**: System timezone detected automatically
2. **Manual Selection**: Choose from comprehensive timezone list
3. **Common Zones**: Quick selection for major timezones
4. **UTC Option**: Use UTC for international collaboration

#### Supported Timezones
- **All IANA Zones**: Complete list of timezone identifiers
- **Major Cities**: New York, London, Tokyo, Sydney, etc.
- **UTC Offsets**: GMT+/-X format support
- **DST Handling**: Automatic daylight saving time adjustments

### Interface Preferences

#### Window Settings
- **Default Size**: Initial window dimensions
- **Position Memory**: Remember window location between sessions
- **Maximize State**: Start maximized or windowed
- **Multi-Monitor**: Support for multiple display setups

#### Visual Preferences
- **Font Size**: Adjust text size for readability
- **Color Theme**: Light/dark theme options (if available)
- **Progress Indicators**: Style and frequency of progress updates
- **Status Messages**: Verbosity of user feedback

---

## 🔧 Advanced Configuration

### Developer Options

#### Debug Mode
- **Verbose Logging**: Detailed operation logs
- **API Call Logging**: Log all OpenAI API interactions (excluding keys)
- **Error Details**: Extended error information
- **Performance Metrics**: Timing and resource usage data

#### Experimental Features
- **Beta Functionality**: Access to new features in development
- **Advanced Models**: Early access to new OpenAI models
- **Custom Endpoints**: Support for OpenAI-compatible APIs
- **Feature Flags**: Toggle experimental capabilities

### Performance Tuning

#### Memory Management
- **Cache Size**: Amount of data cached for performance
- **Garbage Collection**: Memory cleanup frequency
- **Large File Handling**: Optimization for big datasets
- **Preview Limits**: Maximum rows shown in data previews

#### Network Settings
- **Connection Timeout**: Maximum wait for network requests
- **Proxy Support**: Configure proxy servers if needed
- **SSL Verification**: Certificate validation settings
- **User Agent**: Custom user agent for API requests

---

## 📁 Configuration Storage

### Settings File Locations

#### Windows
```
%APPDATA%\CodebookAI\config.json
```

#### macOS
```
~/Library/Application Support/CodebookAI/config.json
```

#### Linux
```
~/.config/CodebookAI/config.json
```

### Configuration Format

#### JSON Structure
```json
{
  "api": {
    "model": "gpt-4o",
    "timeout": 120,
    "retries": 3
  },
  "display": {
    "timezone": "America/New_York",
    "max_batches": 4,
    "window_size": [1000, 620]
  },
  "processing": {
    "concurrent_requests": 5,
    "progress_updates": true,
    "notifications": true
  }
}
```

#### Manual Editing
- **Backup First**: Always backup before manual edits
- **Valid JSON**: Ensure proper JSON formatting
- **Restart Required**: Changes require application restart
- **Validation**: Invalid settings revert to defaults

---

## 🔄 Configuration Management

### Backup and Restore

#### Creating Backups
1. **Locate Settings**: Find config file using paths above
2. **Copy File**: Make backup copy with date suffix
3. **Document Changes**: Note what settings were modified
4. **Test Restore**: Verify backup works before major changes

#### Restoring Settings
1. **Close CodebookAI**: Ensure application is not running
2. **Replace File**: Copy backup over current config
3. **Restart App**: Launch CodebookAI to load restored settings
4. **Verify Settings**: Check that preferences are correct

### Sharing Configurations

#### Team Standardization
- **Export Settings**: Share config file with team members
- **Standard Models**: Agree on consistent model choices
- **Timezone Sync**: Use common timezone for collaboration
- **Processing Standards**: Consistent timeout and retry settings

#### Version Control
- **Track Changes**: Document configuration modifications
- **Environment-Specific**: Different settings for dev/prod
- **Migration**: Update configs when upgrading CodebookAI
- **Documentation**: Maintain notes on configuration decisions

---

## 🛠️ Troubleshooting Configuration Issues

### Common Problems

#### Settings Not Saving
**Causes**:
- Insufficient file permissions
- Disk space issues
- Application crash during save
- Invalid configuration values

**Solutions**:
- Check file/folder permissions
- Free up disk space
- Restart application and re-enter settings
- Validate JSON syntax if manually edited

#### API Configuration Problems
**Causes**:
- Incorrect API key format
- Expired or revoked keys
- Network connectivity issues
- OpenAI service outages

**Solutions**:
- Verify key format (starts with sk-)
- Check OpenAI dashboard for key status
- Test internet connection
- Check OpenAI status page

#### Display Issues
**Causes**:
- Invalid timezone identifier
- Display scaling problems
- Missing system fonts
- Multi-monitor setup changes

**Solutions**:
- Select timezone from dropdown list
- Adjust system display scaling
- Check font availability
- Reset window position settings

### Resetting Configuration

#### Full Reset
1. **Close CodebookAI**
2. **Delete Config File**: Remove from appropriate location
3. **Restart Application**: Fresh settings will be created
4. **Reconfigure**: Re-enter all preferences

#### Selective Reset
1. **Backup Current Config**: Save copy of existing file
2. **Edit Config File**: Remove only problematic sections
3. **Restart Application**: Defaults will be used for missing sections
4. **Adjust Settings**: Fine-tune through Settings window

---

## 💡 Configuration Best Practices

### Security Best Practices

#### API Key Management
- **Regular Rotation**: Change API keys periodically
- **Least Privilege**: Use keys with minimum required permissions
- **Monitor Usage**: Track API usage through OpenAI dashboard
- **Secure Sharing**: Never share API keys via email or chat

#### System Security
- **User Permissions**: Run CodebookAI with standard user privileges
- **Firewall**: Allow necessary network connections only
- **Updates**: Keep CodebookAI updated to latest version
- **Backup**: Regular backup of configuration and data

### Performance Optimization

#### Model Selection Strategy
- **Test Phase**: Use gpt-4o-mini for initial testing
- **Validation**: Compare results across different models
- **Production**: Choose optimal model for accuracy/cost balance
- **Monitoring**: Track performance metrics over time

#### Resource Management
- **Memory Limits**: Be aware of system memory constraints
- **Disk Space**: Monitor storage for batch results and logs
- **Network**: Consider bandwidth limitations for large datasets
- **Processing Power**: Adjust concurrent requests based on system capabilities

### Collaboration Settings

#### Team Coordination
- **Consistent Models**: Use same model across team members
- **Shared Timezones**: Agree on common timezone for timestamps  
- **Standard Configurations**: Share baseline configuration files
- **Documentation**: Document team-specific configuration decisions

#### Project Management
- **Environment Separation**: Different configs for different projects
- **Version Tracking**: Document configuration changes over time
- **Quality Assurance**: Establish configuration standards for quality
- **Backup Strategy**: Ensure configurations are backed up regularly

---

## 📋 Configuration Checklist

### Initial Setup
- [ ] OpenAI API key entered and verified
- [ ] Appropriate model selected for use case
- [ ] Timezone set to local preference
- [ ] Display preferences configured
- [ ] Network settings verified (if behind proxy)

### Regular Maintenance
- [ ] API key rotation schedule established
- [ ] Configuration backup created
- [ ] Usage monitoring in place
- [ ] Performance metrics reviewed
- [ ] Team configurations synchronized

### Before Major Projects
- [ ] Model choice validated for project requirements
- [ ] Timeout settings appropriate for data size
- [ ] Batch limits configured for expected volume
- [ ] Error handling preferences set
- [ ] Notification settings enabled

---

## 🔗 Related Topics

- **[Installation Guide](Installation-Guide.md)**: Initial setup and prerequisites
- **[Quick Start](Quick-Start.md)**: First-time configuration walkthrough
- **[Troubleshooting](Troubleshooting.md)**: Detailed problem resolution
- **[Best Practices](Best-Practices.md)**: Optimization and efficiency tips

---

*Need help with specific configuration issues? Check the [Troubleshooting Guide](Troubleshooting.md) for detailed solutions to common problems.*