import yt_dlp
import os

def get_available_formats(url: str) -> list:
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('height'):
                        formats.append({
                            "format_id": fmt['format_id'],
                            "resolution": f"{fmt['height']}p",
                            "ext": fmt['ext']
                        })
            return formats[:10]  # Limitar a 10 formatos
    except Exception as e:
        print(f"Error al obtener formatos: {e}")
        return []

def get_twitch_formats(url: str) -> list:
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('height'):
                        formats.append({
                            "format_id": fmt['format_id'],
                            "quality": f"{fmt['height']}p",
                        })
            return formats[:5]
    except Exception as e:
        print(f"Error en Twitch: {e}")
        return []

def download_media(url: str, format_id: str, platform: str = "youtube") -> str:
    download_path = "downloads"
    os.makedirs(download_path, exist_ok=True)

    ydl_opts = {
        'format': format_id,
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Error al descargar: {e}")
        return None
