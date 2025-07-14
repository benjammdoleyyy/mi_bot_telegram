import yt_dlp
import os

# Cabecera para evitar bloqueos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'
}

def get_youtube_formats(url: str) -> list:
    """
    Extrae una lista de formatos válidos para descarga desde YouTube,
    con audio y video combinados (progresivos).
    """
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

            for fmt in info.get("formats", []):
                if (
                    fmt.get("vcodec") != "none" and
                    fmt.get("acodec") != "none" and
                    fmt.get("height") and
                    fmt.get("ext") in ("mp4", "webm")
                ):
                    res = f"{fmt['height']}p"
                    if res not in seen_res:
                        seen_res.add(res)
                        formats.append({
                            "format_id": fmt["format_id"],
                            "resolution": res,
                            "ext": fmt["ext"]
                        })

            return formats[:6]
    except Exception as e:
        print(f"[ERROR] get_youtube_formats: {e}")
        return []

def download_youtube_video(url: str, format_id: str) -> str:
    """
    Descarga el video de YouTube en el formato especificado y devuelve
    la ruta absoluta al archivo descargado.
    """
    download_path = "downloads"
    os.makedirs(download_path, exist_ok=True)

    ydl_opts = {
        'quiet': True,
        'format': format_id,
        'outtmpl': f'{download_path}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'nocheckcertificate': True,
        'http_headers': HEADERS
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"[ERROR] download_youtube_video: {e}")
        return None
