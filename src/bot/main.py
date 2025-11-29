import sys
import os
import asyncio
import logging

# --- Add Project Root to Python Path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End of Path Fix ---


# --- Main function with lazy imports ---
async def main():
    """Main function to start the bot"""
    print("🚀 Starting License Plate Recognition Bot...")
    print(
        "⏳ Loading dependencies... This may take a while in a slow environment. Please wait."
    )

    from aiogram import Bot, Dispatcher, types
    from aiogram.enums import ParseMode

    from config.bot_config import BotConfig
    from src.bot.handlers import router

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, BotConfig.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    logger = logging.getLogger(__name__)

    # Check for the bot token
    if not BotConfig.TOKEN:
        logger.error("BOT_TOKEN not found! Please set it in your .env file.")
        sys.exit(1)

    logger.info("Dependencies loaded. Initializing bot...")

    # Initialize bot
    bot = Bot(
        token=BotConfig.TOKEN, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )

    # --- FUNCTION TO SET UP MENU ---
    async def set_bot_commands():
        """Sets the bot's command menu."""
        commands = [
            types.BotCommand(command="/start", description="Show the main menu"),
            types.BotCommand(command="/status", description="Show current bot status"),
            types.BotCommand(
                command="/stats", description="Show recent detection stats"
            ),
            types.BotCommand(command="/help", description="Show this help message"),
        ]
        await bot.set_my_commands(commands)
        logger.info("Bot command menu set successfully.")

    # Set commands on startup
    await set_bot_commands()

    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Bot initialized. Starting polling...")

    # Start bot
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        print(f"\n💥 Bot crashed: {e}")


