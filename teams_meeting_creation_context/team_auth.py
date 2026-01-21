import requests
import base64
import hashlib
import secrets
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI

def generate_pkce():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def get_auth_url(code_challenge):
    """Generate Microsoft authorization URL"""
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite offline_access',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    return f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?" + urlencode(params)

def exchange_code_for_tokens(auth_code, code_verifier):
    """Exchange authorization code for access and refresh tokens"""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'code_verifier': code_verifier
    }
    
    response = requests.post(url, data=data)
    return response.json()

def refresh_access_token(refresh_token):
    """Get new access token using refresh token"""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite',
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(url, data=data)
    return response.json()
