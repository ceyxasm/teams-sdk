import requests
import json
import os
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://your-webhook-url.ngrok-free.app")

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

def check_all_recent_meetings_for_transcripts(access_token):
    """Check all recent meetings for new transcripts"""
    try:
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print("🔍 CHECKING ALL RECENT MEETINGS FOR NEW TRANSCRIPTS")
        print("=" * 65)
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            subscriptions = response.json()
            
            meeting_ids = set()
            for sub in subscriptions.get('value', []):
                resource = sub.get('resource', '') or ''
                if '/onlineMeetings/' in resource and '/transcripts' in resource:
                    meeting_id = resource.split('/onlineMeetings/')[1].split('/transcripts')[0]
                    meeting_ids.add(meeting_id)
                    print(f"📋 Found meeting subscription: {meeting_id[:30]}...")
            
            print(f"\n🎯 Checking {len(meeting_ids)} meetings for transcripts...")
            
            for i, meeting_id in enumerate(meeting_ids):
                print(f"\n📅 Meeting {i+1}: {meeting_id[:30]}...")
                
                # Get meeting details
                meeting_url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}"
                meeting_response = requests.get(meeting_url, headers=headers)
                
                if meeting_response.status_code == 200:
                    meeting = meeting_response.json()
                    subject = meeting.get('subject', 'No Subject')
                    start_time = meeting.get('startDateTime', 'Unknown')
                    print(f"   Subject: {subject}")
                    print(f"   Start Time: {start_time}")
                    
                    # Check for transcripts
                    transcript_url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts"
                    transcript_response = requests.get(transcript_url, headers=headers)
                    
                    if transcript_response.status_code == 200:
                        transcripts = transcript_response.json()
                        transcript_count = len(transcripts.get('value', []))
                        print(f"   📝 Transcripts: {transcript_count}")
                        
                        if transcript_count > 0:
                            for j, transcript in enumerate(transcripts.get('value', [])):
                                created_time = transcript.get('createdDateTime', 'Unknown')
                                print(f"      Transcript {j+1}: Created {created_time}")
                                
                                # Check if this is very recent (last 30 minutes)
                                try:
                                    created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                                    now = datetime.now(created_dt.tzinfo)
                                    age = now - created_dt
                                    
                                    if age.total_seconds() < 1800:  # Less than 30 minutes
                                        print(f"         🚨 RECENT TRANSCRIPT! Age: {age}")
                                        print(f"         🔔 This should have triggered a notification!")
                                except:
                                    pass
                    else:
                        print(f"   ❌ Failed to get transcripts: {transcript_response.status_code}")
                else:
                    print(f"   ❌ Failed to get meeting: {meeting_response.status_code}")
            
            return True
        else:
            print(f"❌ Failed to get subscriptions: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking meetings: {e}")
        return False

def main():
    print("🔍 FINAL COMPREHENSIVE DIAGNOSIS")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        return
    
    # Check all recent meetings
    check_all_recent_meetings_for_transcripts(access_token)
    
    # Test webhook one more time
    # test_webhook_with_realistic_payload(access_token)
    
    # Create polling solution
    # create_polling_solution(access_token)
    
    # Final recommendations
    # final_recommendations()

if __name__ == "__main__":
    main() 