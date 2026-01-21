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

def get_fresh_meeting_id_from_subscriptions(access_token):
    """Find the meeting ID from our fresh subscription"""
    try:
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            subscriptions = response.json()
            
            print(f"📋 Found {len(subscriptions.get('value', []))} total subscriptions")
            
            for sub in subscriptions.get('value', []):
                client_state = sub.get('clientState', '') or ''  # Handle None
                resource = sub.get('resource', '') or ''  # Handle None
                
                print(f"   Subscription: {sub.get('id')}")
                print(f"      Client State: {client_state}")
                print(f"      Resource: {resource[:80]}...")
                
                # Look for our fresh meeting subscription
                if 'fresh-meeting' in client_state and '/onlineMeetings/' in resource:
                    meeting_id = resource.split('/onlineMeetings/')[1].split('/transcripts')[0]
                    print(f"🎯 Found fresh meeting ID: {meeting_id[:30]}...")
                    print(f"   Subscription ID: {sub.get('id')}")
                    print(f"   Client State: {client_state}")
                    return meeting_id
                
                # Also check for any transcript subscriptions and extract meeting IDs
                if '/onlineMeetings/' in resource and '/transcripts' in resource:
                    meeting_id = resource.split('/onlineMeetings/')[1].split('/transcripts')[0]
                    print(f"   📝 Contains meeting ID: {meeting_id[:30]}...")
                    # Return the most recent one if we don't find a fresh-meeting one
                    if not any('fresh-meeting' in s.get('clientState', '') or '' for s in subscriptions.get('value', [])):
                        return meeting_id
            
            print("❌ No fresh meeting subscription found, will check latest meeting")
            return None
        else:
            print(f"❌ Failed to get subscriptions: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error finding fresh meeting: {e}")
        return None

def get_latest_meeting_id(access_token):
    """Get the most recent meeting ID as fallback"""
    try:
        # Try to get meetings from subscriptions first
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            subscriptions = response.json()
            
            # Get all meeting IDs from transcript subscriptions
            meeting_ids = []
            for sub in subscriptions.get('value', []):
                resource = sub.get('resource', '') or ''
                if '/onlineMeetings/' in resource and '/transcripts' in resource:
                    meeting_id = resource.split('/onlineMeetings/')[1].split('/transcripts')[0]
                    created_time = sub.get('expirationDateTime', '')
                    meeting_ids.append((meeting_id, created_time))
            
            if meeting_ids:
                # Sort by creation time and get the most recent
                meeting_ids.sort(key=lambda x: x[1], reverse=True)
                latest_meeting_id = meeting_ids[0][0]
                print(f"🎯 Using latest meeting ID: {latest_meeting_id[:30]}...")
                return latest_meeting_id
        
        print("❌ Could not find any meeting IDs")
        return None
    except Exception as e:
        print(f"❌ Error getting latest meeting: {e}")
        return None

def check_meeting_details(access_token, meeting_id):
    """Get detailed meeting information"""
    try:
        url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            meeting = response.json()
            
            print(f"\n📅 MEETING DETAILS:")
            print(f"   Subject: {meeting.get('subject')}")
            print(f"   Start Time: {meeting.get('startDateTime')}")
            print(f"   End Time: {meeting.get('endDateTime')}")
            print(f"   Join URL: {meeting.get('joinWebUrl', 'N/A')[:60]}...")
            # print(f"   Allow Transcription: {meeting.get('allowTranscription')}")
            # print(f"   Allow Recording: {meeting.get('allowRecording')}")
            # print(f"   Record Automatically: {meeting.get('recordAutomatically')}")
            
            # Check if meeting has participants info
            # participants = meeting.get('participants', {})
            # if participants:
            #     print(f"   Participants Info: {json.dumps(participants, indent=4)}")
            
            return meeting
        else:
            print(f"❌ Failed to get meeting details: {response.status_code}")
            print(f"   Error: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Error getting meeting details: {e}")
        return None

def check_meeting_transcripts(access_token, meeting_id):
    """Check for transcripts and get their details"""
    try:
        url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        print(f"\n📝 TRANSCRIPT CHECK:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            transcripts = response.json()
            transcript_list = transcripts.get('value', [])
            
            print(f"   📊 Found {len(transcript_list)} transcripts")
            
            if len(transcript_list) == 0:
                print("   ❌ No transcripts found - this explains why no notifications were sent!")
                print("   💡 Possible reasons:")
                print("      - Meeting didn't have enough speech (need 30+ seconds)")
                print("      - Meeting wasn't properly ended")
                print("      - Transcription service didn't process the audio")
                print("      - Meeting is too recent (transcripts can take 5-15 minutes)")
                return []
            
            # Process each transcript
            for i, transcript in enumerate(transcript_list):
                print(f"\n   📄 Transcript {i+1}:")
                print(f"      ID: {transcript.get('id')}")
                print(f"      Created: {transcript.get('createdDateTime')}")
                print(f"      Meeting ID: {transcript.get('meetingId')}")
                
                # Try to get the actual transcript content
                content_url = transcript.get('transcriptContentUrl')
                if content_url:
                    print(f"      Content URL: {content_url[:80]}...")
                    content = get_transcript_content(access_token, meeting_id, transcript.get('id'))
                    if content:
                        print(f"      📋 CONTENT PREVIEW:")
                        preview = content[:300] + "..." if len(content) > 300 else content
                        print(f"         {preview}")
                else:
                    print(f"      ❌ No content URL available")
            
            return transcript_list
        else:
            print(f"   ❌ Failed to get transcripts: {response.status_code}")
            print(f"   Error: {response.json()}")
            return []
    except Exception as e:
        print(f"   ❌ Error checking transcripts: {e}")
        return []

def get_transcript_content(access_token, meeting_id, transcript_id):
    """Fetch the actual transcript content"""
    try:
        url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'text/vtt'  # WebVTT format
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"         ❌ Failed to get content: {response.status_code}")
            return None
    except Exception as e:
        print(f"         ❌ Error getting content: {e}")
        return None

def check_subscription_status(access_token):
    """Check the status of our fresh subscriptions"""
    try:
        # breakpoint()
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            subscriptions = response.json()
            
            print(f"\n🔔 SUBSCRIPTION STATUS:")
            for sub in subscriptions.get('value', []):
                client_state = sub.get('clientState', '')
                # if 'fresh-meeting' in client_state or 'global-transcript' in client_state:
                print(f"   📋 {client_state}:")
                print(f"      ID: {sub.get('id')}")
                print(f"      Resource: {sub.get('resource')}")
                # print(f"      Webhook: {sub.get('notificationUrl')}")
                # print(f"      Expires: {sub.get('expirationDateTime')}")
                
                # Check time until expiry
                exp_time = datetime.fromisoformat(sub.get('expirationDateTime', '').replace('Z', '+00:00'))
                time_left = exp_time - datetime.now().replace(tzinfo=exp_time.tzinfo)
                print(f"      Time left: {time_left}\n\n")
            
            return True
        else:
            print(f"❌ Failed to get subscription status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking subscription status: {e}")
        return False

def main():
    print("🔍 CHECKING FRESH MEETING AND TRANSCRIPTS")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        return
    
    # Find our fresh meeting ID
    print("\n1. Finding fresh meeting ID...")
    # meeting_id = get_fresh_meeting_id_from_subscriptions(access_token)
    meeting_id = get_latest_meeting_id(access_token)

    # if not meeting_id:
    #     print("🔄 Trying to find latest meeting as fallback...")
    #     meeting_id = get_latest_meeting_id(access_token)
    
    if not meeting_id:
        print("❌ Could not find any meeting ID")
        return
    
    # Check meeting details
    print(f"\n2. Checking meeting details...")
    meeting = check_meeting_details(access_token, meeting_id)
    
    # Check for transcripts
    print(f"\n3. Checking for transcripts...")
    transcripts = check_meeting_transcripts(access_token, meeting_id)
    
    # Check subscription status
    print(f"\n4. Checking subscription status...")
    check_subscription_status(access_token)
    
    # Summary and next steps
    print(f"\n" + "=" * 60)
    print(f"🔍 ANALYSIS SUMMARY:")
    
    if transcripts:
        print(f"   ✅ Meeting has {len(transcripts)} transcript(s)")
        print(f"   🎯 TRANSCRIPTS EXIST but NO NOTIFICATIONS RECEIVED")
        print(f"   🔧 This confirms the webhook delivery issue")
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. The subscriptions are correctly configured")
        print(f"   2. Transcripts are being generated")
        print(f"   3. But Microsoft Graph is not sending notifications")
        print(f"   4. This might be a temporary Microsoft Graph issue")
        print(f"   5. Try creating another meeting and test again")
    else:
        print(f"   ❌ No transcripts found for this meeting")
        print(f"   💡 POSSIBLE REASONS:")
        print(f"   1. Meeting didn't have enough clear speech (need 30+ seconds)")
        print(f"   2. Meeting is too recent (transcripts take time to process)")
        print(f"   3. Transcription service didn't process the audio")
        print(f"   4. Meeting wasn't properly joined/ended")
        print(f"\n🧪 RECOMMENDED TEST:")
        print(f"   1. Join the meeting again")
        print(f"   2. Speak clearly for 60+ seconds")
        print(f"   3. End meeting properly")
        print(f"   4. Wait 10-15 minutes")
        print(f"   5. Run this script again")

if __name__ == "__main__":
    main() 