# Settings

## Accessing Settings
**Navigate**: File > Settings

## Settings
- **API Key**: OpenAI API key
- **Model**: Which model from OpenAI to use for all LLM tools
- **Batch Limits**: Max batches to retrieve from OpenAI (currently not functional)
- **Timezone**: Timezone

---

## 💾 Settings Storage

### User Settings Location
User-configurable settings are stored in platform-appropriate directories:
- **Windows**: `%APPDATA%\CodebookAI\config.json`
- **macOS**: `~/Library/Application Support/CodebookAI/config.json`
- **Linux**: `~/.config/CodebookAI/config.json`

### Configuration System
- **Application Defaults**: Read from `settings/config.py` (read-only)
- **User Overrides**: Stored in user-specific JSON configuration file
- **Merged Configuration**: User settings override defaults at runtime
- **Bundled Application Safe**: Works correctly in PyInstaller and other bundled environments

---

## 🔑 API Key Configuration

### Setting Your API Key
1. **Obtain Key**: Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. **Copy Key**: Starts with `sk-` followed by alphanumeric characters
3. **Paste in Settings**: API Key field in CodebookAI settings
4. **Secure Storage**: Key stored in system keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)

### API Key Security
- **Local Storage**: Keys never leave your system
- **Encrypted**: Stored using OS-level encryption
- **No Logging**: Keys never appear in logs or error messages
- **Revocable**: Can be changed/revoked anytime from OpenAI dashboard

---
