import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging config
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import bot runners
from main_bot.bot import run_main_bot
from payment_bot.bot import run_payment_bot

async def main():
    logger.info("🔄 Initializing Terabox Premium Bot System...")
    try:
        # Run both bots concurrently in the same event loop
        await asyncio.gather(
            run_main_bot(),  # Start the main bot
            run_payment_bot()  # Start the payment bot
        )
    except Exception as e:
        logger.error(f"❌ An error occurred while running bots: {e}")

if __name__ == "__main__":
    try:
        # Check if there's already a running event loop and run the main function accordingly
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.error("❌ Event loop is already running!")
        else:
            asyncio.run(main())
    except RuntimeError:
        # For Python >= 3.10
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
