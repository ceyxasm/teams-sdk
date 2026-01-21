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

def check_transcript_directly(access_token, meeting_id):
    """Directly check if transcripts exist for a meeting"""
    try:
        url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}/transcripts"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        print(f"\n🔍 Direct transcript check for meeting {meeting_id[:20]}...")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            transcripts = response.json()
            transcript_count = len(transcripts.get('value', []))
            print(f"   📝 Found {transcript_count} transcripts")
            
            if transcript_count > 0:
                print("   🎯 TRANSCRIPTS EXIST - but notifications weren't sent!")
                print("   This indicates a webhook/subscription issue")
                for i, transcript in enumerate(transcripts.get('value', [])):
                    print(f"      Transcript {i+1}: ID={transcript.get('id', 'N/A')}")
                    print(f"                      Created: {transcript.get('createdDateTime', 'N/A')}")
            else:
                print("   ❌ No transcripts found - meeting may not have generated transcripts")
            return transcripts.get('value', [])
        else:
            print(f"   ❌ Failed: {response.json()}")
            return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def simulate_webhook_notification(access_token, meeting_id, transcript_id=None):
    """Test if we can manually trigger a webhook-style notification"""
    try:
        print(f"\n🧪 Testing manual webhook call...")
        
        # Create a test notification payload similar to what Teams would send
        test_payload = {
            "value": [
                {
                    "subscriptionId": "test-subscription-id",
                    "clientState": "test-client-state",
                    "changeType": "created",
                    "resource": f"communications/onlineMeetings/{meeting_id}/transcripts",
                    "subscriptionExpirationDateTime": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
                    "resourceData": {
                        "@odata.type": "#Microsoft.Graph.callTranscript",
                        "@odata.id": f"communications/onlineMeetings/{meeting_id}/transcripts/{transcript_id or 'test-transcript-id'}",
                        "id": transcript_id or "test-transcript-id",
                        "meetingId": meeting_id,
                        "createdDateTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
                        "transcriptContentUrl": f"https://graph.microsoft.com/v1.0/communications/onlineMeetings/{meeting_id}/transcripts/{transcript_id or 'test-transcript-id'}/content",
                        "content": "WEBVTT\\n\\n00:00:00.000 --> 00:00:05.120\\nTest User: This is a test transcript to verify webhook functionality."
                    },
                    "tenantId": "d87b89ce-27bc-4742-9394-b56b2e8ab18e"
                }
            ]
        }
        
        # Send to our webhook
        response = requests.post(
            f"{WEBHOOK_BASE_URL}/teams/webhook",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Manual webhook test successful!")
            print("   📋 Check your webhook server logs for the test notification")
            return True
        else:
            print(f"   ❌ Manual webhook test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Manual webhook test error: {e}")
        return False

def check_ngrok_status():
    """Check if ngrok is properly configured"""
    try:
        print(f"\n🌐 Checking ngrok configuration...")
        
        # Check if ngrok admin API is accessible
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                tunnels = response.json()
                print("   ✅ ngrok is running")
                
                for tunnel in tunnels.get('tunnels', []):
                    if tunnel.get('config', {}).get('addr') == 'localhost:5000':
                        public_url = tunnel.get('public_url', '')
                        if WEBHOOK_BASE_URL.replace('https://', '').replace('http://', '') in public_url:
                            print(f"   ✅ Correct tunnel found: {public_url}")
                        else:
                            print(f"   ⚠️  Tunnel mismatch: Found {public_url}, expected {WEBHOOK_BASE_URL}")
                return True
            else:
                print("   ❌ ngrok admin API not accessible")
                return False
        except:
            print("   ⚠️  Cannot access ngrok admin API (may be normal)")
            return None
    except Exception as e:
        print(f"   ❌ Error checking ngrok: {e}")
        return False

def check_subscription_details_deep(access_token):
    """Deep dive into subscription configuration"""
    try:
        print(f"\n🔬 Deep subscription analysis...")
        
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            subscriptions = response.json()
            
            for sub in subscriptions.get('value', []):
                if 'transcript' in sub.get('resource', '').lower():
                    print(f"\n   📋 Subscription {sub.get('id')[:20]}...")
                    print(f"      Resource: {sub.get('resource')}")
                    print(f"      Change Type: {sub.get('changeType')}")
                    print(f"      Notification URL: {sub.get('notificationUrl')}")
                    print(f"      Client State: {sub.get('clientState')}")
                    print(f"      Expires: {sub.get('expirationDateTime')}")
                    print(f"      Creator ID: {sub.get('creatorId')}")
                    print(f"      Application ID: {sub.get('applicationId')}")
                    print(f"      Latest TLS Version: {sub.get('latestSupportedTlsVersion')}")
                    
                    # Check if subscription is about to expire
                    exp_time = datetime.fromisoformat(sub.get('expirationDateTime', '').replace('Z', '+00:00'))
                    time_left = exp_time - datetime.now().replace(tzinfo=exp_time.tzinfo)
                    
                    if time_left.total_seconds() < 3600:  # Less than 1 hour
                        print(f"      ⚠️  WARNING: Subscription expires in {time_left}")
                    else:
                        print(f"      ✅ Time until expiry: {time_left}")
            
            return True
        else:
            print(f"   ❌ Failed to get subscriptions: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error in deep analysis: {e}")
        return False

def check_tenant_transcript_policy(access_token):
    """Check if tenant has transcript policies that might block notifications"""
    try:
        print(f"\n🏢 Checking tenant transcript policies...")
        
        # Try to get organization settings that might affect transcripts
        url = "https://graph.microsoft.com/v1.0/organization"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            org_data = response.json()
            print("   ✅ Organization data accessible")
            
            # Look for any privacy or compliance settings
            for org in org_data.get('value', []):
                privacy_profile = org.get('privacyProfile', {})
                if privacy_profile:
                    print(f"      Privacy Contact: {privacy_profile.get('contactEmail', 'Not set')}")
                    print(f"      Privacy Statement: {privacy_profile.get('statementUrl', 'Not set')}")
                
        else:
            print(f"   ⚠️  Cannot access organization settings: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error checking tenant policies: {e}")
        return False

def main():
    print("🔍 ADVANCED TEAMS TRANSCRIPT DEBUGGING")
    print("=" * 70)
    
    # Get access token
    print("\n1. Getting access token...")
    access_token = get_access_token()
    if not access_token:
        print("❌ Cannot proceed without access token")
        return
    print("✅ Access token obtained")
    
    # Check ngrok status
    check_ngrok_status()
    
    # Deep subscription analysis
    check_subscription_details_deep(access_token)
    
    # Check tenant policies
    check_tenant_transcript_policy(access_token)
    
    # Get recent meetings and check for transcripts
    print(f"\n🔍 Checking recent meetings for transcripts...")
    try:
        url = "https://graph.microsoft.com/v1.0/me/onlineMeetings"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            meetings = response.json()
            recent_meetings = meetings.get('value', [])[:5]  # Check last 5 meetings
            
            print(f"   Found {len(recent_meetings)} recent meetings")
            
            for i, meeting in enumerate(recent_meetings):
                meeting_id = meeting.get('id')
                subject = meeting.get('subject', 'No subject')
                created = meeting.get('creationDateTime', 'Unknown')
                
                print(f"\n   📅 Meeting {i+1}: {subject}")
                print(f"      ID: {meeting_id[:30]}...")
                print(f"      Created: {created}")
                print(f"      Transcription Allowed: {meeting.get('allowTranscription', 'Not set')}")
                
                # Check for transcripts
                transcripts = check_transcript_directly(access_token, meeting_id)
                
                # If transcripts exist, test manual webhook
                if transcripts:
                    transcript_id = transcripts[0].get('id')
                    # simulate_webhook_notification(access_token, meeting_id, transcript_id)
        else:
            print(f"   ❌ Failed to get meetings: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error checking meetings: {e}")
    
    # Final test - simulate webhook
    print(f"\n🧪 Testing webhook with synthetic data...")
    simulate_webhook_notification(access_token, "test-meeting-id")
    
    print("\n" + "=" * 70)
    print("🔍 ADVANCED DEBUGGING COMPLETE")
    print("\n💡 If transcripts exist but notifications aren't received:")
    print("   1. Check webhook server logs during the synthetic test")
    print("   2. Verify ngrok is exposing the correct port")
    print("   3. Check if there are firewall/network issues")
    print("   4. Try recreating the subscription")
    print("\n⚠️  If no transcripts exist for meetings with speech:")
    print("   1. Ensure you spoke clearly for 30+ seconds")
    print("   2. Check if your tenant allows transcription")
    print("   3. Verify meeting settings allow transcription")
    print("   4. Try with multiple participants")

if __name__ == "__main__":
    main() 