import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackContext, CallbackQueryHandler
)
from utils import download_media, get_available_formats, get_twitch_formats
from spotify import search_spotify, download_spotify_track

# Configuración
TOKEN = os.environ.get("TELEGRAM_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
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
"""

# Handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("ℹ️ Envíame un enlace o usa /spotify_search.")

def spotify_search(update: Update, context: CallbackContext):
    query = " ".join(context.args)
    if not query:
        update.message.reply_text("🔍 Usa: /spotify_search <canción/artista>")
        return

    results = search_spotify(query)
    if not results:
        update.message.reply_text("❌ No se encontraron resultados.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{track['name']} - {track['artist']}", callback_data=f"spotify_{track['id']}")]
        for track in results[:5]
    ]
    update.message.reply_text("🎵 Resultados en Spotify:", reply_markup=InlineKeyboardMarkup(keyboard))

def handle_download(update: Update, context: CallbackContext):
    url = update.message.text
    if "twitch.tv" in url:
        formats = get_twitch_formats(url)
        keyboard = [
            [InlineKeyboardButton(fmt["quality"], callback_data=f"twitch_{fmt['format_id']}")]
            for fmt in formats
        ]
        update.message.reply_text("🎮 Elige calidad para Twitch:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif any(domain in url for domain in ["youtube.com", "instagram.com", "facebook.com", "tiktok.com"]):
        formats = get_available_formats(url)
        keyboard = [
            [InlineKeyboardButton(fmt["resolution"], callback_data=f"video_{fmt['format_id']}")]
            for fmt in formats
        ]
        update.message.reply_text("🛠️ Elige calidad:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text("❌ Enlace no soportado.")

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data.startswith("twitch_"):
        format_id = data.split("_")[1]
        url = query.message.reply_to_message.text
        file_path = download_media(url, format_id, platform="twitch")
    elif data.startswith("spotify_"):
        track_id = data.split("_")[1]
        file_path = download_spotify_track(track_id)
    else:  # Video (YouTube, Instagram, etc.)
        format_id = data.split("_")[1]
        url = query.message.reply_to_message.text
        file_path = download_media(url, format_id)

    if file_path:
        with open(file_path, 'rb') as file:
            query.message.reply_document(file, caption="✅ ¡Descarga completada!")
        os.remove(file_path)
    else:
        query.message.reply_text("❌ Error al descargar.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("spotify_search", spotify_search))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_download))
    dp.add_handler(CallbackQueryHandler(button_handler))

    # 🚀 Modo polling para Railway (no requiere webhook)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
