from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Premium plan configurations
PREMIUM_PLANS = {
    "monthly": {
        "name": "Monthly Premium",
        "duration_days": 30,
        "price": 49,  # INR
        "price_in_paise": 4900,  # RazorPay uses paise
        "description": "30 days of unlimited downloads",
        "plan_id": "monthly_premium"
    },
    "quarterly": {
        "name": "Quarterly Premium",
        "duration_days": 90,
        "price": 129,  # INR
        "price_in_paise": 12900,  # RazorPay uses paise
        "description": "90 days of unlimited downloads",
        "plan_id": "quarterly_premium"
    },
    "yearly": {
        "name": "Yearly Premium",
        "duration_days": 365,
        "price": 499,  # INR
        "price_in_paise": 49900,  # RazorPay uses paise
        "description": "365 days of unlimited downloads",
        "plan_id": "yearly_premium"
    }
}

# Discount codes (if applicable)
DISCOUNT_CODES = {
    "WELCOME10": {
        "percentage": 10,
        "max_discount": 50,  # INR
        "valid_until": "2023-12-31",
        "description": "10% off for new users"
    },
    "PREMIUM20": {
        "percentage": 20,
        "max_discount": 100,  # INR
        "valid_until": "2023-12-31",
        "description": "20% off for premium plans"
    }
}

def get_all_plans() -> Dict:
    """Get all available premium plans
    
    Returns:
        Dict: Dictionary of premium plans
    """
    return PREMIUM_PLANS

def get_plan_by_id(plan_id: str) -> Optional[Dict]:
    """Get plan details by plan ID
    
    Args:
        plan_id (str): ID of the premium plan
        
    Returns:
        Optional[Dict]: Plan details or None if plan doesn't exist
    """
    for plan in PREMIUM_PLANS.values():
        if plan["plan_id"] == plan_id:
            return plan
    return None

def get_plan_by_key(plan_key: str) -> Optional[Dict]:
    """Get plan details by plan key
    
    Args:
        plan_key (str): Key of the premium plan (monthly, quarterly, yearly)
        
    Returns:
        Optional[Dict]: Plan details or None if plan doesn't exist
    """
    return PREMIUM_PLANS.get(plan_key)

def get_formatted_plans_list() -> str:
    """Get formatted list of plans for display
    
    Returns:
        str: Formatted plans list
    """
    plans_text = ""
    for key, plan in PREMIUM_PLANS.items():
        plans_text += f"• *{plan['name']}* - ₹{plan['price']}\n  {plan['description']}\n\n"
    return plans_text

def get_plan_from_button_text(button_text: str) -> Optional[Dict]:
    """Get plan from button text
    
    Args:
        button_text (str): Button text (e.g., "Monthly - ₹49")
        
    Returns:
        Optional[Dict]: Plan details or None if no match
    """
    for key, plan in PREMIUM_PLANS.items():
        if f"{key.capitalize()} - ₹{plan['price']}" in button_text:
            return plan
    return None

def calculate_discounted_price(plan_id: str, discount_code: str) -> Dict:
    """Calculate discounted price for a plan
    
    Args:
        plan_id (str): ID of the premium plan
        discount_code (str): Discount code
        
    Returns:
        Dict: Dictionary with original price, discount amount, and final price
    """
    plan = get_plan_by_id(plan_id)
    if not plan:
        return {
            "original_price": 0,
            "discount_amount": 0,
            "final_price": 0,
            "is_valid": False,
            "message": "Invalid plan"
        }
    
    # Check if discount code is valid
    discount = DISCOUNT_CODES.get(discount_code.upper())
    if not discount:
        return {
            "original_price": plan["price"],
            "discount_amount": 0,
            "final_price": plan["price"],
            "original_price_paise": plan["price_in_paise"],
            "final_price_paise": plan["price_in_paise"],
            "is_valid": False,
            "message": "Invalid discount code"
        }
    
    # Calculate discount
    discount_amount = (plan["price"] * discount["percentage"]) / 100
    
    # Apply max discount cap
    if discount_amount > discount["max_discount"]:
        discount_amount = discount["max_discount"]
    
    # Calculate final price
    final_price = plan["price"] - discount_amount
    final_price_paise = int(final_price * 100)
    
    return {
        "original_price": plan["price"],
        "discount_amount": discount_amount,
        "final_price": final_price,
        "original_price_paise": plan["price_in_paise"],
        "final_price_paise": final_price_paise,
        "is_valid": True,
        "message": f"Discount applied: {discount['description']}"
    }

def get_plan_details_message(plan_id: str, discount_code: str = None) -> str:
    """Get detailed message about a plan
    
    Args:
        plan_id (str): ID of the premium plan
        discount_code (str, optional): Discount code. Defaults to None.
        
    Returns:
        str: Formatted plan details message
    """
    plan = get_plan_by_id(plan_id)
    if not plan:
        return "Invalid plan selected"
    
    message = f"*{plan['name']}*\n\n" \
              f"• Duration: {plan['duration_days']} days\n" \
              f"• Price: ₹{plan['price']}\n" \
              f"• {plan['description']}\n\n"
    
    # Add discount information if provided
    if discount_code:
        discount_info = calculate_discounted_price(plan_id, discount_code)
        if discount_info["is_valid"]:
            message += f"*Discount Applied*\n" \
                      f"• Original price: ₹{discount_info['original_price']}\n" \
                      f"• Discount: ₹{discount_info['discount_amount']}\n" \
                      f"• Final price: ₹{discount_info['final_price']}\n\n"
    
    message += "Click the button below to proceed with payment."
    
    return message