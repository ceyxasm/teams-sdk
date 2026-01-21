import requests

def create_teams_meeting(access_token, subject="Test Meeting", start_time="2025-08-20T10:00:00.0000000Z", end_time="2025-08-20T11:00:00.0000000Z"):
    """Create Teams meeting using access token"""
    url = "https://graph.microsoft.com/v1.0/me/onlineMeetings"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "subject": subject,
        "startDateTime": start_time,
        "endDateTime": end_time
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.json()

def extract_meeting_details(meeting_response):
    """Extract useful meeting details from API response"""
    if 'joinWebUrl' not in meeting_response:
        return None
    
    return {
        'join_url': meeting_response['joinWebUrl'],
        'meeting_id': meeting_response['joinMeetingIdSettings']['joinMeetingId'],
        'passcode': meeting_response['joinMeetingIdSettings']['passcode'],
        'subject': meeting_response['subject'],
        'start_time': meeting_response['startDateTime'],
        'end_time': meeting_response['endDateTime']
    }
