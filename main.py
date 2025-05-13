import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from main_bot.bot import run_main_bot
from payment_bot.bot import run_payment_bot

async def main():
    logger.info("🔄 Initializing Terabox Premium Bot System...")
    try:
        await asyncio.gather(
            run_main_bot(),
            run_payment_bot()
        )
    except Exception as e:
        logger.error(f"❌ An error occurred while running bots: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        logger.error(f"❌ RuntimeError occurred: {e}")
    except Exception as e:
        logger.error(f"❌ Error during bot execution: {e}")
