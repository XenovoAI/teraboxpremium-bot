import os
import logging
import threading
from dotenv import load_dotenv

# Import bot runners
from main_bot.bot import run_main_bot
from payment_bot.bot import run_payment_bot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application"""
    logger.info("Starting Terabox Premium Bot System")
    
    # Create threads for each bot
    main_bot_thread = threading.Thread(target=run_main_bot, name="MainBot")
    payment_bot_thread = threading.Thread(target=run_payment_bot, name="PaymentBot")
    
    # Start both bots
    logger.info("Starting Main Bot")
    main_bot_thread.start()
    
    logger.info("Starting Payment Bot")
    payment_bot_thread.start()
    
    # Wait for both threads to complete (they won't unless there's an error)
    main_bot_thread.join()
    payment_bot_thread.join()
    
    logger.info("Both bots have stopped. Exiting.")

if __name__ == "__main__":
    main()
