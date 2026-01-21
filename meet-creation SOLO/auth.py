import requests
import base64
import hashlib
import secrets
import json
import os
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/OnlineMeetingTranscript.Read.All offline_access',

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/plugins/teams/code")

def get_user_info(access_token):
    """Get user information using access token"""
    try:
        user_response = requests.get('https://graph.microsoft.com/v1.0/me', 
                                   headers={'Authorization': f'Bearer {access_token}'})
        if user_response.status_code == 200:
            user_data = user_response.json()
            return user_data['id'], user_data.get('displayName', 'Unknown'), user_data.get('mail', 'Unknown')
        else:
            print(f"Failed to get user info: {user_response.status_code}")
            return None, None, None
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None, None, None

def main():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip('=')
    
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'OnlineMeetings.ReadWrite User.Read',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': '27112000'
    }
    
    auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urlencode(params)
    print(f"Visit this URL: {auth_url}")
    
    redirect_url = input("\nPaste the full redirect URL you got (or just the authorization code): ").strip()
    
    if redirect_url.startswith('http'):
        parsed = urlparse(redirect_url)
        auth_code = parse_qs(parsed.query)['code'][0]
    else:
        auth_code = redirect_url
    
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'OnlineMeetings.ReadWrite User.Read',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'code_verifier': code_verifier
    }
    
    response = requests.post(token_url, data=data)
    token_response = response.json()
    
    if 'access_token' not in token_response:
        print("\nError getting tokens:")
        print(token_response)
        return token_response
    
    access_token = token_response['access_token']
    user_id, display_name, email = get_user_info(access_token)
    
    if not user_id:
        print("Failed to get user information")
        return
    
    print(f"\nUser authenticated: {display_name} ({email})")
    print(f"User ID: {user_id}")
    
    complete_data = {
        'tokens': token_response,
        'user_info': {
            'id': user_id,
            'displayName': display_name,
            'email': email
        },
        'created_at': datetime.utcnow().isoformat()
    }
    
    with open('teams_tokens.json', 'w') as f:
        json.dump(complete_data, f, indent=2)
    print("\nTokens and user info saved to teams_tokens.json")
    
    print("\n" + "="*50)
    print("APP INSTALLATION COMPLETE!")
    print(f"User: {display_name}")
    print("Ready to create meetings with transcript subscriptions!")
    print("="*50)
    
    return complete_data

if __name__ == "__main__":
    main()
