import os
import logging
import threading
import re
from telegram import Update, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from utils import is_valid_instagram_url, fetch_instagram_data
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Welcome to the Instagram Downloader Bot!\n\n"
        "📩 Send me any *public* Instagram link (post, reel, or IGTV), and I'll fetch the media for you.\n"
        "⚠️ Make sure the post is *public* and not private.\n\n"
        "Happy downloading! 🎉"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instagram_post = update.message.text.strip()

    if not is_valid_instagram_url(instagram_post):
        await update.message.reply_text(
            "❌ Invalid Instagram URL. Please send a valid post, Reel, or IGTV link."
        )
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    progress_message = await update.message.reply_text("⏳ Fetching your media...")

    media_url = fetch_instagram_data(instagram_post)
    if not media_url:
        await progress_message.edit_text(
            "❌ Failed to fetch media. Ensure the post is public and try again."
        )
        return

    file_ext = "mp4" if "video" in media_url else "jpg"
    file_name = f"temp_{update.message.chat_id}.{file_ext}"

    import requests

    try:
        response = requests.get(media_url, stream=True)
        response.raise_for_status()
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

        with open(file_name, "rb") as media_file:
            if file_ext == "mp4":
                await update.message.reply_video(media_file, caption="👾 Downloaded with Instagram Bot")
            else:
                await update.message.reply_photo(media_file, caption="👾 Downloaded with Instagram Bot")

        await progress_message.delete()
    except Exception as e:
        logger.error(f"Error sending media: {e}")
        await progress_message.edit_text("❌ Failed to send media. Please try again later.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)


async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread = threading.Thread(target=lambda: context.application.create_task(process_download(update, context)))
    thread.start()


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_handler))

    logger.info("🤖 Instagram Downloader Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
