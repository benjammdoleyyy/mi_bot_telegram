import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,  # Nuevo en v20
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,  # Reemplaza CallbackContext
    filters  # ¡Cambiado de Filters a filters!
)
from utils import download_media, get_available_formats, get_twitch_formats
from spotify import search_spotify, download_spotify_track

# Configuración
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ ¡TELEGRAM_TOKEN no está configurado!")

# Logging (visible en Railway)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Mensaje de inicio
WELCOME_MSG = """
🌟 *Bot de Descargas Premium* 🌟
Envía un enlace de YouTube, Spotify, Twitch, etc.
"""

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text(f"🔍 Procesando: {url}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="✅ Descarga en progreso...")

# Main
def main():
    try:
        logger.info("🚀 Iniciando bot...")
        app = ApplicationBuilder().token(TOKEN).build()

        # Registra handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
        app.add_handler(CallbackQueryHandler(button_handler))

        # Polling
        logger.info("🤖 Bot listo para recibir mensajes...")
        app.run_polling()

    except Exception as e:
        logger.critical(f"CRASH: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
