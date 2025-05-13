# Application constants for Terabox Premium Bot

from typing import Dict, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
PAYMENT_BOT_TOKEN = os.getenv("PAYMENT_BOT_TOKEN")
MAIN_BOT_USERNAME = os.getenv("MAIN_BOT_USERNAME", "terabox_premium_bot")
PAYMENT_BOT_USERNAME = os.getenv("PAYMENT_BOT_USERNAME", "terabox_payment_bot")

# Admin configuration
ADMIN_USER_IDS = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]

# Free tier limits
MAX_FREE_USES_PER_DAY = int(os.getenv("MAX_FREE_USES_PER_DAY", "3"))

# Rate limiting
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds
RATE_LIMIT_MAX_CALLS = int(os.getenv("RATE_LIMIT_MAX_CALLS", "5"))  # calls per period

# Terabox domains
TERABOX_DOMAINS = [
    "terabox.com",
    "teraboxapp.com",
    "4funbox.com",
    "mirrobox.com",
    "1024tera.com",
    "terabox.app",
    "nephobox.com",
    "momerybox.com",
    "teraboxapp.app",
    "ddl.to/terabox"
]

MESSAGES = {
    "welcome": WELCOME_MESSAGE,
    "help": HELP_MESSAGE,
    "free_limit_reached": FREE_LIMIT_REACHED_MESSAGE,
    "processing": PROCESSING_MESSAGE,
    "invalid_url": INVALID_URL_MESSAGE,
    "download_success_template": DOWNLOAD_SUCCESS_TEMPLATE,
    "download_error": DOWNLOAD_ERROR_MESSAGE,
    "premium_upgrade": PREMIUM_UPGRADE_MESSAGE,
    "payment_welcome": PAYMENT_WELCOME_MESSAGE,
    "payment_success": PAYMENT_SUCCESS_MESSAGE,
    "payment_cancelled": PAYMENT_CANCELLED_MESSAGE,
    "payment_error": PAYMENT_ERROR_MESSAGE,
}

# Bot messages
WELCOME_MESSAGE = (
    "👋 Welcome to Terabox Premium Bot!\n\n"
    "I can help you download files from Terabox without any ads, captchas, or waiting.\n\n"
    "🔹 *Free users*: {max_free} downloads per day\n"
    "🔸 *Premium users*: Unlimited downloads\n\n"
    "Simply send me a Terabox link to get started!\n\n"
    "Use /help to see all available commands."
).format(max_free=MAX_FREE_USES_PER_DAY)

HELP_MESSAGE = (
    "🤖 *Terabox Premium Bot Help*\n\n"
    "*Commands:*\n"
    "/start - Start the bot\n"
    "/help - Show this help message\n"
    "/status - Check your account status\n"
    "/upgrade - Upgrade to premium\n"
    "/cancel - Cancel current operation\n\n"
    "*How to use:*\n"
    "1. Send any Terabox link to get a direct download link\n"
    "2. Free users get {max_free} downloads per day\n"
    "3. Premium users get unlimited downloads\n\n"
    "*Premium Benefits:*\n"
    "✅ Unlimited downloads\n"
    "✅ No daily limits\n"
    "✅ Priority processing\n"
    "✅ Support for larger files\n\n"
    "For any issues, contact @{admin_username}"
).format(max_free=MAX_FREE_USES_PER_DAY, admin_username=MAIN_BOT_USERNAME)

FREE_LIMIT_REACHED_MESSAGE = (
    "⚠️ *Daily Limit Reached*\n\n"
    "You've used all {max_free} of your free downloads for today.\n\n"
    "🌟 *Upgrade to Premium* for unlimited downloads!\n\n"
    "Use /upgrade to see available plans."
).format(max_free=MAX_FREE_USES_PER_DAY)

PROCESSING_MESSAGE = "⏳ Processing your Terabox link..."

INVALID_URL_MESSAGE = (
    "❌ *Invalid URL*\n\n"
    "The link you sent doesn't appear to be a valid Terabox link.\n"
    "Please check the URL and try again."
)

DOWNLOAD_SUCCESS_TEMPLATE = (
    "✅ *Download Ready*\n\n"
    "📁 *File:* {filename}\n"
    "📏 *Size:* {filesize}\n\n"
    "⬇️ [Download Now]({download_url})\n\n"
    "🔗 This link will expire in 24 hours.\n"
    "Remaining free downloads today: {remaining_downloads}"
)

DOWNLOAD_ERROR_MESSAGE = (
    "❌ *Download Error*\n\n"
    "Sorry, I couldn't process this Terabox link.\n"
    "Error: {error_message}\n\n"
    "Please try again or contact support if the issue persists."
)

PREMIUM_UPGRADE_MESSAGE = (
    "🌟 *Upgrade to Premium*\n\n"
    "Enjoy unlimited Terabox downloads with our premium plans:\n\n"
    "{plans_list}\n\n"
    "Click the button below to start the upgrade process."
)

# Keyboard button texts
BUTTON_UPGRADE = "🌟 Upgrade to Premium"
BUTTON_CHECK_STATUS = "📊 Check Status"
BUTTON_CANCEL = "❌ Cancel"
BUTTON_MONTHLY_PLAN = "Monthly - ₹49"
BUTTON_QUARTERLY_PLAN = "Quarterly - ₹129"
BUTTON_YEARLY_PLAN = "Yearly - ₹499"
BUTTON_BACK = "⬅️ Back"
BUTTON_SUPPORT = "📞 Support"

# Payment messages
PAYMENT_WELCOME_MESSAGE = (
    "💳 *Terabox Premium Payment*\n\n"
    "Welcome to the payment process for Terabox Premium.\n"
    "Please select a plan to continue."
)

# ✅ DO NOT FORMAT THIS MESSAGE YET — it will be formatted at runtime
PAYMENT_SUCCESS_MESSAGE = (
    "✅ *Payment Successful*\n\n"
    "Thank you for upgrading to Terabox Premium!\n\n"
    "Your premium plan is now active.\n"
    "Plan: {plan_name}\n"
    "Valid until: {expiry_date}\n\n"
    "Return to @{main_bot} to enjoy your premium benefits!"
)

PAYMENT_CANCELLED_MESSAGE = (
    "❌ *Payment Cancelled*\n\n"
    "Your payment process has been cancelled.\n"
    "You can restart the upgrade process anytime using /upgrade."
)

PAYMENT_ERROR_MESSAGE = (
    "⚠️ *Payment Error*\n\n"
    "There was an error processing your payment: {error_message}\n\n"
    "Please try again or contact support if the issue persists."
)

# File size limits (in bytes)
MAX_FREE_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB
MAX_PREMIUM_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB
