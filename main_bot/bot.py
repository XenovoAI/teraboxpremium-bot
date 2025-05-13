import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Import local modules
from main_bot.url_detector import extract_terabox_urls, is_terabox_url, normalize_terabox_url
from main_bot.download import TeraboxDownloader
from main_bot.premium import is_user_premium, get_premium_status_message, get_premium_plans
from firebase.user import get_user, create_user, increment_free_uses, get_remaining_free_uses
from utils.constants import MAIN_BOT_TOKEN, PAYMENT_BOT_USERNAME, MESSAGES, BUTTON_TEXT, MAX_FREE_FILE_SIZE, MAX_PREMIUM_FILE_SIZE

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Terabox downloader
downloader = TeraboxDownloader()

# Callback data prefixes
CB_PREMIUM = "premium"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    user = update.effective_user
    user_id = user.id
    logger.info(f"User {user_id} started the bot")
    
    # Create user in database if not exists
    db_user = get_user(user_id)
    if not db_user:
        create_user(user_id, user.username or "", user.first_name or "", user.last_name or "")
    
    # Send welcome message
    await update.message.reply_text(
        MESSAGES["welcome"].format(name=user.first_name or "there"),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    await update.message.reply_text(
        MESSAGES["help"],
        parse_mode="Markdown"
    )

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /premium command"""
    user_id = update.effective_user.id
    
    # Check if user is premium
    premium_status = is_user_premium(user_id)
    
    # Get premium status message
    message = get_premium_status_message(user_id)
    
    # Create keyboard with premium options
    keyboard = []
    
    if not premium_status:
        # Add button to upgrade
        keyboard.append([InlineKeyboardButton(
            BUTTON_TEXT["upgrade_premium"], 
            url=f"https://t.me/{PAYMENT_BOT_USERNAME}?start=premium"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Send premium status message
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    message_text = update.message.text
    user_id = update.effective_user.id
    
    # Extract Terabox URLs from message
    terabox_urls = extract_terabox_urls(message_text)
    
    if not terabox_urls:
        # No Terabox URLs found
        await update.message.reply_text(
            MESSAGES["invalid_url"],
            parse_mode="Markdown"
        )
        return
    
    # Process each Terabox URL
    for url in terabox_urls:
        await process_terabox_url(update, context, url)

async def process_terabox_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str) -> None:
    """Process a Terabox URL"""
    user_id = update.effective_user.id
    
    # Check if user is premium
    is_premium = is_user_premium(user_id)
    
    if not is_premium:
        # Check if user has reached free usage limit
        remaining_uses = get_remaining_free_uses(user_id)
        if remaining_uses <= 0:
            # User has reached free usage limit
            keyboard = [[InlineKeyboardButton(
                BUTTON_TEXT["upgrade_premium"], 
                url=f"https://t.me/{PAYMENT_BOT_USERNAME}?start=premium"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                MESSAGES["free_limit_reached"],
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
    
    # Send processing message
    processing_message = await update.message.reply_text(
        MESSAGES["processing"].format(url=url),
        parse_mode="Markdown"
    )
    
    try:
        # Normalize URL
        normalized_url = normalize_terabox_url(url)
        
        # Get file info
        file_info = await downloader.get_file_info(normalized_url)
        
        if not file_info or not file_info.get("list"):
            # Failed to get file info
            await processing_message.edit_text(
                MESSAGES["download_error"].format(error="Failed to get file information"),
                parse_mode="Markdown"
            )
            return
        
        # Get file details
        file_list = file_info.get("list", [])
        
        # Process each file in the share
        for file in file_list:
            file_name = file.get("server_filename", "Unknown")
            file_size = int(file.get("size", 0))
            file_size_mb = file_size / (1024 * 1024)  # Convert to MB
            
            # Check file size limit based on user status
            max_size = MAX_FILE_SIZE_PREMIUM if is_premium else MAX_FILE_SIZE_FREE
            if file_size_mb > max_size:
                # File size exceeds limit
                await update.message.reply_text(
                    MESSAGES["file_too_large"].format(
                        file_name=file_name,
                        file_size=round(file_size_mb, 2),
                        max_size=max_size
                    ),
                    parse_mode="Markdown"
                )
                continue
            
            # Get download link
            download_link = await downloader.get_download_link(normalized_url, file.get("fs_id"))
            
            if not download_link:
                # Failed to get download link
                await update.message.reply_text(
                    MESSAGES["download_error"].format(error="Failed to generate download link"),
                    parse_mode="Markdown"
                )
                continue
            
            # Send download link
            await update.message.reply_text(
                MESSAGES["download_success"].format(
                    file_name=file_name,
                    file_size=round(file_size_mb, 2),
                    download_link=download_link
                ),
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
        
        # Increment free usage counter for non-premium users
        if not is_premium:
            increment_free_uses(user_id)
        
        # Delete processing message
        await processing_message.delete()
        
    except Exception as e:
        logger.error(f"Error processing Terabox URL: {e}")
        await processing_message.edit_text(
            MESSAGES["download_error"].format(error=str(e)),
            parse_mode="Markdown"
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    data = query.data
    
    # Handle different callback types
    if data == CB_PREMIUM:
        await premium_command(update, context)
    else:
        await query.answer("Unknown callback!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Send error message to user
    if update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

async def run_main_bot():
    """Run the main bot"""
    # Create application
    application = Application.builder().token(MAIN_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    print("✅ Payment Bot running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait()
