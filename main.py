import os
import logging
import threading
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import bot starters
from main_bot.bot import run_main_bot
from payment_bot.bot import run_payment_bot

def start_bot(bot_runner, bot_name: str):
    """Wrapper to start a bot in a new thread with its own event loop."""
    try:
        logger.info(f"🚀 Starting {bot_name}...")
        asyncio.run(bot_runner())
    except Exception as e:
        logger.error(f"❌ Failed to start {bot_name}: {e}")

def main():
    """Main entry point for the application"""
    logger.info("🔄 Initializing Terabox Premium Bot System...")

    # Create threads for each bot
    main_bot_thread = threading.Thread(target=start_bot, args=(run_main_bot, "MainBot"), name="MainBot")
    payment_bot_thread = threading.Thread(target=start_bot, args=(run_payment_bot, "PaymentBot"), name="PaymentBot")

    # Start both bots
    main_bot_thread.start()
    payment_bot_thread.start()

    # Keep the main thread alive
    main_bot_thread.join()
    payment_bot_thread.join()

    logger.info("🛑 Both bots have stopped. Exiting.")

if __name__ == "__main__":
    main()
