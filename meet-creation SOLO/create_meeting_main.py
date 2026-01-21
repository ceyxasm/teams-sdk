import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def refresh_access_token():
    """Refresh access token using saved refresh token"""
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
            print("Tokens refreshed and saved")
            return new_tokens['access_token']
        else:
            print("Failed to refresh token:", new_tokens)
            return None
            
    except FileNotFoundError:
        print("teams_tokens.json not found. Run the auth script first.")
        return None

def create_teams_meeting(access_token, subject="Test Meeting"):
    """Create Teams meeting with access token"""
    url = "https://graph.microsoft.com/v1.0/me/onlineMeetings"
    
    start_time = datetime.utcnow() + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=1)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "subject": subject,
        "startDateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        "endDateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        "allowTranscription": True, 
        "allowRecording": True,
        "recordAutomatically": True
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.json()

def main():
    access_token = refresh_access_token()
    if not access_token:
        return
    
    subject = input("Enter meeting subject (or press Enter for default): ").strip() or "API Created Meeting"
    status_code, meeting_data = create_teams_meeting(access_token, subject)
    
    if status_code == 201:
        print("Meeting created successfully!")
        print(f"Join URL: {meeting_data.get('joinWebUrl', 'N/A')}")
        print(f"Meeting ID: {meeting_data.get('id', 'N/A')}")
        print(f"Join Meeting ID: {meeting_data.get('joinMeetingIdSettings', {}).get('joinMeetingId', 'N/A')}")
        print("\nNote: Recording and transcription will start automatically when you join the meeting.")
        print("Use the transcript puller script after the meeting to download the transcript.")
    else:
        print(f"Failed to create meeting (Status: {status_code})")
        print(meeting_data)

if __name__ == "__main__":
    main()
