"""
Example of the 3-step flow using the abstracted functions
Based on your original scripts
"""

from teams_auth import generate_pkce, get_auth_url, exchange_code_for_tokens
from teams_api import create_teams_meeting, extract_meeting_details

# Step 1: Generate auth URL (like your first script)
def step1_get_auth_url():
    code_verifier, code_challenge = generate_pkce()
    auth_url = get_auth_url(code_challenge)
    return code_verifier, auth_url

# Step 2: Exchange code for tokens (like your second script)  
def step2_exchange_code(auth_code, code_verifier):
    token_response = exchange_code_for_tokens(auth_code, code_verifier)
    return token_response

# Step 3: Create meeting (like your third script)
def step3_create_meeting(access_token, subject="Test Meeting"):
    status_code, meeting_response = create_teams_meeting(access_token, subject)
    if status_code == 201:
        return extract_meeting_details(meeting_response)
    return None

# Example usage (your original flow)
if __name__ == "__main__":
    # Step 1: Get auth URL
    code_verifier, auth_url = step1_get_auth_url()
    print(f"Code verifier: {code_verifier}")
    print(f"Visit this URL: {auth_url}")
    
    # Step 2: Exchange code (you'd get this from callback)
    # auth_code = "your_auth_code_from_callback"
    # token_response = step2_exchange_code(auth_code, code_verifier)
    # access_token = token_response['access_token']
    
    # Step 3: Create meeting
    # meeting = step3_create_meeting(access_token)
    # print(meeting)
