import os
import razorpay
import json
from typing import Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
from payment_bot.plans import get_plan_by_id, calculate_discounted_price
from utils.security import verify_payment_signature, verify_webhook_signature

# Load environment variables
load_dotenv()

# RazorPay configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

# Initialize RazorPay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_order(user_id: int, plan_id: str, discount_code: str = None) -> Tuple[bool, Dict]:
    """Create a RazorPay order
    
    Args:
        user_id (int): Telegram user ID
        plan_id (str): Premium plan ID
        discount_code (str, optional): Discount code. Defaults to None.
        
    Returns:
        Tuple[bool, Dict]: (Success status, Order details or error message)
    """
    try:
        # Get plan details
        plan = get_plan_by_id(plan_id)
        if not plan:
            return False, {"error": "Invalid plan selected"}
        
        # Apply discount if provided
        price_in_paise = plan["price_in_paise"]
        if discount_code:
            discount_info = calculate_discounted_price(plan_id, discount_code)
            if discount_info["is_valid"]:
                price_in_paise = discount_info["final_price_paise"]
        
        # Create order data
        order_data = {
            "amount": price_in_paise,
            "currency": "INR",
            "receipt": f"terabox_premium_{user_id}_{int(datetime.utcnow().timestamp())}",
            "notes": {
                "user_id": str(user_id),
                "plan_id": plan_id,
                "discount_code": discount_code if discount_code else ""
            }
        }
        
        # Create order in RazorPay
        order = razorpay_client.order.create(data=order_data)
        
        # Add plan details to response
        order["plan_name"] = plan["name"]
        order["plan_description"] = plan["description"]
        order["duration_days"] = plan["duration_days"]
        
        return True, order
    except Exception as e:
        return False, {"error": str(e)}

def verify_payment(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify RazorPay payment
    
    Args:
        order_id (str): RazorPay order ID
        payment_id (str): RazorPay payment ID
        signature (str): RazorPay signature
        
    Returns:
        bool: True if payment is valid, False otherwise
    """
    try:
        return verify_payment_signature(order_id, payment_id, signature)
    except Exception:
        return False

def get_payment_details(payment_id: str) -> Tuple[bool, Dict]:
    """Get payment details from RazorPay
    
    Args:
        payment_id (str): RazorPay payment ID
        
    Returns:
        Tuple[bool, Dict]: (Success status, Payment details or error message)
    """
    try:
        payment = razorpay_client.payment.fetch(payment_id)
        return True, payment
    except Exception as e:
        return False, {"error": str(e)}

def get_order_details(order_id: str) -> Tuple[bool, Dict]:
    """Get order details from RazorPay
    
    Args:
        order_id (str): RazorPay order ID
        
    Returns:
        Tuple[bool, Dict]: (Success status, Order details or error message)
    """
    try:
        order = razorpay_client.order.fetch(order_id)
        return True, order
    except Exception as e:
        return False, {"error": str(e)}

def process_webhook_event(request_body: bytes, signature: str) -> Tuple[bool, Dict]:
    """Process RazorPay webhook event
    
    Args:
        request_body (bytes): Request body
        signature (str): Signature from X-Razorpay-Signature header
        
    Returns:
        Tuple[bool, Dict]: (Success status, Event data or error message)
    """
    try:
        # Verify webhook signature
        if not verify_webhook_signature(request_body, signature, RAZORPAY_WEBHOOK_SECRET):
            return False, {"error": "Invalid webhook signature"}
        
        # Parse event data
        event_data = json.loads(request_body.decode('utf-8'))
        
        # Extract event details
        event = {
            "event": event_data.get("event"),
            "payment_id": event_data.get("payload", {}).get("payment", {}).get("entity", {}).get("id"),
            "order_id": event_data.get("payload", {}).get("payment", {}).get("entity", {}).get("order_id"),
            "status": event_data.get("payload", {}).get("payment", {}).get("entity", {}).get("status"),
            "amount": event_data.get("payload", {}).get("payment", {}).get("entity", {}).get("amount"),
            "notes": event_data.get("payload", {}).get("payment", {}).get("entity", {}).get("notes", {})
        }
        
        return True, event
    except Exception as e:
        return False, {"error": str(e)}

def generate_payment_link(order_id: str, amount: int, user_id: int, plan_id: str) -> str:
    """Generate payment link for RazorPay checkout
    
    Args:
        order_id (str): RazorPay order ID
        amount (int): Amount in paise
        user_id (int): Telegram user ID
        plan_id (str): Premium plan ID
        
    Returns:
        str: Payment link
    """
    plan = get_plan_by_id(plan_id)
    plan_name = plan["name"] if plan else "Premium Plan"
    
    return f"https://rzp.io/i/checkout?key={RAZORPAY_KEY_ID}&order_id={order_id}&amount={amount}&" \
           f"currency=INR&name=Terabox%20Premium&description={plan_name}&prefill[contact]=&" \
           f"prefill[email]=&notes[user_id]={user_id}&notes[plan_id]={plan_id}"