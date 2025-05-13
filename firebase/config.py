import os
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase Admin SDK initialization (for Firestore)
def initialize_firebase_admin():
    """Initialize Firebase Admin SDK for Firestore operations"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
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
        return firestore.client()
    except Exception as e:
        print(f"Firebase Admin initialization error: {e}")
        return None

# Pyrebase initialization (for Authentication and Realtime Database)
def initialize_pyrebase():
    """Initialize Pyrebase for Authentication and Realtime Database operations"""
    try:
        config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }
        return pyrebase.initialize_app(config)
    except Exception as e:
        print(f"Pyrebase initialization error: {e}")
        return None

# Get Firestore database instance
def get_firestore_db():
    """Get Firestore database instance"""
    return initialize_firebase_admin()

# Get Pyrebase auth instance
def get_pyrebase_auth():
    """Get Pyrebase auth instance"""
    firebase = initialize_pyrebase()
    if firebase:
        return firebase.auth()
    return None

# Get Pyrebase database instance
def get_pyrebase_db():
    """Get Pyrebase database instance"""
    firebase = initialize_pyrebase()
    if firebase:
        return firebase.database()
    return None