# Teams Meeting Creation Scripts

Clean, organized scripts for Microsoft Teams meeting management.

## Quick Start

### 1. First Time Setup - Authenticate

```bash
python auth.py
```

This will:
- Open browser for OAuth authentication
- Save your tokens to `teams_tokens.json`
- Store user information

### 2. Create a Meeting

```bash
python create_meeting_main.py
```

Creates a Teams meeting with:
- Automatic recording enabled
- Automatic transcription enabled
- Returns join URL and meeting ID

### 3. Download Meeting Transcript

```bash
python pull_transcript_main.py
```

Downloads transcripts after a meeting ends (transcripts may take 5-15 minutes to become available).

---
## Main Scripts

### `auth.py`
**Purpose**: Initial authentication and token management

**When to use**: 
- First time setup
- When refresh token expires
- To re-authenticate

**What it does**:
- Generates OAuth URL with PKCE
- Exchanges auth code for access/refresh tokens
- Saves tokens to `teams_tokens.json`
- Retrieves and stores user info

**Usage**:
```bash
python auth.py
```

Follow the OAuth flow in your browser, paste the redirect URL when prompted.

---

### `create_meeting_main.py`
**Purpose**: Create Teams meetings with recording and transcription

**When to use**:
- Whenever you need to create a new Teams meeting
- Meetings will have auto-recording and transcription enabled

**What it does**:
- Automatically refreshes expired tokens
- Creates meeting 5 minutes from now
- Enables recording and transcription
- Returns meeting details (join URL, meeting ID)

**Usage**:
```bash
python create_meeting_main.py
# Enter meeting subject when prompted (or press Enter for default)
```

**Output**:
```
Meeting created successfully!
Join URL: https://teams.microsoft.com/l/meetup-join/...
Meeting ID: MSo...
```

**Save the Meeting ID** - you'll need it to download transcripts later!

---

### `pull_transcript_main.py`
**Purpose**: Download meeting transcripts in VTT format

**When to use**:
- After a meeting ends (wait 5-15 minutes for processing)
- To retrieve transcripts for archival/analysis

**What it does**:
- Automatically refreshes expired tokens
- Fetches all transcripts for a meeting
- Downloads transcripts in VTT format
- Saves to `transcripts/` folder

**Usage**:
```bash
python pull_transcript_main.py
# Enter meeting ID when prompted
```

**Note**: Transcripts can take 5-15 minutes to become available after a meeting ends. If you get "No transcripts found", wait a bit and try again.

---

## Examples (Advanced Usage)

### `examples/webhook_handler.py`
**Flask webhook server** for receiving real-time transcript notifications.

**Setup**:
1. Install Flask: `pip install flask`
2. Set up ngrok: `ngrok http 5000`
3. Update `WEBHOOK_BASE_URL` in `.env`
4. Run: `python webhook_handler.py`

**Use case**: Automatically process transcripts as soon as they're available.

---

### `examples/transcript_poller.py`
**Automated polling script** that checks for new transcripts periodically.

**Usage**:
```bash
python transcript_poller.py
# Enter meeting ID and polling interval
```

**Use case**: Continuously monitor for transcript availability without webhooks.

---

### `examples/subscription_manager.py`
**Setup webhook subscriptions** for transcript notifications.

**What it does**:
- Authenticates user
- Creates Graph API subscription
- Registers webhook URL for transcript notifications

**Usage**:
```bash
python subscription_manager.py
```

**Requirements**: You need a publicly accessible webhook endpoint.

---

## Utils (Diagnostic Tools)

### `utils/check_permissions.py`
Verify that your Azure app has the correct API permissions.

**Usage**:
```bash
python utils/check_permissions.py
```

**Checks**:
- `OnlineMeetings.ReadWrite`
- `OnlineMeetingTranscript.Read.All`
- `User.Read`

---

### `utils/diagnosis.py`
Comprehensive diagnostic information about your setup.

**Usage**:
```bash
python utils/diagnosis.py
```

**Provides**:
- Token status
- User information
- Permission details
- Subscription status (if any)

---

### `utils/subscription_review.py`
Review and manage active Graph API subscriptions.

**Usage**:
```bash
python utils/subscription_review.py
```

**Shows**:
- Active subscriptions
- Expiration dates
- Resource endpoints
- Client state

---

### `utils/debug.py`
Advanced debugging tool for troubleshooting API issues.

**Usage**:
```bash
python utils/debug.py
```

**Features**:
- Detailed API request/response logging
- Token inspection
- Subscription testing
- Meeting creation debugging

---

## Workflow Examples

### Standard Workflow
```bash
# 1. First time: Authenticate
python auth.py

# 2. Create meeting
python create_meeting_main.py
# Save the meeting ID!

# 3. After meeting ends (wait 5-15 mins)
python pull_transcript_main.py
# Enter the meeting ID from step 2
```

---

### Advanced Workflow (with webhooks)
```bash
# 1. Authenticate
python auth.py

# 2. Setup webhook subscription
python examples/subscription_manager.py

# 3. Start webhook server
python examples/webhook_handler.py

# 4. Create meetings as usual
python create_meeting_main.py

# Transcripts will be automatically downloaded via webhook!
```

---

### Troubleshooting Workflow
```bash
# Check permissions
python utils/check_permissions.py

# Run diagnostics
python utils/diagnosis.py

# Review subscriptions
python utils/subscription_review.py

# Advanced debugging
python utils/debug.py
```

---

## Common Issues

### "teams_tokens.json not found"
**Solution**: Run `python auth.py` to authenticate first.

### "Failed to refresh token"
**Solution**: Refresh token expired. Run `python auth.py` to re-authenticate.

### "No transcripts found"
**Solution**: Transcripts take 5-15 minutes to process. Wait and try again.

### "Permission denied" or "403 Forbidden"
**Solution**: Check Azure app permissions with `python utils/check_permissions.py`. Ensure admin consent is granted.

---

## Environment Variables

All scripts use environment variables from `.env` in the parent directory:

```
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
TENANT_ID=your-tenant-id
REDIRECT_URI=http://localhost:8000/callback
WEBHOOK_BASE_URL=https://your-ngrok-url.app  # For webhook features
```

See `../env.example` for the template.

---

## Archive

The `archive/` folder contains older experimental code:

- **v2-experiments/**: Version 2 attempts with various approaches
  - `all.py` - Combined auth + meeting creation
  - `save-at.py` - Alternative auth flow
  - `create_meeting.py` - V2 meeting creation

**Note**: Archive code is kept for reference but may not work with current setup.

---

## Tips

1. **Save meeting IDs**: Always save the meeting ID when creating meetings - you'll need it for transcripts
2. **Wait for transcripts**: Transcripts aren't instant - wait 5-15 minutes after meeting ends
3. **Token management**: Tokens auto-refresh, but if you get auth errors, re-run `auth.py`
4. **Use main scripts**: Stick to the `*_main.py` scripts for production use
5. **Experiment safely**: Play with `examples/` and `utils/` scripts to learn more

---
Start with `python auth.py` and follow the quick start guide above.
