Had these files as part of local exp
Kinda was clutering the system
Folder reorg-ed courtesy Cowork

# Microsoft Teams SDK - Meeting & Transcript Management

A Python SDK for creating Microsoft Teams meetings and managing transcripts using the Microsoft Graph API.

## Features

- OAuth 2.0 authentication with PKCE flow
- Create Teams meetings with automatic recording and transcription
- Download meeting transcripts in VTT format
- Webhook subscriptions for transcript notifications
- Automatic token refresh

## Prerequisites

- Python 3.7+
- Microsoft Azure App Registration with the following permissions:
  - `OnlineMeetings.ReadWrite`
  - `OnlineMeetingTranscript.Read.All`
  - `User.Read`

## Setup

### 1. Clone and Install Dependencies

```bash
cd teams-sdk
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your Azure app credentials:

```bash
cp env.example .env
```

Edit `.env` with your Azure app details:

```
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
TENANT_ID=your-tenant-id-here
REDIRECT_URI=http://localhost:8000/callback
```

### 3. Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
3. Configure:
   - **Name**: Your app name
   - **Redirect URI**: `http://localhost:8000/callback` (or your custom URI)
4. After creation:
   - Copy the **Application (client) ID** → `CLIENT_ID`
   - Copy the **Directory (tenant) ID** → `TENANT_ID`
   - Go to **Certificates & secrets** → Create new client secret → Copy value → `CLIENT_SECRET`
5. Go to **API permissions** → Add permissions:
   - Microsoft Graph → Delegated permissions:
     - `OnlineMeetings.ReadWrite`
     - `OnlineMeetingTranscript.Read.All`
     - `User.Read`
   - Click **Grant admin consent**

## Usage

### Quick Start

```bash
cd meet-creation

# 1. First time: Authenticate
python auth.py

# 2. Create a meeting
python create_meeting_main.py

# 3. Download transcript (wait 5-15 mins after meeting ends)
python pull_transcript_main.py
```

### Authentication

First, authenticate and save your tokens:

```bash
cd meet-creation
python auth.py
```

This will:
1. Open a browser for OAuth authentication
2. Save your access and refresh tokens to `teams_tokens.json`
3. Store user information

**Note**: `teams_tokens.json` is gitignored and should never be committed!

### Creating a Meeting

```bash
python create_meeting_main.py
```

Features:
- Automatically refreshes expired tokens
- Creates meeting with recording and transcription enabled
- Returns meeting join URL and ID

**Important**: Save the meeting ID - you'll need it to download transcripts!

### Downloading Transcripts

After a meeting ends (transcripts may take 5-15 minutes to be available):

```bash
python pull_transcript_main.py
```

Enter the meeting ID when prompted. Transcripts will be saved to the `transcripts/` folder in VTT format.

## Project Structure

```
teams-sdk/
├── meet-creation/                    # Main scripts (see meet-creation/README.md)
│   ├── auth.py                      # 🔐 Authentication & token management
│   ├── create_meeting_main.py       # 📅 Create Teams meetings
│   ├── pull_transcript_main.py      # 📝 Download transcripts
│   ├── examples/                    # Advanced usage examples
│   │   ├── webhook_handler.py       # Flask webhook server
│   │   ├── transcript_poller.py     # Auto-polling for transcripts
│   │   └── subscription_manager.py  # Webhook subscription setup
│   ├── utils/                       # Diagnostic & debug tools
│   │   ├── check_permissions.py     # Verify API permissions
│   │   ├── diagnosis.py             # System diagnostics
│   │   ├── subscription_review.py   # Review subscriptions
│   │   └── debug.py                 # Advanced debugging
│   ├── archive/                     # Archived experiments
│   │   └── v2-experiments/          # Version 2 code
│   ├── transcripts/                 # Downloaded transcripts (gitignored)
│   └── README.md                    # Detailed usage guide
│
├── teams_meeting_creation_context/  # Reusable library modules
│   ├── config.py                    # Configuration management
│   ├── team_api.py                  # API wrappers
│   ├── team_auth.py                 # Authentication helpers
│   └── example_flow.py              # Usage examples
│
├── .gitignore                       # Git ignore rules
├── env.example                      # Environment template
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Folder Organization

### `meet-creation/` - Main Scripts

**Production Scripts** (use these!):
- **`auth.py`**: OAuth authentication and token management
- **`create_meeting_main.py`**: Create meetings with auto-recording/transcription
- **`pull_transcript_main.py`**: Download meeting transcripts

**See `meet-creation/README.md` for detailed documentation!**

### `meet-creation/examples/` - Advanced Features

Experimental/advanced usage:
- **`webhook_handler.py`**: Flask server for real-time notifications
- **`transcript_poller.py`**: Automated transcript polling
- **`subscription_manager.py`**: Setup webhook subscriptions

### `meet-creation/utils/` - Diagnostic Tools

Troubleshooting and debugging:
- **`check_permissions.py`**: Verify Azure app permissions
- **`diagnosis.py`**: Comprehensive diagnostic information
- **`subscription_review.py`**: Review active subscriptions
- **`debug.py`**: Advanced debugging tools

### `meet-creation/archive/` - Archived Code

Older experimental code kept for reference (may not work with current setup)

### `teams_meeting_creation_context/` - Reusable Modules

Library modules for integration into other projects

## Security Notes

⚠️ **Important Security Practices**:

1. **Never commit secrets**: The `.gitignore` is configured to exclude:
   - `.env` files
   - `*_tokens.json` files
   - `teams_tokens.json`

2. **Token Management**:
   - Access tokens expire after ~1 hour
   - Refresh tokens are automatically used to get new access tokens
   - Tokens are stored locally in `teams_tokens.json`

3. **Production Deployment**:
   - Use Azure Key Vault or similar for secrets
   - Implement proper token encryption at rest
   - Use secure webhook endpoints (HTTPS only)

## Troubleshooting

### "teams_tokens.json not found"
Run `python save_at.py` to authenticate first.

### "Failed to refresh token"
Your refresh token may have expired. Re-run `python save_at.py` to re-authenticate.

### "No transcripts found"
Transcripts can take 5-15 minutes after a meeting ends to become available. Wait and try again.

### "Failed to create meeting" (403 Forbidden)
Check that your Azure app has the correct permissions and admin consent has been granted.

## API Scopes

- `OnlineMeetings.ReadWrite`: Create and manage online meetings
- `OnlineMeetingTranscript.Read.All`: Read meeting transcripts
- `User.Read`: Read user profile information
- `offline_access`: Get refresh tokens for long-term access

## Development

### Adding New Features

1. Create new scripts in `meet-creation/` for experimentation
2. Move stable code to `meet-creation/fin_sol/`
3. Extract reusable components to `teams_meeting_creation_context/`

### Testing

Always test with a non-production Azure app registration during development.

## Contributing

This is an experimental/personal project. Feel free to fork and adapt for your needs.

## License

See LICENSE file for details.

## Resources

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/api/overview)
- [Online Meetings API](https://learn.microsoft.com/en-us/graph/api/resources/onlinemeeting)
- [Transcript API](https://learn.microsoft.com/en-us/graph/api/resources/calltranscript)
