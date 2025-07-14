import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackContext, CallbackQueryHandler
)
from utils import download_media, get_available_formats, get_twitch_formats
from spotify import search_spotify, download_spotify_track

# ===== CONFIGURACIÓN =====
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN no está configurado")

# Logging avanzado
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Logs en Railway
        logging.FileHandler('bot.log')  # Backup local (opcional)
    ]
)
logger = logging.getLogger(__name__)

# Mensajes
WELCOME_MSG = """
🌟 *Bot de Descargas Premium* 🌟
✅ **Soporta**: YouTube, Instagram, Twitch, Spotify, Facebook, TikTok.

📌 *Comandos*:
/start - Muestra este mensaje
/help - Ayuda rápida
/spotify_search <query> - Busca en Spotify
/download <url> - Descarga directa
/ping - Verifica si el bot está activo
"""

# ===== HANDLERS =====
def start(update: Update, context: CallbackContext):
    update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("ℹ️ Envíame un enlace o usa /spotify_search.")

def ping(update: Update, context: CallbackContext):
    """Mantiene activo el servicio en Railway"""
    update.message.reply_text("🏓 ¡Pong! Bot activo")

def error_handler(update: Update, context: CallbackContext):
    logger.error(f'Error: {context.error}', exc_info=True)

# (Tus otros handlers aquí: spotify_search, handle_download, button_handler...)
# ... [Mantén el mismo código que ya tenías para estos handlers]

# ===== MAIN =====
def main():
    try:
        logger.info("🚀 Iniciando bot en modo polling...")
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher

        # Handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("ping", ping))
        dp.add_handler(CommandHandler("spotify_search", spotify_search))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_download))
        dp.add_handler(CallbackQueryHandler(button_handler))
        
        # Manejo de errores
        dp.add_error_handler(error_handler)

        # Polling con reinicio automático
        updater.start_polling(
            poll_interval=1,
            timeout=30,
            drop_pending_updates=True
        )
        logger.info("🤖 Bot escuchando comandos...")
        updater.idle()

    except Exception as e:
        logger.critical(f"CRASH: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
