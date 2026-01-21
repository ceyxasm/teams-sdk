import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token():
    """Get fresh access token"""
    try:
        with open('teams_tokens.json', 'r') as f:
            data = json.load(f)
        
        tokens = data['tokens']
        
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/OnlineMeetings.ReadWrite https://graph.microsoft.com/OnlineMeetingTranscript.Read.All offline_access',
            'refresh_token': tokens['refresh_token'],
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=token_data)
        new_tokens = response.json()
        
        if 'access_token' in new_tokens:
            return new_tokens['access_token']
        else:
            print("Failed to refresh token:", new_tokens)
            return None
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def test_meetings_api_different_ways(access_token):
    """Test different ways to access meetings API"""
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Method 1: Try standard meetings endpoint
    print("🧪 Method 1: /me/onlineMeetings")
    try:
        response = requests.get("https://graph.microsoft.com/v1.0/me/onlineMeetings", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.json()}")
        else:
            meetings = response.json()
            print(f"   ✅ Found {len(meetings.get('value', []))} meetings")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Method 2: Try with beta endpoint
    print("\n🧪 Method 2: /beta/me/onlineMeetings")
    try:
        response = requests.get("https://graph.microsoft.com/beta/me/onlineMeetings", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.json()}")
        else:
            meetings = response.json()
            print(f"   ✅ Found {len(meetings.get('value', []))} meetings")
            return meetings.get('value', [])
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Method 3: Try with specific meeting ID from subscription
    print("\n🧪 Method 3: Direct meeting access")
    try:
        # Extract meeting ID from a known subscription
        subs_response = requests.get("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)
        if subs_response.status_code == 200:
            subscriptions = subs_response.json()
            for sub in subscriptions.get('value', []):
                resource = sub.get('resource', '')
                if '/onlineMeetings/' in resource and '/transcripts' in resource:
                    meeting_id = resource.split('/onlineMeetings/')[1].split('/transcripts')[0]
                    print(f"   Testing meeting ID: {meeting_id[:30]}...")
                    
                    # Try to access this specific meeting
                    meeting_response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}", headers=headers)
                    print(f"   Meeting access status: {meeting_response.status_code}")
                    
                    if meeting_response.status_code == 200:
                        meeting = meeting_response.json()
                        print(f"   ✅ Meeting found: {meeting.get('subject', 'No subject')}")
                        
                        # Now try to get transcripts for this meeting
                        transcript_response = requests.get(f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts", headers=headers)
                        print(f"   Transcript access status: {transcript_response.status_code}")
                        
                        if transcript_response.status_code == 200:
                            transcripts = transcript_response.json()
                            transcript_count = len(transcripts.get('value', []))
                            print(f"   📝 Found {transcript_count} transcripts for this meeting")
                            
                            if transcript_count > 0:
                                print("   🎯 TRANSCRIPTS EXIST! This means:")
                                print("      - Meeting had speech and generated transcripts")
                                print("      - But webhook notifications were not sent")
                                print("      - The issue is with the subscription/webhook delivery")
                                
                                for transcript in transcripts.get('value', []):
                                    print(f"      📄 Transcript ID: {transcript.get('id')}")
                                    print(f"         Created: {transcript.get('createdDateTime')}")
                                    print(f"         Content URL: {transcript.get('transcriptContentUrl', 'N/A')}")
                            else:
                                print("   ❌ No transcripts - meeting didn't generate transcripts")
                        else:
                            print(f"   ❌ Transcript access failed: {transcript_response.json()}")
                    else:
                        print(f"   ❌ Meeting access failed: {meeting_response.json()}")
                    
                    break
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return []

def check_scopes_and_permissions(access_token):
    """Check what scopes we actually have"""
    print("\n🔍 Checking actual token scopes...")
    
    # Decode the token (just the payload part for scopes)
    try:
        import base64
        token_parts = access_token.split('.')
        if len(token_parts) >= 2:
            # Add padding if needed
            payload = token_parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            token_data = json.loads(decoded.decode('utf-8'))
            
            scopes = token_data.get('scp', '').split(' ')
            print(f"   Token scopes: {scopes}")
            
            required_scopes = [
                'OnlineMeetings.ReadWrite',
                'OnlineMeetingTranscript.Read.All'
            ]
            
            for scope in required_scopes:
                if any(scope in s for s in scopes):
                    print(f"   ✅ {scope} - Present")
                else:
                    print(f"   ❌ {scope} - Missing!")
            
            return True
    except Exception as e:
        print(f"   ❌ Could not decode token: {e}")
        return False

def main():
    print("🔍 INVESTIGATING MEETINGS API ACCESS ISSUE")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        return
    
    # Check token scopes
    check_scopes_and_permissions(access_token)
    

if __name__ == "__main__":
    main() 