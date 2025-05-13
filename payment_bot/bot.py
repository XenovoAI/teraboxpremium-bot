import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from dotenv import load_dotenv

# Import local modules
from payment_bot.plans import get_all_plans, get_plan_by_id, get_formatted_plans_list, get_plan_details_message, get_plan_from_button_text
from payment_bot.razorpay_handlers import create_order, verify_payment, get_payment_details, generate_payment_link
from firebase.user import get_user, upgrade_user_plan
from utils.constants import PAYMENT_BOT_TOKEN, ADMIN_USER_IDS, MESSAGES, BUTTON_TEXT
from utils.security import generate_callback_data, decode_callback_data

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Callback data prefixes
CB_SELECT_PLAN = "select_plan:"
CB_CONFIRM_PLAN = "confirm_plan:"
CB_CANCEL_PLAN = "cancel_plan"
CB_PAYMENT_STATUS = "payment_status:"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} started the payment bot")
    
    # Check if user is coming from a deep link with a plan ID
    if context.args and len(context.args) > 0:
        # Try to get plan from deep link
        plan_id = context.args[0]
        plan = get_plan_by_id(plan_id)
        if plan:
            await show_plan_details(update, context, plan_id)
            return
    
    # Show welcome message and plan options
    await show_plans(update, context)

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available premium plans"""
    # Get all plans
    plans = get_all_plans()
    
    # Create keyboard with plan options
    keyboard = []
    for plan in plans:
        callback_data = f"{CB_SELECT_PLAN}{plan['id']}"
        keyboard.append([InlineKeyboardButton(get_formatted_plans_list(plan), callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with plan options
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=MESSAGES["select_plan"],
            reply_markup=reply_markup
        )
    else:
        await update.effective_message.reply_text(
            text=MESSAGES["select_plan"],
            reply_markup=reply_markup
        )

async def show_plan_details(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: Optional[str] = None) -> None:
    """Show details for a specific plan"""
    # Get plan ID from callback data if not provided
    if not plan_id and update.callback_query:
        callback_data = update.callback_query.data
        plan_id = callback_data.replace(CB_SELECT_PLAN, "")
    
    # Get plan details
    plan = get_plan_by_id(plan_id)
    if not plan:
        await update.callback_query.answer("Plan not found!")
        return
    
    # Create keyboard with confirm and cancel buttons
    keyboard = [
        [InlineKeyboardButton(BUTTON_TEXT["confirm_plan"], callback_data=f"{CB_CONFIRM_PLAN}{plan_id}")],
        [InlineKeyboardButton(BUTTON_TEXT["cancel"], callback_data=CB_CANCEL_PLAN)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get plan details message
    message = get_plan_details_message(plan)
    
    # Send message with plan details
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.effective_message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def create_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create payment for selected plan"""
    # Get user ID
    user_id = update.effective_user.id
    
    # Get plan ID from callback data
    callback_data = update.callback_query.data
    plan_id = callback_data.replace(CB_CONFIRM_PLAN, "")
    
    # Create order in RazorPay
    success, order = create_order(user_id, plan_id)
    if not success:
        await update.callback_query.answer("Failed to create payment!")
        await update.callback_query.edit_message_text(
            text=MESSAGES["payment_error"].format(error=order.get("error", "Unknown error"))
        )
        return
    
    # Generate payment link
    payment_link = generate_payment_link(
        order_id=order["id"],
        amount=order["amount"],
        user_id=user_id,
        plan_id=plan_id
    )
    
    # Create keyboard with payment link and check status buttons
    keyboard = [
        [InlineKeyboardButton(BUTTON_TEXT["pay_now"], url=payment_link)],
        [InlineKeyboardButton(BUTTON_TEXT["check_payment_status"], 
                             callback_data=f"{CB_PAYMENT_STATUS}{order['id']}")],
        [InlineKeyboardButton(BUTTON_TEXT["cancel"], callback_data=CB_CANCEL_PLAN)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with payment instructions
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=MESSAGES["payment_instructions"].format(
            plan_name=order["plan_name"],
            amount=order["amount"]/100,  # Convert paise to rupees
            order_id=order["id"]
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Store order ID in user data
    context.user_data["current_order_id"] = order["id"]
    context.user_data["current_plan_id"] = plan_id

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check payment status for an order"""
    # Get order ID from callback data
    callback_data = update.callback_query.data
    order_id = callback_data.replace(CB_PAYMENT_STATUS, "")
    
    # Get user ID
    user_id = update.effective_user.id
    
    # Get plan ID from user data or use a default
    plan_id = context.user_data.get("current_plan_id", "unknown")
    
    # Check if payment is completed
    from razorpay.resources import Order
    from razorpay.errors import BadRequestError
    
    try:
        # Get order details from RazorPay
        from payment_bot.razorpay_handlers import get_order_details
        success, order = get_order_details(order_id)
        
        if not success:
            await update.callback_query.answer("Failed to check payment status!")
            return
        
        # Check if payment is completed
        if order.get("status") == "paid":
            # Payment successful, upgrade user plan
            plan = get_plan_by_id(plan_id)
            if not plan:
                await update.callback_query.answer("Plan not found!")
                return
            
            # Upgrade user plan
            upgrade_success = upgrade_user_plan(user_id, plan_id, plan["duration_days"])
            
            # Send success message
            await update.callback_query.answer("Payment successful!")
            await update.callback_query.edit_message_text(
                text=MESSAGES["payment_success"].format(
                    plan_name=plan["name"],
                    duration=plan["duration_days"]
                ),
                parse_mode="Markdown"
            )
            
            # Clear user data
            if "current_order_id" in context.user_data:
                del context.user_data["current_order_id"]
            if "current_plan_id" in context.user_data:
                del context.user_data["current_plan_id"]
                
            # Log successful payment
            logger.info(f"User {user_id} successfully upgraded to plan {plan_id}")
            
            # Notify admins about successful payment
            for admin_id in ADMIN_USER_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🎉 New payment received!\n\nUser ID: {user_id}\nPlan: {plan['name']}\nAmount: ₹{order.get('amount', 0)/100}\nOrder ID: {order_id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
        else:
            # Payment pending or failed
            # Generate payment link again
            payment_link = generate_payment_link(
                order_id=order_id,
                amount=order.get("amount", 0),
                user_id=user_id,
                plan_id=plan_id
            )
            
            # Create keyboard with payment link and check status buttons
            keyboard = [
                [InlineKeyboardButton(BUTTON_TEXT["pay_now"], url=payment_link)],
                [InlineKeyboardButton(BUTTON_TEXT["check_payment_status"], 
                                    callback_data=f"{CB_PAYMENT_STATUS}{order_id}")],
                [InlineKeyboardButton(BUTTON_TEXT["cancel"], callback_data=CB_CANCEL_PLAN)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send message with payment status
            await update.callback_query.answer("Payment not completed yet!")
            await update.callback_query.edit_message_text(
                text=MESSAGES["payment_pending"].format(
                    order_id=order_id
                ),
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        await update.callback_query.answer("Failed to check payment status!")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    data = query.data
    
    # Handle different callback types
    if data.startswith(CB_SELECT_PLAN):
        await show_plan_details(update, context)
    elif data.startswith(CB_CONFIRM_PLAN):
        await create_payment(update, context)
    elif data == CB_CANCEL_PLAN:
        await show_plans(update, context)
    elif data.startswith(CB_PAYMENT_STATUS):
        await check_payment_status(update, context)
    else:
        await query.answer("Unknown callback!")

async def handle_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle RazorPay webhook events"""
    # This function would be used if we set up a webhook endpoint
    # For simplicity, we're using the check_payment_status function instead
    pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Send error message to user
    if update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

def run_payment_bot():
    """Run the payment bot"""
    # Create application
    application = Application.builder().token(PAYMENT_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    run_payment_bot()