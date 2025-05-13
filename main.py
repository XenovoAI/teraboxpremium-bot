import os
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import bot runners after loading env
from main_bot.bot import run_main_bot
from payment_bot.bot import run_payment_bot

async def main():
    logger.info("🔄 Initializing Terabox Premium Bot System...")

    try:
        # Run both bots concurrently in the same event loop
        await asyncio.gather(
            run_main_bot(),
            run_payment_bot()
        )
    except Exception as e:
        logger.error(f"❌ An error occurred while running bots: {e}")

if __name__ == "__main__":
    asyncio.run(main())
