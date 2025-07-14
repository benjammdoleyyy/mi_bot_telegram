import yt_dlp
import os

def get_available_formats(url: str) -> list:
    ydl_opts = {
        'quiet': True,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen_resolutions = set()
            if 'formats' in info:
                for fmt in info['formats']:
                    if (
                        fmt.get('vcodec') != 'none' and
                        fmt.get('acodec') != 'none' and
                        fmt.get('height') and
                        fmt['ext'] in ('mp4', 'webm')
                    ):
                        resolution = f"{fmt['height']}p"
                        if resolution not in seen_resolutions:
                            seen_resolutions.add(resolution)
                            formats.append({
                                "format_id": fmt['format_id'],
                                "resolution": resolution,
                                "ext": fmt['ext']
                            })
            return formats[:6]
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
        'outtmpl': f'{download_path}/%(id)s.%(ext)s',
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Error al descargar: {e}")
        return None
