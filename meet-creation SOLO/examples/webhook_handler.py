from flask import Flask, request, jsonify
import json
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_fresh_access_token():
    """Get fresh access token for renewal operations"""
    try:
        with open('teams_tokens.json', 'r') as f:
            data = json.load(f)
        
        # Access tokens from the nested structure
        tokens = data['tokens']
        
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/CallRecords.Read.All https://graph.microsoft.com/OnlineMeetings.ReadWrite',
            'refresh_token': tokens['refresh_token'],
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=token_data)
        new_tokens = response.json()
        
        if 'access_token' in new_tokens:
            # Update only the tokens section, preserve user_info and subscription
            data['tokens'] = new_tokens
            with open('teams_tokens.json', 'w') as f:
                json.dump(data, f, indent=2)
            return new_tokens['access_token']
        else:
            print("Failed to refresh token:", new_tokens)
            return None
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None

def renew_subscription(subscription_id, access_token):
    """Renew a subscription by extending its expiration time"""
    try:
        url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
        
        # Extend by 3 days for transcript subscriptions
        new_expiration = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "expirationDateTime": new_expiration
        }
        
        response = requests.patch(url, json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"SUCCESS: Subscription {subscription_id} renewed successfully")
            return True
        else:
            print(f"FAILED: Failed to renew subscription {subscription_id}: {response.status_code}")
            print(response.json())
            return False
            
    except Exception as e:
        print(f"Error renewing subscription: {e}")
        return False

@app.route('/teams/webhook', methods=['GET', 'POST'])
def transcript_webhook():
    """Handle transcript notifications"""

    # Log ALL incoming requests
    print(f"WEBHOOK HIT: {request.method} {request.url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Args: {dict(request.args)}")
    
    # Check for validation token first (works for both GET and POST)
    validation_token = request.args.get('validationToken')
    if validation_token:
        print(f"VALIDATION: Transcript webhook validation: {validation_token}")
        return validation_token, 200, {'Content-Type': 'text/plain'}
    
    if request.method == 'POST':
        # how to verify that teams sent the request?
        try:
            notification_data = request.get_json()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print("\n" + "🔔" * 20 + " REAL TRANSCRIPT NOTIFICATION " + "🔔" * 20)
            print(f"⏰ TIMESTAMP: {timestamp}")
            print("📝 NOTIFICATION DATA:")
            print("=" * 80)
            print(json.dumps(notification_data, indent=2))
            print("=" * 80)
            print("✅ This is a REAL notification from Microsoft Teams!")
            print("🔔" * 70)
            
            # Save transcript notification data with clear labeling
            with open('transcript_notifications.json', 'a') as f:
                json.dump({
                    'timestamp': timestamp,
                    'type': 'REAL_TEAMS_TRANSCRIPT_NOTIFICATION',
                    'source': 'Microsoft Teams via Graph API',
                    'data': notification_data
                }, f, indent=2)
                f.write('\n')
            
            return jsonify({'status': 'transcript_received'}), 200
            
        except Exception as e:
            print(f"Error processing transcript notification: {e}")
            return jsonify({'error': str(e)}), 400
    
    return "Transcript Webhook Endpoint", 200


@app.route('/teams/lifecycle', methods=['GET', 'POST'])
def lifecycle_webhook():
    """Handle subscription lifecycle notifications for auto-renewal"""
    
    # Check for validation token first (works for both GET and POST)
    validation_token = request.args.get('validationToken')
    if validation_token:
        print(f"VALIDATION: Lifecycle webhook validation: {validation_token}")
        return validation_token, 200, {'Content-Type': 'text/plain'}
    
    if request.method == 'POST':
        try:
            lifecycle_data = request.get_json()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[{timestamp}] LIFECYCLE NOTIFICATION:")
            print("=" * 60)
            print(json.dumps(lifecycle_data, indent=2))
            print("=" * 60)
            
            # Save lifecycle notification data
            with open('lifecycle_notifications.json', 'a') as f:
                json.dump({
                    'timestamp': timestamp,
                    'type': 'lifecycle_notification',
                    'data': lifecycle_data
                }, f, indent=2)
                f.write('\n')
            
            # Handle auto-renewal for reauthorizationRequired
            if 'value' in lifecycle_data:
                for notification in lifecycle_data['value']:
                    lifecycle_event = notification.get('lifecycleEvent')
                    subscription_id = notification.get('subscriptionId')
                    
                    print(f"Lifecycle Event: {lifecycle_event} for subscription: {subscription_id}")
                    
                    if lifecycle_event == 'reauthorizationRequired' and subscription_id:
                        print("AUTO-RENEWING: Starting subscription renewal...")
                        access_token = get_fresh_access_token()
                        
                        if access_token:
                            success = renew_subscription(subscription_id, access_token)
                            if success:
                                print("SUCCESS: Subscription auto-renewed successfully!")
                            else:
                                print("FAILED: Failed to auto-renew subscription")
                        else:
                            print("FAILED: Failed to get access token for renewal")
                    
                    elif lifecycle_event == 'subscriptionRemoved':
                        print("WARNING: Subscription was removed/expired")
                        # TODO: Optionally recreate subscription here
                    
                    elif lifecycle_event == 'missed':
                        print("WARNING: Some notifications were missed")
            
            return jsonify({'status': 'lifecycle_processed'}), 200
            
        except Exception as e:
            print(f"Error processing lifecycle notification: {e}")
            return jsonify({'error': str(e)}), 400
    
    return "Lifecycle Webhook Endpoint", 200


# @app.route('/health')
# def health():
#     return jsonify({
#         'status': 'healthy',
#         'timestamp': datetime.now().isoformat(),
#         'endpoints': {
#             'transcript_webhook': '/teams/webhook',
#             'lifecycle_webhook': '/teams/lifecycle'
#         }
#     }), 200

@app.route('/')
def index():
    return jsonify({
        'message': 'Teams Transcript Webhook Server',
        'endpoints': {
            'transcript_notifications': '/teams/webhook',
        }
    }), 200

if __name__ == '__main__':
    print("Starting Teams Transcript Webhook Server...")
    print("Transcript notifications: /teams/webhook")
    print("Lifecycle notifications: /teams/lifecycle")
    print("Health check: /health")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
