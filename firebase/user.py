from datetime import datetime, timedelta
import pytz
from firebase.config import get_firestore_db

# User collection reference
db = get_firestore_db()
users_ref = db.collection('users') if db else None

def get_user(user_id):
    """Get user data from Firestore
    
    Args:
        user_id (str): Telegram user ID
        
    Returns:
        dict: User data or None if user doesn't exist
    """
    if not users_ref:
        return None
    
    try:
        user_doc = users_ref.document(str(user_id)).get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        return None

def create_user(user_id, username=None):
    """Create a new user in Firestore
    
    Args:
        user_id (str): Telegram user ID
        username (str, optional): Telegram username
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not users_ref:
        return False
    
    try:
        # Check if user already exists
        existing_user = get_user(user_id)
        if existing_user:
            return True  # User already exists
        
        # Create new user with default values
        user_data = {
            'free_uses': 0,
            'plan': 'free',
            'expiry': None,
            'referral_bonus': False,
            'username': username,
            'created_at': datetime.now(pytz.UTC),
            'last_active': datetime.now(pytz.UTC)
        }
        
        users_ref.document(str(user_id)).set(user_data)
        return True
    except Exception as e:
        print(f"Error creating user {user_id}: {e}")
        return False

def update_user(user_id, data):
    """Update user data in Firestore
    
    Args:
        user_id (str): Telegram user ID
        data (dict): Data to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not users_ref:
        return False
    
    try:
        # Update last_active timestamp
        data['last_active'] = datetime.now(pytz.UTC)
        
        users_ref.document(str(user_id)).update(data)
        return True
    except Exception as e:
        print(f"Error updating user {user_id}: {e}")
        return False

def increment_free_uses(user_id):
    """Increment free_uses counter for a user
    
    Args:
        user_id (str): Telegram user ID
        
    Returns:
        int: New free_uses count or -1 if error
    """
    if not users_ref:
        return -1
    
    try:
        user_data = get_user(user_id)
        if not user_data:
            # Create user if doesn't exist
            create_user(user_id)
            user_data = {'free_uses': 0}
        
        new_count = user_data.get('free_uses', 0) + 1
        update_user(user_id, {'free_uses': new_count})
        return new_count
    except Exception as e:
        print(f"Error incrementing free_uses for user {user_id}: {e}")
        return -1

def get_remaining_free_uses(user_id):
    """Get remaining free uses for a user
    
    Args:
        user_id (str): Telegram user ID
        
    Returns:
        int: Remaining free uses (3 - current uses) or 0 if exceeded
    """
    if not users_ref:
        return 0
    
    try:
        user_data = get_user(user_id)
        if not user_data:
            # Create user if doesn't exist
            create_user(user_id)
            return 3  # Max free uses
        
        # Check if user has premium plan
        if user_data.get('plan') != 'free':
            # Check if premium plan is still valid
            expiry = user_data.get('expiry')
            if expiry:
                expiry_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                if expiry_date > datetime.now(pytz.UTC):
                    return float('inf')  # Unlimited for premium users
        
        # For free users, calculate remaining uses
        current_uses = user_data.get('free_uses', 0)
        remaining = max(3 - current_uses, 0)  # Max 3 free uses
        return remaining
    except Exception as e:
        print(f"Error getting remaining free uses for user {user_id}: {e}")
        return 0

def upgrade_user_plan(user_id, plan_type):
    """Upgrade user to premium plan
    
    Args:
        user_id (str): Telegram user ID
        plan_type (str): 'premium_20' or 'premium_99'
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not users_ref:
        return False
    
    try:
        # Calculate expiry date based on plan type
        if plan_type == 'premium_20':
            days = 12
        elif plan_type == 'premium_99':
            days = 99
        else:
            return False
        
        expiry_date = (datetime.now(pytz.UTC) + timedelta(days=days)).isoformat()
        
        # Update user data
        update_data = {
            'plan': plan_type,
            'expiry': expiry_date,
            'upgraded_at': datetime.now(pytz.UTC).isoformat()
        }
        
        return update_user(user_id, update_data)
    except Exception as e:
        print(f"Error upgrading user {user_id} to plan {plan_type}: {e}")
        return False

def reset_daily_uses():
    """Reset free_uses counter for all users (called by Cloud Function)
    
    Returns:
        int: Number of users reset or -1 if error
    """
    if not users_ref:
        return -1
    
    try:
        # Get all free users
        free_users = users_ref.where('plan', '==', 'free').stream()
        
        count = 0
        for user in free_users:
            users_ref.document(user.id).update({'free_uses': 0})
            count += 1
        
        return count
    except Exception as e:
        print(f"Error resetting daily uses: {e}")
        return -1