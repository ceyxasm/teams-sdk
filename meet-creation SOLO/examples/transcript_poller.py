#!/usr/bin/env python3
import requests
import json
import time
import os
from datetime import datetime, timedelta
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
            data['tokens'] = new_tokens
            with open('teams_tokens.json', 'w') as f:
                json.dump(data, f, indent=2)
            return new_tokens['access_token']
        else:
            print("Failed to refresh token:", new_tokens)
            return None
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def get_meetings_with_subscriptions(access_token):
    """Get meeting IDs from active subscriptions"""
    try:
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            subscriptions = response.json()
            
            meeting_ids = []
            for sub in subscriptions.get('value', []):
                resource = sub.get('resource', '')
                if '/transcripts' in resource and '/onlineMeetings/' in resource:
                    try:
                        meeting_id = resource.split('/onlineMeetings/')[1].split('/transcripts')[0]
                        meeting_ids.append({
                            'meeting_id': meeting_id,
                            'subscription_id': sub.get('id'),
                            'client_state': sub.get('clientState', 'Unknown')
                        })
                    except:
                        continue
            
            return meeting_ids
        else:
            print(f"Failed to get subscriptions: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting subscriptions: {e}")
        return []

def check_meeting_transcripts(access_token, meeting_info, last_check_time):
    """Check a specific meeting for new transcripts"""
    try:
        meeting_id = meeting_info['meeting_id']
        url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            transcripts = response.json()
            new_transcripts = []
            
            for transcript in transcripts.get('value', []):
                created_time_str = transcript.get('createdDateTime')
                if created_time_str:
                    try:
                        created_time = datetime.fromisoformat(created_time_str.replace('Z', '+00:00'))
                        # Remove timezone info for comparison
                        created_time = created_time.replace(tzinfo=None)
                        
                        if created_time > last_check_time:
                            new_transcripts.append(transcript)
                    except:
                        # If we can't parse time, include it to be safe
                        new_transcripts.append(transcript)
            
            return new_transcripts
        else:
            if response.status_code != 404:  # 404 is normal for meetings without transcripts
                print(f"Error checking meeting {meeting_id[:30]}...: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error checking transcripts for meeting: {e}")
        return []

def process_new_transcript(meeting_info, transcript):
    """Process a newly found transcript (simulate notification)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "🎉" * 20 + " NEW TRANSCRIPT FOUND! " + "🎉" * 20)
    print(f"⏰ FOUND AT: {timestamp}")
    print(f"📅 Meeting: {meeting_info['meeting_id'][:30]}...")
    print(f"📝 Transcript ID: {transcript.get('id')}")
    print(f"🕐 Created: {transcript.get('createdDateTime')}")
    print(f"🎯 Subscription: {meeting_info['client_state']}")
    print("🎉" * 70)
    
    # Save to file (like webhook would)
    notification_data = {
        'timestamp': timestamp,
        'type': 'POLLED_TRANSCRIPT_FOUND',
        'source': 'Transcript Poller (not webhook)',
        'meeting_id': meeting_info['meeting_id'],
        'subscription_id': meeting_info['subscription_id'],
        'transcript_data': transcript
    }
    
    with open('transcript_notifications.json', 'a') as f:
        json.dump(notification_data, f, indent=2)
        f.write('\n')
    
    print(f"💾 Saved to transcript_notifications.json")

def main():
    print("🔄 TRANSCRIPT POLLER - WEBHOOK ALTERNATIVE")
    print("=" * 60)
    print("Since Microsoft Graph webhook notifications aren't working,")
    print("this script polls for new transcripts every 2 minutes.")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        return
    
    # Get meetings to monitor
    meetings = get_meetings_with_subscriptions(access_token)
    
    if not meetings:
        print("❌ No meetings with transcript subscriptions found")
        return
    
    print(f"📋 Monitoring {len(meetings)} meetings for new transcripts:")
    for meeting in meetings:
        print(f"   📅 {meeting['meeting_id'][:30]}... ({meeting['client_state']})")
    
    print(f"\n🔄 Starting polling every 2 minutes...")
    print(f"💡 This will catch transcripts that webhooks miss!")
    
    last_check = datetime.utcnow() - timedelta(hours=1)  # Check last hour initially
    
    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Checking for new transcripts...")
            
            # Refresh token periodically
            if datetime.now().minute % 30 == 0:  # Every 30 minutes
                access_token = get_access_token()
                if not access_token:
                    print("❌ Failed to refresh token, stopping")
                    break
            
            current_check = datetime.utcnow()
            found_new = False
            
            for meeting in meetings:
                new_transcripts = check_meeting_transcripts(access_token, meeting, last_check)
                
                for transcript in new_transcripts:
                    process_new_transcript(meeting, transcript)
                    found_new = True
            
            if not found_new:
                print("   📭 No new transcripts found")
            
            last_check = current_check
            
            print(f"   😴 Sleeping 2 minutes until next check...")
            time.sleep(120)  # 2 minutes
            
    except KeyboardInterrupt:
        print(f"\n🛑 Transcript poller stopped by user")
    except Exception as e:
        print(f"\n❌ Poller error: {e}")

if __name__ == "__main__":
    main()
