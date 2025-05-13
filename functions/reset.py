import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import pytz
import os

# This file is meant to be deployed as a Cloud Function

def initialize_firebase():
    """Initialize Firebase Admin SDK for Cloud Function"""
    try:
        # Use the application default credentials for Cloud Functions
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        return firestore.client()
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        return None

def reset_daily_uses(event, context):
    """Cloud Function to reset free_uses counter for all users at midnight UTC
    
    Args:
        event: Cloud Functions event object
        context: Cloud Functions context object
        
    Returns:
        str: Status message
    """
    db = initialize_firebase()
    if not db:
        return "Failed to initialize Firebase"
    
    try:
        # Get all free users
        users_ref = db.collection('users')
        free_users = users_ref.where('plan', '==', 'free').stream()
        
        count = 0
        for user in free_users:
            users_ref.document(user.id).update({'free_uses': 0})
            count += 1
        
        # Log the reset
        now = datetime.datetime.now(pytz.UTC)
        log_ref = db.collection('logs').document()
        log_ref.set({
            'type': 'daily_reset',
            'timestamp': now,
            'users_reset': count
        })
        
        return f"Successfully reset daily uses for {count} users at {now.isoformat()}"
    except Exception as e:
        error_msg = f"Error resetting daily uses: {e}"
        print(error_msg)
        return error_msg

# For local testing only
if __name__ == "__main__":
    # Set up service account credentials for local testing
    # This part won't run in the actual Cloud Function
    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
        })
        firebase_admin.initialize_app(cred)
        result = reset_daily_uses(None, None)
        print(result)
    except Exception as e:
        print(f"Local testing error: {e}")