import yt_dlp
import os
import logging
from typing import List, Dict, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadError(Exception):
    pass

def sanitize_filename(filename: str) -> str:
    """Limpia caracteres inválidos en nombres de archivo"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:250]  # Limitar longitud

def get_available_formats(url: str) -> List[Dict]:
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'socket_timeout': 15,
        'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.sanitize_info(ydl.extract_info(url, download=False))
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('height'):
                        formats.append({
                            "format_id": fmt['format_id'],
                            "resolution": f"{fmt['height']}p",
                            "ext": fmt.get('ext', 'mp4'),
                            "filesize": fmt.get('filesize', 0)
                        })
            # Ordenar por resolución y filtrar formatos inválidos
            return sorted(
                [f for f in formats if f['filesize'] > 0],
                key=lambda x: x['filesize'],
                reverse=True
            )[:10]
    except Exception as e:
        logger.error(f"YTDL Error: {str(e)}")
        raise DownloadError(f"No se pudieron obtener formatos: {str(e)}")

def get_twitch_formats(url: str) -> List[Dict]:
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'extractor_args': {'twitch': {'vod': {'format': 'best'}}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.sanitize_info(ydl.extract_info(url, download=False))
            return [{
                "format_id": fmt['format_id'],
                "quality": f"{fmt.get('height', '?')}p",
                "bandwidth": fmt.get('tbr', 0)
            } for fmt in info.get('formats', []) if fmt.get('tbr')][:5]
    except Exception as e:
        logger.error(f"Twitch Error: {str(e)}")
        raise DownloadError(f"Error en Twitch: {str(e)}")

def download_media(url: str, format_id: str, platform: str = "youtube") -> str:
    download_path = "downloads"
    os.makedirs(download_path, exist_ok=True)
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'restrictfilenames': True,
        'merge_output_format': 'mp4',
        'retries': 3,
        'fragment_retries': 3,
        'extractor_args': {'youtube': {'player_skip': ['js']}},
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Verificar y corregir extensión
            if not os.path.exists(filename):
                possible_ext = ['mp4', 'mkv', 'webm', 'flv']
                for ext in possible_ext:
                    test_file = os.path.splitext(filename)[0] + '.' + ext
                    if os.path.exists(test_file):
                        return test_file
            
            if not os.path.exists(filename):
                raise DownloadError("Archivo descargado no encontrado")
                
            return filename
    except yt_dlp.DownloadError as e:
        logger.error(f"Download Error: {str(e)}")
        raise DownloadError(f"Error en descarga: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise DownloadError(f"Error inesperado: {str(e)}")
