import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from utils import get_youtube_formats, download_youtube_video

# Configuración del bot
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
<b>🤖 Bot de Descargas YouTube</b>
Envíame un enlace de YouTube y elige la calidad para descargar.

<b>Comandos disponibles:</b>
/start - Mostrar este mensaje
/help - Ayuda rápida
"""

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, parse_mode="HTML")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Envíame un enlace válido de YouTube.")

# Manejador principal
async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Solo se permite YouTube por ahora.")
        return

    try:
        formats = get_youtube_formats(url)
        if not formats:
            await update.message.reply_text("❌ No se encontraron formatos disponibles.")
            return

        keyboard = [
            [InlineKeyboardButton(fmt["resolution"], callback_data=f"yt_{fmt['format_id']}")]
            for fmt in formats
        ]
        await update.message.reply_text(
            "🎥 Elige la calidad de descarga:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        context.user_data["youtube_url"] = url

    except Exception as e:
        logger.error(f"Error procesando enlace de YouTube: {e}")
        await update.message.reply_text("❌ Error al procesar el video.")

# Botón de descarga
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith("yt_"):
        await query.edit_message_text("❌ Acción no reconocida.")
        return

    format_id = data.split("_")[1]
    url = context.user_data.get("youtube_url")
    if not url:
        await query.edit_message_text("❌ No se encontró el enlace original.")
        return

    try:
        await query.edit_message_text("⏳ Descargando video...")
        file_path = download_youtube_video(url, format_id)
        if not file_path:
            await query.edit_message_text("❌ Falló la descarga.")
            return

        with open(file_path, "rb") as file:
            await query.message.reply_video(file, caption="✅ ¡Video descargado!")
        os.remove(file_path)

    except Exception as e:
        logger.error(f"Error al descargar: {e}")
        await query.edit_message_text("❌ Error en la descarga.")

# main()
def main():
    logger.info("🚀 Iniciando bot de YouTube...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("✅ Bot en ejecución.")
    app.run_polling()

if __name__ == "__main__":
    main()
