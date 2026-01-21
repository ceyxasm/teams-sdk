import requests
import json
import os
from datetime import datetime
import urllib.parse
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

def get_meeting_transcripts(access_token, meeting_id):
    """Get all transcripts for a specific meeting"""
    # URL encode the meeting ID to handle special characters
    encoded_meeting_id = urllib.parse.quote(meeting_id, safe='')
    url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{encoded_meeting_id}/transcripts"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        transcripts = response.json()
        return transcripts.get('value', [])
    else:
        print(f"Failed to get transcripts (Status: {response.status_code})")
        print(response.json())
        return []

def download_transcript_content(access_token, meeting_id, transcript_id):
    """Download the actual transcript content"""
    # URL encode both IDs
    encoded_meeting_id = urllib.parse.quote(meeting_id, safe='')
    encoded_transcript_id = urllib.parse.quote(transcript_id, safe='')
    url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{encoded_meeting_id}/transcripts/{encoded_transcript_id}/content?$format=text/vtt"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'text/vtt'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to download transcript content (Status: {response.status_code})")
        return None

def save_transcript_to_file(transcript_content, meeting_id, transcript_id):
    """Save transcript content to a file"""
    if not os.path.exists('transcripts'):
        os.makedirs('transcripts')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcripts/transcript_{meeting_id[:8]}_{transcript_id[:8]}_{timestamp}.vtt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(transcript_content)
        print(f"Transcript saved to: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return None

def main():
    access_token = refresh_access_token()
    if not access_token:
        return
    
    meeting_id = input("Enter the Meeting ID (from when you created the meeting): ").strip()
    
    if not meeting_id:
        print("Meeting ID is required!")
        return
    
    print(f"Fetching transcripts for meeting: {meeting_id}")
    transcripts = get_meeting_transcripts(access_token, meeting_id)
    
    if not transcripts:
        print("No transcripts found for this meeting.")
        print("Note: Transcripts may take a few minutes to be available after the meeting ends.")
        return
    
    print(f"Found {len(transcripts)} transcript(s)")
    
    for i, transcript in enumerate(transcripts, 1):
        transcript_id = transcript.get('id')
        created_time = transcript.get('createdDateTime', 'Unknown')
        
        print(f"\nTranscript {i}:")
        print(f"  ID: {transcript_id}")
        print(f"  Created: {created_time}")
        
        # Download transcript content
        print("  Downloading content...")
        content = download_transcript_content(access_token, meeting_id, transcript_id)
        
        if content:
            filename = save_transcript_to_file(content, meeting_id, transcript_id)
            if filename:
                print(f"  ✅ Successfully saved to {filename}")
            else:
                print("  ❌ Failed to save transcript")
        else:
            print("  ❌ Failed to download transcript content")
    
    print("\nTranscript pulling complete!")

if __name__ == "__main__":
    main() 