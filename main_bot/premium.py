from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import os

# Import Firebase user operations
from firebase.user import get_user, upgrade_user_plan

# Premium plan configurations
PREMIUM_PLANS = {
    "monthly": {
        "name": "Monthly Premium",
        "duration_days": 30,
        "price": 49,  # INR
        "description": "30 days of unlimited downloads",
        "plan_id": "monthly_premium"
    },
    "quarterly": {
        "name": "Quarterly Premium",
        "duration_days": 90,
        "price": 129,  # INR
        "description": "90 days of unlimited downloads",
        "plan_id": "quarterly_premium"
    },
    "yearly": {
        "name": "Yearly Premium",
        "duration_days": 365,
        "price": 499,  # INR
        "description": "365 days of unlimited downloads",
        "plan_id": "yearly_premium"
    }
}

def get_premium_plans() -> Dict:
    """Get all available premium plans
    
    Returns:
        Dict: Dictionary of premium plans
    """
    return PREMIUM_PLANS

def get_plan_details(plan_id: str) -> Optional[Dict]:
    """Get details for a specific premium plan
    
    Args:
        plan_id (str): ID of the premium plan
        
    Returns:
        Optional[Dict]: Plan details or None if plan doesn't exist
    """
    for plan_key, plan_data in PREMIUM_PLANS.items():
        if plan_data["plan_id"] == plan_id:
            return plan_data
    return None

def calculate_expiry_date(plan_id: str) -> Optional[datetime]:
    """Calculate expiry date for a premium plan
    
    Args:
        plan_id (str): ID of the premium plan
        
    Returns:
        Optional[datetime]: Expiry date or None if plan doesn't exist
    """
    plan = get_plan_details(plan_id)
    if not plan:
        return None
    
    now = datetime.utcnow()
    expiry_date = now + timedelta(days=plan["duration_days"])
    return expiry_date

def is_user_premium(user_id: int) -> Tuple[bool, Optional[datetime]]:
    """Check if a user has an active premium subscription
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        Tuple[bool, Optional[datetime]]: (Is premium, Expiry date or None)
    """
    user = get_user(user_id)
    if not user:
        return False, None
    
    # Check if user has premium status
    if not user.get("is_premium", False):
        return False, None
    
    # Check if premium has expired
    expiry_str = user.get("premium_expiry")
    if not expiry_str:
        return False, None
    
    try:
        expiry_date = datetime.fromisoformat(expiry_str)
        now = datetime.utcnow()
        
        if expiry_date > now:
            return True, expiry_date
        else:
            return False, expiry_date
    except (ValueError, TypeError):
        return False, None

def activate_premium_plan(user_id: int, plan_id: str, payment_id: str) -> Tuple[bool, str]:
    """Activate premium plan for a user
    
    Args:
        user_id (int): Telegram user ID
        plan_id (str): ID of the premium plan
        payment_id (str): Payment transaction ID
        
    Returns:
        Tuple[bool, str]: (Success status, Message)
    """
    # Get plan details
    plan = get_plan_details(plan_id)
    if not plan:
        return False, "Invalid plan selected"
    
    # Calculate expiry date
    expiry_date = calculate_expiry_date(plan_id)
    if not expiry_date:
        return False, "Failed to calculate plan expiry date"
    
    # Get current user status
    is_premium, current_expiry = is_user_premium(user_id)
    
    # If user is already premium, extend the subscription
    if is_premium and current_expiry:
        new_expiry = current_expiry + timedelta(days=plan["duration_days"])
    else:
        new_expiry = expiry_date
    
    # Update user in database
    premium_data = {
        "is_premium": True,
        "premium_plan": plan_id,
        "premium_expiry": new_expiry.isoformat(),
        "last_payment_id": payment_id,
        "last_payment_date": datetime.utcnow().isoformat()
    }
    
    success = upgrade_user_plan(user_id, premium_data)
    if not success:
        return False, "Failed to update premium status"
    
    return True, f"Premium plan activated until {new_expiry.strftime('%Y-%m-%d')}"

def format_time_remaining(expiry_date: datetime) -> str:
    """Format the remaining time for premium subscription
    
    Args:
        expiry_date (datetime): Premium expiry date
        
    Returns:
        str: Formatted time remaining
    """
    now = datetime.utcnow()
    remaining = expiry_date - now
    
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} days, {hours} hours"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    else:
        return f"{minutes} minutes"

def get_premium_status_message(user_id: int) -> str:
    """Get premium status message for a user
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        str: Premium status message
    """
    is_premium, expiry_date = is_user_premium(user_id)
    
    if is_premium and expiry_date:
        time_remaining = format_time_remaining(expiry_date)
        return f"✅ You have an active premium subscription!\n\n" \
               f"Your premium plan expires in {time_remaining}\n" \
               f"Expiry date: {expiry_date.strftime('%Y-%m-%d %H:%M')} UTC\n\n" \
               f"Enjoy unlimited downloads!"
    else:
        # Get available plans for upsell
        plans = get_premium_plans()
        plans_text = "\n".join([f"• {p['name']} - ₹{p['price']} - {p['description']}" 
                           for p in plans.values()])
        
        return f"❌ You don't have an active premium subscription.\n\n" \
               f"Upgrade to premium for unlimited downloads!\n\n" \
               f"Available plans:\n{plans_text}\n\n" \
               f"Use /upgrade to purchase a premium plan."