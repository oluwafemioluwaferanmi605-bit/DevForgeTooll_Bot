import os
import sys
import logging
import time
import hashlib
import secrets
import base64
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🕒 Current Timestamp"), KeyboardButton("🔑 Generate Password")],
        [KeyboardButton("🔏 Base64 Encode"), KeyboardButton("🔓 Base64 Decode")],
        [KeyboardButton("🤖 Bot Info")]
    ], resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "⚙️ *Welcome to DevForgeToolBot\!*\n\nSelect a tool below or send me text to hash\.", 
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

    # Default: output MD5
    md5_hash = hashlib.md5(user_text.encode('utf-8')).hexdigest()
    await update.message.reply_text(f"📝 *MD5 Hash:* `{md5_hash}`", parse_mode="MarkdownV2")

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN is missing!")
        sys.exit(1)

    # Simplified production runner perfectly compatible with Render's worker lifestyle
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("Starting polling engine...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
