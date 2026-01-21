import requests
import base64
import hashlib
import secrets
import json
import os
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/plugins/teams/code")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://your-webhook-url.ngrok-free.app")

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

def create_transcript_subscription(access_token, user_id):
    """Create subscription for user's meeting transcripts"""
    try:
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        
        # Subscription expires in 3 days for transcript subscriptions
        expiration_time = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "changeType": "created",
            "notificationUrl": f"{WEBHOOK_BASE_URL}/teams/webhook",
            "lifecycleNotificationUrl": f"{WEBHOOK_BASE_URL}/teams/lifecycle",
            "resource": f"users/{user_id}/onlineMeetings/getAllTranscripts",
            "expirationDateTime": expiration_time,
            "clientState": f"transcript-webhook-{user_id}"
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            subscription_data = response.json()
            print("SUCCESS: Transcript subscription created!")
            print(f"Subscription ID: {subscription_data.get('id')}")
            print(f"Expires: {subscription_data.get('expirationDateTime')}")
            return subscription_data
        else:
            print(f"FAILED: Failed to create subscription (Status: {response.status_code})")
            print(response.json())
            return None
            
    except Exception as e:
        print(f"Error creating subscription: {e}")
        return None

def main():
    # Generate PKCE parameters
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip('=')
    
    # Generate auth URL with updated scope
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/OnlineMeetingTranscript.Read.All offline_access',
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
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/OnlineMeetingTranscript.Read.All',
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
    
    # Get user information
    user_id, display_name, email = get_user_info(access_token)
    if not user_id:
        print("Failed to get user information")
        return
    
    print(f"\nUser authenticated: {display_name} ({email})")
    print(f"User ID: {user_id}")
    
    # Create transcript subscription
    print("\nCreating transcript subscription...")
    subscription_data = create_transcript_subscription(access_token, user_id)
    
    # Save everything to JSON file
    complete_data = {
        'tokens': token_response,
        'user_info': {
            'id': user_id,
            'displayName': display_name,
            'email': email
        },
        'subscription': subscription_data,
        'created_at': datetime.utcnow().isoformat()
    }
    
    with open('teams_tokens.json', 'w') as f:
        json.dump(complete_data, f, indent=2)
    print("\nComplete installation data saved to teams_tokens.json")
    
    print("\n" + "="*50)
    print("APP INSTALLATION COMPLETE!")
    print(f"User: {display_name}")
    print(f"Subscription ID: {subscription_data.get('id') if subscription_data else 'FAILED'}")
    print("Make sure your webhook server is running to receive notifications!")
    print("="*50)
    
    return complete_data

if __name__ == "__main__":
    main()
