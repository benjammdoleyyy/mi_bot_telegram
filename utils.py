import yt_dlp
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'
}

def get_available_formats(url: str) -> list:
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'http_headers': HEADERS
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen_res = set()

            if 'formats' in info:
                for fmt in info['formats']:
                    if (
                        fmt.get('vcodec') != 'none' and
                        fmt.get('acodec') != 'none' and
                        fmt.get('height') and
                        fmt.get('ext') in ('mp4', 'webm') and
                        not fmt.get('format_note', '').lower().startswith('dash') and
                        not fmt.get('format_note', '').lower().startswith('audio')
                    ):
                        res = f"{fmt['height']}p"
                        if res not in seen_res:
                            seen_res.add(res)
                            formats.append({
                                "format_id": fmt['format_id'],
                                "resolution": res,
                                "ext": fmt['ext']
                            })

            return formats[:6] if formats else []

    except Exception as e:
        print(f"[ERROR] al obtener formatos: {e}")
        return []

def get_twitch_formats(url: str) -> list:
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'http_headers': HEADERS
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
        print(f"[ERROR] Twitch: {e}")
        return []

def download_media(url: str, format_id: str, platform: str = "generic") -> str:
    download_path = "downloads"
    os.makedirs(download_path, exist_ok=True)

    ydl_opts = {
        'quiet': True,
        'format': format_id,
        'outtmpl': f'{download_path}/%(id)s.%(ext)s',
        'nocheckcertificate': True,
        'http_headers': HEADERS
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    except Exception as e:
        print(f"[ERROR] al descargar ({platform}): {e}")
        return None
