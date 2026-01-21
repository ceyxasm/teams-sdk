import requests
import base64
import hashlib
import secrets
import os
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/plugins/teams/code")

def get_access_token():
    # Generate PKCE parameters
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip('=')
    
    # Generate auth URL
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite offline_access',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': '27112000'
    }
    
    auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urlencode(params)
    print(f"Visit this URL: {auth_url}")
    
    # Wait for user to paste the redirect URL or just the code
    redirect_url = input("\nPaste the full redirect URL you got (or just the authorization code): ").strip()
    
    # Extract code from URL if full URL was pasted
    if redirect_url.startswith('http'):
        parsed = urlparse(redirect_url)
        auth_code = parse_qs(parsed.query)['code'][0]
    else:
        auth_code = redirect_url
    
    # Get access token
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'code_verifier': code_verifier
    }
    
    response = requests.post(token_url, data=data)
    token_response = response.json()
    
    if 'access_token' not in token_response:
        print("Error getting access token:")
        print(token_response)
        return None
    
    return token_response['access_token']

def create_teams_meeting(access_token, subject="Test Meeting"):
    url = "https://graph.microsoft.com/v1.0/me/onlineMeetings"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "subject": subject,
        "startDateTime": "2025-08-20T10:00:00.0000000Z",
        "endDateTime": "2025-08-20T11:00:00.0000000Z",
        "allowTranscription": True,
        "allowRecording": True,
        "recordAutomatically": True
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    return response.json()

def main():
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token")
        return
    
    print(f"\nAccess token obtained successfully")
    
    # Create meeting
    meeting = create_teams_meeting(access_token)
    print("\nMeeting created:")
    print(meeting)

if __name__ == "__main__":
    main()
