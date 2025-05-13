import os
import base64
import hashlib
import hmac
import time
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key and print it - should be saved to .env file
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Generated new encryption key: {ENCRYPTION_KEY}")
    print("Please add this key to your .env file as ENCRYPTION_KEY")

# Initialize Fernet cipher with the key
cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# RazorPay webhook verification
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data
    
    Args:
        data (str): Data to encrypt
        
    Returns:
        str: Encrypted data in base64 format
    """
    if not data:
        return ""
    
    try:
        encrypted_data = cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return ""

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt encrypted data
    
    Args:
        encrypted_data (str): Encrypted data in base64 format
        
    Returns:
        str: Decrypted data
    """
    if not encrypted_data:
        return ""
    
    try:
        decoded_data = base64.urlsafe_b64decode(encrypted_data)
        decrypted_data = cipher_suite.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""

def generate_payment_signature(order_id: str, payment_id: str) -> str:
    """Generate signature for payment verification
    
    Args:
        order_id (str): RazorPay order ID
        payment_id (str): RazorPay payment ID
        
    Returns:
        str: Generated signature
    """
    key = f"{order_id}|{payment_id}"
    signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        key.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify RazorPay payment signature
    
    Args:
        order_id (str): RazorPay order ID
        payment_id (str): RazorPay payment ID
        signature (str): Signature to verify
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    expected_signature = generate_payment_signature(order_id, payment_id)
    return hmac.compare_digest(expected_signature, signature)

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify RazorPay webhook signature
    
    Args:
        body (bytes): Request body
        signature (str): Signature from X-Razorpay-Signature header
        secret (str): Webhook secret
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def generate_callback_data(user_id: int, plan_id: str) -> str:
    """Generate encrypted callback data for payment flow
    
    Args:
        user_id (int): Telegram user ID
        plan_id (str): Premium plan ID
        
    Returns:
        str: Encrypted callback data
    """
    # Add timestamp to prevent reuse
    timestamp = int(time.time())
    data = f"{user_id}:{plan_id}:{timestamp}"
    return encrypt_data(data)

def decode_callback_data(encrypted_data: str) -> Tuple[Optional[int], Optional[str]]:
    """Decode encrypted callback data
    
    Args:
        encrypted_data (str): Encrypted callback data
        
    Returns:
        Tuple[Optional[int], Optional[str]]: (User ID, Plan ID) or (None, None) if invalid
    """
    try:
        decrypted_data = decrypt_data(encrypted_data)
        if not decrypted_data:
            return None, None
        
        parts = decrypted_data.split(":")
        if len(parts) != 3:
            return None, None
        
        user_id, plan_id, timestamp = parts
        
        # Check if callback data is not too old (24 hours)
        current_time = int(time.time())
        if current_time - int(timestamp) > 86400:  # 24 hours in seconds
            return None, None
        
        return int(user_id), plan_id
    except Exception:
        return None, None