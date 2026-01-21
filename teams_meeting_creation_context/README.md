# Teams Meeting Integration

Clean abstractions for creating Microsoft Teams meetings via API.

## What This Contains

- `teams_auth.py` - OAuth2/PKCE authentication functions
- `teams_api.py` - Teams meeting creation functions  
- `config.py` - Microsoft app credentials
- `example_flow.py` - Shows how the 3 steps work together

## The 3-Step Flow

### 1. Get Authorization URL
```python
from teams_auth import generate_pkce, get_auth_url

code_verifier, code_challenge = generate_pkce()
auth_url = get_auth_url(code_challenge)
# User visits auth_url, signs in, gets redirected with auth_code
```

### 2. Exchange Code for Tokens
```python
from teams_auth import exchange_code_for_tokens

token_response = exchange_code_for_tokens(auth_code, code_verifier)
access_token = token_response['access_token']
refresh_token = token_response['refresh_token']
```

### 3. Create Meeting
```python
from teams_api import create_teams_meeting, extract_meeting_details

status_code, response = create_teams_meeting(access_token, "My Meeting")
if status_code == 201:
    meeting = extract_meeting_details(response)
    # meeting contains: join_url, meeting_id, passcode, etc.
```

## What You Need To Store

**Per user in your database:**
```
refresh_token (string) - Long-lived token for getting new access tokens
```

**For meeting creation:**
```
access_token (string) - Short-lived token (1 hour) for API calls
```

## Integration Into Your Backend

### One-Time Setup (per user)
1. Generate auth URL when user wants to connect Microsoft account
2. User visits URL, signs in, gets redirected to your callback
3. Extract auth_code from callback URL
4. Exchange auth_code for tokens
5. Store refresh_token in your user database

### Every Meeting Creation
1. Get user's refresh_token from database
2. Use refresh_token to get fresh access_token
3. Create meeting with access_token
4. Return meeting details to frontend

## Core Functions You'll Use

```python
# Authentication
generate_pkce() -> (code_verifier, code_challenge)
get_auth_url(code_challenge) -> auth_url  
exchange_code_for_tokens(auth_code, code_verifier) -> tokens
refresh_access_token(refresh_token) -> new_tokens

# Meeting Creation  
create_teams_meeting(access_token, subject, start_time, end_time) -> (status, response)
extract_meeting_details(response) -> clean_meeting_object
```

## Token Lifecycle

- **Access Token**: Expires in 1 hour, used for API calls
- **Refresh Token**: Lasts months, used to get new access tokens
- **Code Verifier**: Single-use, generated per auth session

## Error Handling

```python
# Common scenarios:
if 'access_token' not in token_response:
    # Token exchange failed
    
if status_code == 401:
    # Access token expired, refresh it
    
if status_code == 403: 
    # User lacks permissions
    
if 'refresh_token' expired:
    # User needs to re-authenticate
```

## Security Notes

- Store refresh_tokens encrypted
- Never expose refresh_tokens to frontend  
- Access tokens expire automatically
- Use HTTPS for all requests

## Dependencies

```
requests>=2.31.0
```

## Framework Agnostic

These functions work with any Python backend:
- Django/Flask/FastAPI for web apps
- Lambda functions for serverless
- Background workers for batch processing
- CLI tools for testing

No assumptions made about your database, authentication, or API structure.
