import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from utils import get_available_formats, download_media, get_twitch_formats
from spotify import search_spotify, download_spotify_track

# Configuración
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ ¡TELEGRAM_TOKEN no está configurado!")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Mensajes
WELCOME_MSG = """
🌟 *Bot de Descargas Premium* 🌟
✅ **Soporta**: YouTube, Instagram, Twitch, Spotify, Facebook, TikTok.

📌 **Comandos**:
/start - Muestra este mensaje
/help - Ayuda rápida
/spotify_search <query> - Busca en Spotify
"""

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Envíame un enlace o usa /spotify_search.")

async def spotify_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🔍 Usa: /spotify_search <canción/artista>")
        return

    try:
        results = search_spotify(query)
        if not results:
            await update.message.reply_text("❌ No se encontraron resultados.")
            return

        keyboard = [
            [InlineKeyboardButton(f"{track['name']} - {track['artist']}", callback_data=f"spotify_{track['id']}")]
            for track in results[:5]
        ]
        await update.message.reply_text(
            "🎵 Resultados en Spotify:",
            reply_markup=InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error en Spotify: {e}")
        await update.message.reply_text("❌ Error al buscar en Spotify.")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    logger.info(f"Procesando enlace: {url}")

    try:
        if "youtube.com" in url or "youtu.be" in url:
            formats = get_available_formats(url)
            if not formats:
                await update.message.reply_text("❌ No se encontraron formatos disponibles.")
                return

            keyboard = [
                [InlineKeyboardButton(fmt["resolution"], callback_data=f"video_{fmt['format_id']}")]
                for fmt in formats[:5]
            ]
            await update.message.reply_text(
                "🛠️ Elige calidad:",
                reply_markup=InlineKeyboardMarkup(keyboard)
        
        elif "twitch.tv" in url:
            formats = get_twitch_formats(url)
            if not formats:
                await update.message.reply_text("❌ No se encontraron formatos disponibles para Twitch.")
                return

            keyboard = [
                [InlineKeyboardButton(fmt["quality"], callback_data=f"twitch_{fmt['format_id']}")]
                for fmt in formats[:3]
            ]
            await update.message.reply_text(
                "🎮 Elige calidad para Twitch:",
                reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif "spotify.com" in url:
            await update.message.reply_text("🔍 Usa /spotify_search para buscar en Spotify.")
        
        else:
            await update.message.reply_text("❌ Plataforma no soportada aún.")

    except Exception as e:
        logger.error(f"Error al procesar enlace: {e}")
        await update.message.reply_text("❌ Error al procesar el enlace.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        file_path = None
        if data.startswith("video_"):
            format_id = data.split("_")[1]
            url = query.message.reply_to_message.text
            await query.edit_message_text(text="⏳ Descargando video...")
            file_path = download_media(url, format_id)

        elif data.startswith("twitch_"):
            format_id = data.split("_")[1]
            url = query.message.reply_to_message.text
            await query.edit_message_text(text="⏳ Descargando de Twitch...")
            file_path = download_media(url, format_id, platform="twitch")

        elif data.startswith("spotify_"):
            track_id = data.split("_")[1]
            await query.edit_message_text(text="⏳ Descargando de Spotify...")
            file_path = download_spotify_track(track_id)

        if file_path:
            with open(file_path, 'rb') as file:
                if data.startswith("spotify_"):
                    await query.message.reply_audio(file, caption="✅ ¡Audio descargado!")
                else:
                    await query.message.reply_video(file, caption="✅ ¡Video descargado!")
            os.remove(file_path)
        else:
            await query.edit_message_text(text="❌ Error en la descarga")

    except Exception as e:
        logger.error(f"Error en descarga: {e}")
        await query.edit_message_text(text="❌ Error al descargar")

def main():
    try:
        logger.info("🚀 Iniciando bot...")
        app = ApplicationBuilder().token(TOKEN).build()

        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("spotify_search", spotify_search))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
        app.add_handler(CallbackQueryHandler(button_handler))

        logger.info("🤖 Bot listo para recibir mensajes...")
        app.run_polling()

    except Exception as e:
        logger.critical(f"CRASH: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
