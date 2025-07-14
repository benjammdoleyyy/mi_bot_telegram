import yt_dlp
import os
import logging
import subprocess
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadError(Exception):
    """Excepción personalizada para errores de descarga"""
    pass

def sanitize_filename(filename: str) -> str:
    """
    Limpia caracteres inválidos en nombres de archivo y acorta si es necesario
    Args:
        filename: Nombre de archivo a sanitizar
    Returns:
        str: Nombre sanitizado
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:200]  # Limitar longitud para evitar problemas

def get_file_metadata(file_path: str) -> Dict:
    """
    Obtiene metadatos básicos de un archivo
    Args:
        file_path: Ruta al archivo
    Returns:
        dict: Metadatos (tamaño, duración, etc.)
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        return {
            'size': os.path.getsize(file_path),
            'extension': Path(file_path).suffix.lower(),
            'filename': os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Error obteniendo metadatos: {str(e)}")
        raise DownloadError("Error al analizar el archivo")

def get_available_formats(url: str) -> List[Dict]:
    """
    Obtiene formatos disponibles para un video de YouTube
    Args:
        url: URL del video
    Returns:
        list: Lista de formatos disponibles
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'socket_timeout': 30,
        'extractor_args': {'youtube': {'skip': ['dash', 'hls']},
        'compat_opts': {'no-youtube-unavailable-videos'},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.sanitize_info(ydl.extract_info(url, download=False))
            
            if not info:
                raise DownloadError("No se pudo obtener información del video")
            
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('height'):
                        # Calcular tamaño aproximado si no está disponible
                        filesize = fmt.get('filesize') or estimate_filesize(
                            fmt.get('width'),
                            fmt.get('height'),
                            fmt.get('fps'),
                            fmt.get('tbr'),
                            fmt.get('vbr'),
                            fmt.get('abr')
                        )
                        
                        formats.append({
                            "format_id": fmt['format_id'],
                            "resolution": f"{fmt['height']}p",
                            "ext": fmt.get('ext', 'mp4'),
                            "filesize": filesize,
                            "vcodec": fmt.get('vcodec', 'unknown'),
                            "acodec": fmt.get('acodec', 'unknown'),
                            "fps": fmt.get('fps'),
                            "tbr": fmt.get('tbr')
                        })
            
            # Ordenar por resolución y filtrar formatos inválidos
            valid_formats = sorted(
                [f for f in formats if f['filesize'] and f['filesize'] > 0],
                key=lambda x: x['filesize'],
                reverse=True
            )
            
            return valid_formats[:15]  # Limitar a 15 formatos
            
    except yt_dlp.DownloadError as e:
        logger.error(f"YTDL Error: {str(e)}")
        raise DownloadError(f"No se pudieron obtener formatos: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise DownloadError(f"Error inesperado: {str(e)}")

def estimate_filesize(width: int, height: int, fps: int, 
                    tbr: int, vbr: int, abr: int) -> int:
    """
    Estima el tamaño de archivo basado en parámetros del video
    Args:
        width: Ancho del video
        height: Alto del video
        fps: Cuadros por segundo
        tbr: Tasa de bits total
        vbr: Tasa de bits de video
        abr: Tasa de bits de audio
    Returns:
        int: Tamaño estimado en bytes
    """
    try:
        # Estimación basada en parámetros comunes
        duration = 300  # Asumir 5 minutos para estimación
        if tbr:
            return int((tbr * 1000 * duration) / 8)  # tbr en kbps
        
        if vbr and abr:
            return int(((vbr + abr) * 1000 * duration) / 8)
        
        # Estimación basada en resolución y FPS
        if width and height and fps:
            pixel_count = width * height * fps * duration
            if height >= 1080:
                return int(pixel_count * 0.07)  # Factor para 1080p
            elif height >= 720:
                return int(pixel_count * 0.05)  # Factor para 720p
            else:
                return int(pixel_count * 0.03)  # Factor para 480p o menos
        
        return 100 * 1024 * 1024  # Valor por defecto: 100MB
    except:
        return 100 * 1024 * 1024  # Valor por defecto si falla la estimación

def get_twitch_formats(url: str) -> List[Dict]:
    """
    Obtiene formatos disponibles para un video de Twitch
    Args:
        url: URL del video/clip de Twitch
    Returns:
        list: Lista de formatos disponibles
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'socket_timeout': 30,
        'extractor_args': {'twitch': {'vod': {'format': 'best'}}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.sanitize_info(ydl.extract_info(url, download=False))
            
            if not info:
                raise DownloadError("No se pudo obtener información de Twitch")
            
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('tbr'):
                        filesize = fmt.get('filesize') or estimate_filesize(
                            fmt.get('width'),
                            fmt.get('height'),
                            fmt.get('fps'),
                            fmt.get('tbr'),
                            fmt.get('vbr'),
                            fmt.get('abr')
                        )
                        
                        formats.append({
                            "format_id": fmt['format_id'],
                            "quality": f"{fmt.get('height', '?')}p",
                            "bandwidth": fmt.get('tbr', 0),
                            "filesize": filesize,
                            "ext": fmt.get('ext', 'mp4'),
                            "protocol": fmt.get('protocol', 'unknown')
                        })
            
            # Filtrar formatos duplicados y ordenar
            unique_formats = {}
            for fmt in formats:
                key = (fmt['quality'], fmt['bandwidth'])
                if key not in unique_formats or fmt['filesize'] > unique_formats[key]['filesize']:
                    unique_formats[key] = fmt
            
            return sorted(
                list(unique_formats.values()),
                key=lambda x: x['filesize'],
                reverse=True
            )[:5]
            
    except yt_dlp.DownloadError as e:
        logger.error(f"Twitch Error: {str(e)}")
        raise DownloadError(f"Error en Twitch: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Twitch Error: {str(e)}")
        raise DownloadError(f"Error inesperado en Twitch: {str(e)}")

def download_media(url: str, format_id: str, platform: str = "youtube") -> str:
    """
    Descarga contenido multimedia de una URL
    Args:
        url: URL del contenido
        format_id: ID del formato a descargar
        platform: Plataforma de origen (youtube/twitch)
    Returns:
        str: Ruta al archivo descargado
    """
    download_path = "downloads"
    os.makedirs(download_path, exist_ok=True)
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'restrictfilenames': True,
        'retries': 3,
        'fragment_retries': 3,
        'socket_timeout': 30,
        'extractor_args': {
            'youtube': {'player_skip': ['js']},
            'twitch': {'vod': {'format': 'best'}}
        },
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'merge_output_format': 'mp4',
        'concurrent_fragment_downloads': 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Verificar primero si el video está disponible
            info = ydl.extract_info(url, download=False)
            if not info:
                raise DownloadError("El contenido no está disponible")
            
            # Descargar el video
            ydl.download([url])
            filename = ydl.prepare_filename(info)
            
            # Verificar y corregir extensión
            if not os.path.exists(filename):
                possible_ext = ['mp4', 'mkv', 'webm', 'flv']
                for ext in possible_ext:
                    test_file = os.path.splitext(filename)[0] + '.' + ext
                    if os.path.exists(test_file):
                        return test_file
            
            if not os.path.exists(filename):
                raise DownloadError("El archivo descargado no se encontró")
            
            return filename
            
    except yt_dlp.DownloadError as e:
        logger.error(f"Download Error: {str(e)}")
        raise DownloadError(f"Error en descarga: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Download Error: {str(e)}")
        raise DownloadError(f"Error inesperado al descargar: {str(e)}")

def split_large_file(file_path: str, chunk_size: int) -> List[str]:
    """
    Divide un archivo grande en partes más pequeñas usando FFmpeg
    Args:
        file_path: Ruta al archivo original
        chunk_size: Tamaño máximo de cada parte (en bytes)
    Returns:
        list: Lista de rutas a los archivos divididos
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        file_name = Path(file_path).stem
        file_ext = Path(file_path).suffix
        output_dir = Path(file_path).parent
        output_pattern = str(output_dir / f"{file_name}_part%03d{file_ext}")
        
        # Verificar si FFmpeg está disponible
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DownloadError("FFmpeg no está instalado o no funciona correctamente")
        
        # Usar FFmpeg para dividir el archivo
        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-c", "copy",  # Sin re-codificación
            "-fs", str(chunk_size),  # Tamaño máximo por fragmento
            "-map", "0",  # Todos los streams
            "-f", "segment",  # Modo segmentación
            "-segment_format", file_ext.lstrip('.'),  # Mismo formato que original
            "-reset_timestamps", "1",  # Resetear timestamps
            "-segment_time", "00:10:00",  # Tiempo máximo por segmento (10 mins)
            output_pattern
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise DownloadError(f"Error al dividir archivo: {result.stderr}")
        
        # Encontrar todos los fragmentos creados
        chunk_files = sorted(str(p) for p in output_dir.glob(f"{file_name}_part*{file_ext}"))
        
        if not chunk_files:
            raise DownloadError("No se crearon fragmentos del archivo")
        
        return chunk_files
        
    except Exception as e:
        logger.error(f"File Split Error: {str(e)}")
        raise DownloadError(f"Error al dividir el archivo: {str(e)}")

def cleanup_files(file_paths: List[str]):
    """
    Elimina archivos temporales
    Args:
        file_paths: Lista de rutas a eliminar
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error al eliminar {file_path}: {str(e)}")

def validate_url(url: str) -> bool:
    """
    Valida que una URL tenga un formato correcto
    Args:
        url: URL a validar
    Returns:
        bool: True si la URL es válida
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
