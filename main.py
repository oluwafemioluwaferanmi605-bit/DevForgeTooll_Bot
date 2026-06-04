import os
import sys
import logging
import asyncio
import signal
import time
import hashlib
import secrets
import base64
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables for local testing (Render uses Dashboard env vars)
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Main Keyboard Markup
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🕒 Current Timestamp"), KeyboardButton("🔑 Generate Password")],
        [KeyboardButton("🔏 Base64 Encode"), KeyboardButton("🔓 Base64 Decode")],
        [KeyboardButton("🤖 Bot Info")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and sets up the tool panel."""
    welcome_text = (
        "⚙️ *Welcome to DevForgeToolBot\!*\n\n"
        "Your self-contained local developer utility belt\. Select a tool below or "
        "send me a text string to see available transform hashes\."
    )
    await update.message.reply_text(welcome_text, parse_mode="MarkdownV2", reply_markup=get_main_keyboard())

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides bot metadata info."""
    info_text = (
        "🛠️ *DevForgeToolBot v1.0*\n\n"
        "• *Runtime:* Python 3.14.3\n"
        "• *Environment:* Render Background Worker\n"
        "• *External APIs:* None (100% Native & Secure)\n\n"
        "Select an option from the menu to execute tasks natively."
    )
    await update.message.reply_text(info_text, parse_mode="MarkdownV2")

# Core Utility Logic
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes menu interactions and string manipulations."""
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # Check for Menu buttons first
    if user_text == "🕒 Current Timestamp":
        now = datetime.utcnow()
        unix_time = int(time.time())
        response = (
            f"🕒 *Current UTC Time*\n\n"
            f"• *ISO 8601:* `{now.isoformat()}Z`\n"
            f"• *Unix Timestamp:* `{unix_time}`"
        )
        await update.message.reply_text(response, parse_mode="MarkdownV2")
        return

    elif user_text == "🔑 Generate Password":
        # Generate a cryptographically secure 16-character alphanumeric password
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(16))
        # Escape markdown special characters safely
        escaped_password = password.replace("!", "\\!").replace("#", "\\#").replace("$", "\\$").replace("^", "\\^").replace("&", "\\&").replace("*", "\\*")
        response = f"🔑 *Secure Password Generated:*\n\n`{escaped_password}`"
        await update.message.reply_text(response, parse_mode="MarkdownV2")
        return

    elif user_text == "🔏 Base64 Encode":
        context.user_data['action'] = 'b64_encode'
        await update.message.reply_text("📥 Send me the raw text string you want to **Encode** to Base64:")
        return

    elif user_text == "🔓 Base64 Decode":
        context.user_data['action'] = 'b64_decode'
        await update.message.reply_text("📥 Send me the Base64 string you want to **Decode**:")
        return

    elif user_text == "🤖 Bot Info":
        await info_command(update, context)
        return

    # Check for stateful operations
    current_action = context.user_data.get('action')
    if current_action == 'b64_encode':
        encoded = base64.b64encode(user_text.encode('utf-8')).decode('utf-8')
        context.user_data['action'] = None
        await update.message.reply_text(f"✅ *Base64 Encoded Result:*\n\n`{encoded}`", parse_mode="MarkdownV2")
        return
    elif current_action == 'b64_decode':
        context.user_data['action'] = None
        try:
            decoded = base64.b64decode(user_text.encode('utf-8')).decode('utf-8')
            # Quick escape for raw markdown strings
            decoded_escaped = decoded.replace("`", "\\`")
            await update.message.reply_text(f"✅ *Base64 Decoded Result:*\n\n`{decoded_escaped}`", parse_mode="MarkdownV2")
        except Exception:
            await update.message.reply_text("❌ Invalid Base64 payload. String transformation failed.")
        return

    # Default action: Generate Hash digest of the string
    md5_hash = hashlib.md5(user_text.encode('utf-8')).hexdigest()
    sha256_hash = hashlib.sha256(user_text.encode('utf-8')).hexdigest()
    url_encoded = urllib.parse.quote_plus(user_text)

    response = (
        f"📝 *String Transformations for:* `{user_text}`\n\n"
        f"• *MD5 Hash:* `{md5_hash}`\n"
        f"• *SHA-256 Hash:* `{sha256_hash}`\n"
        f"• *URL Encoded:* `{url_encoded}`"
    )
    await update.message.reply_text(response, parse_mode="MarkdownV2")

async def main() -> None:
    """Asynchronous driver application loop explicitly structured for Python 3.14."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("CRITICAL ERROR: TELEGRAM_BOT_TOKEN environment variable is missing!")
        sys.exit(1)

    # Building the application framework
    application = Application.builder().token(token).build()

    # Handlers configuration
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Initialize application
    await application.initialize()
    await application.start()
    
    # Start polling updates from Telegram API
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("DevForgeToolBot started successfully as a Render background worker.")

    # Python 3.14 Graceful Signal Handling Engine
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def stop_signal_handler():
        logger.info("Termination signal received. Shutting down system event loops...")
        stop_event.set()

    # Intercept system termination hooks safely without thread collision
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_signal_handler)
        except NotImplementedError:
            # Fallback for platforms without native signal loop attachment support
            pass

    # Keep the worker running until Render sends a SIGTERM or SIGINT event
    await stop_event.wait()

    # Clean shutdown of infrastructure layers
    logger.info("Stopping updater engine...")
    await application.updater.stop()
    logger.info("Stopping application framework...")
    await application.stop()
    logger.info("Sinking remaining service layers...")
    await application.shutdown()
    logger.info("Teardown completed safely. Execution stopped.")

if __name__ == "__main__":
    try:
        # Strict Python 3.14 top-level entry point isolation
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process execution halted via system interruption.")
