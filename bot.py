import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from utils import (
    get_available_formats,
    download_media,
    get_twitch_formats,
    DownloadError,
    sanitize_filename,
    split_large_file
)
from spotify import search_spotify, download_spotify_track
from typing import Optional, List
import subprocess

# Configuración avanzada de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN no configurado")

MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB (límite actual de Telegram)
RECOMMENDED_SIZE = 1500 * 1024 * 1024  # 1.5GB (para evitar problemas)
CHUNK_SIZE = 50 * 1024 * 1024  # 50MB (tamaño para archivos divididos)

# Mensajes
WELCOME_MSG = """
<b>🌟 Descargador Premium v3 🌟</b>
✅ <b>Soportado</b>: YouTube, Twitch, Spotify, Instagram, TikTok
📦 <b>Soporta archivos grandes</b> (hasta 2GB)

📌 <b>Comandos</b>:
/start - Muestra este mensaje
/help - Muestra ayuda
/spotify <canción> - Busca en Spotify
/formats <url> - Muestra formatos disponibles
"""

async def send_chunked_file(update: Update, file_path: str, is_audio: bool = False):
    """Envía archivos grandes dividiéndolos en partes si es necesario"""
    try:
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        if file_size > RECOMMENDED_SIZE:
            # Dividir el archivo en partes
            await update.message.reply_text(f"✂️ Dividiendo archivo grande ({file_size//(1024*1024)}MB)...")
            chunk_files = split_large_file(file_path, CHUNK_SIZE)
            
            for i, chunk_file in enumerate(chunk_files, 1):
                with open(chunk_file, 'rb') as file:
                    caption = f"📦 Parte {i}/{len(chunk_files)} - {file_name}"
                    if is_audio:
                        await update.message.reply_audio(
                            audio=file,
                            title=caption,
                            timeout=300,
                            read_timeout=300,
                            write_timeout=300
                        )
                    else:
                        await update.message.reply_video(
                            video=file,
                            caption=caption,
                            supports_streaming=True,
                            timeout=300,
                            read_timeout=300,
                            write_timeout=300
                        )
                os.remove(chunk_file)
            await update.message.reply_text("✅ Todos los fragmentos enviados")
        else:
            # Enviar archivo normalmente
            with open(file_path, 'rb') as file:
                if is_audio:
                    await update.message.reply_audio(
                        audio=file,
                        title=file_name,
                        timeout=300,
                        read_timeout=300,
                        write_timeout=300
                    )
                else:
                    await update.message.reply_video(
                        video=file,
                        caption="✅ Descarga completada",
                        supports_streaming=True,
                        timeout=300,
                        read_timeout=300,
                        write_timeout=300
                    )
        
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}")
        raise

async def check_ffmpeg():
    """Verifica que FFmpeg esté instalado y funcional"""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg no está instalado o no funciona correctamente")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, parse_mode="HTML")
    
    # Verificar dependencias al inicio
    if not await check_ffmpeg():
        await update.message.reply_text("⚠️ Advertencia: FFmpeg no está configurado correctamente. Algunas funciones pueden no trabajar.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ Envíame un enlace de YouTube, Twitch o Spotify\n\n"
        "📌 Para Spotify puedes usar:\n"
        "/spotify <nombre de canción>\n\n"
        "⚠️ Archivos muy grandes se dividirán automáticamente"
    )
    await update.message.reply_text(help_text)

async def spotify_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔍 Uso: /spotify <nombre de canción>")
        return

    query = " ".join(context.args)
    try:
        await update.message.reply_text("🔍 Buscando en Spotify...")
        results = search_spotify(query)
        
        if not results:
            await update.message.reply_text("❌ No se encontraron resultados")
            return

        keyboard = [
            [InlineKeyboardButton(
                f"{track['name']} - {track['artist']}",
                callback_data=f"spotify_{track['id']}"
            )] for track in results[:5]
        ]
        
        await update.message.reply_text(
            "🎵 Elige una canción:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Spotify search error: {str(e)}")
        await update.message.reply_text("❌ Error al buscar en Spotify")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    logger.info(f"Processing URL: {url}")

    try:
        if "youtube.com" in url or "youtu.be" in url:
            await update.message.reply_text("🔍 Analizando video de YouTube...")
            formats = get_available_formats(url)
            
            # Filtrar formatos que excedan el límite
            valid_formats = [fmt for fmt in formats if fmt.get('filesize', 0) <= MAX_FILE_SIZE]
            
            if not valid_formats:
                await update.message.reply_text("❌ Todos los formatos disponibles exceden el límite de 2GB")
                return

            keyboard = [
                [InlineKeyboardButton(
                    f"{fmt['resolution']} (~{fmt['filesize']//(1024*1024)}MB)",
                    callback_data=f"yt_{fmt['format_id']}"
                )] for fmt in valid_formats[:5]
            ]
            
            await update.message.reply_text(
                "🎬 Elige calidad (se dividirá si es muy grande):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif "twitch.tv" in url:
            await update.message.reply_text("🔍 Analizando contenido de Twitch...")
            formats = get_twitch_formats(url)
            
            keyboard = [
                [InlineKeyboardButton(
                    f"{fmt['quality']} (~{fmt.get('filesize', fmt['bandwidth']//1024)}MB)",
                    callback_data=f"tw_{fmt['format_id']}"
                )] for fmt in formats[:3]
            ]
            
            await update.message.reply_text(
                "🎮 Elige calidad (se dividirá si es muy grande):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif "spotify.com" in url:
            await update.message.reply_text("🔍 Usa /spotify <canción> para buscar música")
        
        else:
            await update.message.reply_text("⚠️ Enlace no soportado. Prueba con YouTube, Twitch o Spotify")

    except DownloadError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"URL handling error: {str(e)}")
        await update.message.reply_text("❌ Error al procesar el enlace")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    url = query.message.reply_to_message.text

    try:
        if data.startswith("yt_"):
            format_id = data.split("_")[1]
            await query.edit_message_text("⏳ Descargando video de YouTube (esto puede tardar)...")
            file_path = download_media(url, format_id)
            await send_chunked_file(query.message.reply_to_message, file_path)
        
        elif data.startswith("tw_"):
            format_id = data.split("_")[1]
            await query.edit_message_text("⏳ Descargando de Twitch (esto puede tardar)...")
            file_path = download_media(url, format_id, "twitch")
            await send_chunked_file(query.message.reply_to_message, file_path)
        
        elif data.startswith("spotify_"):
            track_id = data.split("_")[1]
            await query.edit_message_text("⏳ Descargando de Spotify...")
            file_path = download_spotify_track(track_id)
            await send_chunked_file(query.message.reply_to_message, file_path, True)
        
        # Limpieza
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
    except DownloadError as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        await query.edit_message_text("❌ Fallo en la descarga. Intenta con una calidad más baja.")

def main():
    try:
        # Configurar tiempos de espera más largos para archivos grandes
        app = ApplicationBuilder() \
            .token(TOKEN) \
            .read_timeout(300) \
            .write_timeout(300) \
            .pool_timeout(300) \
            .build()

        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("spotify", spotify_search, has_args=True))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
        app.add_handler(CallbackQueryHandler(button_handler))

        logger.info("🤖 Bot iniciado con soporte para archivos grandes")
        app.run_polling(drop_pending_updates=True, close_loop=False)
    
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
