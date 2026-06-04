import os
import sys
import logging
import asyncio
import signal
import time
import hashlib
import secrets
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🕒 Current Timestamp"), KeyboardButton("🔑 Generate Password")],
        [KeyboardButton("🤖 Bot Info")]
    ], resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Using raw strings to avoid syntax warnings on escape characters
    await update.message.reply_text(
        r"⚙️ *Welcome to DevForgeToolBot\!*" + "\n\nSelect a tool below or send me text to hash.", 
        parse_mode="MarkdownV2", 
        reply_markup=get_main_keyboard()
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🛠️ *DevForgeToolBot v1.0*\n\n• *Runtime:* Python 3.14\n• *Environment:* Render Worker", 
        parse_mode="MarkdownV2"
    )

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    
    if user_text == "🕒 Current Timestamp":
        await update.message.reply_text(f"🕒 *Unix Timestamp:* `{int(time.time())}`", parse_mode="MarkdownV2")
        return
    elif user_text == "🔑 Generate Password":
        pwd = "".join(secrets.choice("abcdefghijklmnopqrstuvwxyzABCDEF1234567890") for _ in range(16))
        await update.message.reply_text(f"🔑 *Password:* `{pwd}`", parse_mode="MarkdownV2")
        return
    elif user_text == "🤖 Bot Info":
        await info_command(update, context)
        return

    md5_hash = hashlib.md5(user_text.encode('utf-8')).hexdigest()
    await update.message.reply_text(f"📝 *MD5 Hash:* `{md5_hash}`", parse_mode="MarkdownV2")

async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN is missing!")
        sys.exit(1)

    # Initialize the application manually 
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Initialize the sub-components explicitly inside the active async context loop
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("DevForgeToolBot structural loops started successfully on Python 3.14.")

    # Create a persistent loop block that respects Render shutdown instructions
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_exit_signal():
        logger.info("Received termination signal from Render environment.")
        stop_event.set()

    # Register OS level hooks safely inside Python 3.14 event framework
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_exit_signal)
        except NotImplementedError:
            pass

    # This keeps your background worker alive indefinitely
    await stop_event.wait()

    # Graceful Teardown Flow
    logger.info("Initiating application teardown sequences...")
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logger.info("Shutdown sequence finalized.")

if __name__ == "__main__":
    # Explicitly spawn the event loop from the top level 
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process exited via signal manual disruption.")
