import os
import re
import sys
import logging
from datetime import datetime, date
from pathlib import Path

# Add src to python path so we can import from config
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

from src.config import Settings
settings = Settings()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = "http://localhost:8000/api/ingest"
VAULT = Path(settings.obsidian_vault_path)
DAILY_NOTES_FOLDER = "0-Daily Notes"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I am **Dhi**, your personal intelligence bot.\n\n"
        "Send me a **URL** and I will ingest it into your knowledge base.\n"
        "Send me **text** and I will append it to today's Daily Note in Obsidian.",
    )

def extract_urls(text: str) -> list[str]:
    """Extract all URLs from a text string."""
    url_pattern = re.compile(r'(https?://\S+)')
    return url_pattern.findall(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages (text or URLs)."""
    text = update.message.text
    if not text:
        return
        
    urls = extract_urls(text)
    
    if urls:
        # Handle as ingestion
        await update.message.reply_text(f"Found {len(urls)} link(s). Sending to ingestion pipeline...")
        
        async with httpx.AsyncClient() as client:
            for url in urls:
                try:
                    response = await client.post(
                        API_URL,
                        json={
                            "url": url,
                            "tags": ["telegram-bot", "dhi"],
                            "telegram_chat_id": update.effective_chat.id,
                            "telegram_bot_token": TELEGRAM_TOKEN,
                        },
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        logger.info(f"Successfully triggered ingestion API for: {url}")
                        await update.message.reply_text(
                            f"✅ **Ingestion Pipeline Triggered**\n\n"
                            f"The URL `{url}` has been sent to your local backend and is processing in the background.",
                            parse_mode="Markdown"
                        )
                    else:
                        logger.error(f"Ingestion API returned {response.status_code} for {url}: {response.text}")
                        await update.message.reply_text(f"❌ **Failed to start ingestion** for {url}:\nStatus: {response.status_code}\nDetails: {response.text}")
                except Exception as e:
                    logger.error(f"Error contacting ingestion API for {url}: {e}", exc_info=True)
                    await update.message.reply_text(f"⚠️ **Connection Error**:\n{e}\n\nIs your FastAPI server (`src/main.py`) running locally?")
    else:
        # Handle as quick thought -> Obsidian Daily Note
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M")
        
        dest_dir = VAULT / DAILY_NOTES_FOLDER
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{today}.md"
        
        # Format the entry
        entry = f"\n### 📱 Thought from Dhi ({now})\n{text}\n"
        
        try:
            with open(dest_file, "a", encoding="utf-8") as f:
                f.write(entry)
            logger.info(f"Successfully saved quick thought to {dest_file}")
            await update.message.reply_text(
                f"✅ **Success!**\n\n"
                f"📝 Thought saved to your vault:\n"
                f"📁 `{DAILY_NOTES_FOLDER}`\n"
                f"📄 `{today}.md`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to write thought to Obsidian vault ({dest_file}): {e}", exc_info=True)
            await update.message.reply_text(f"❌ **Error saving to Obsidian:**\n{e}")

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN found in .env file.")
        print("\n❌ ERROR: TELEGRAM_TOKEN is missing!")
        print("Please create a bot via @BotFather on Telegram, get the token, and add it to your .env file:")
        print("TELEGRAM_TOKEN=your_token_here\n")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
