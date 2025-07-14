import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import logging
from typing import List, Dict, Optional
from urllib.parse import quote
from utils import DownloadError, sanitize_filename

# Configuración
logger = logging.getLogger(__name__)

# Validar credenciales
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET]):
    raise ValueError("❌ Faltan credenciales de Spotify")

# Configurar Spotipy
auth_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=auth_manager)

def search_spotify(query: str) -> List[Dict]:
    try:
        results = sp.search(q=query, limit=5, type='track')
        return [{
            "id": item['id'],
            "name": item['name'],
            "artist": item['artists'][0]['name'],
            "album": item['album']['name'],
            "duration": item['duration_ms'] // 1000
        } for item in results['tracks']['items']]
    except Exception as e:
        logger.error(f"Spotify search error: {str(e)}")
        raise DownloadError("Error al buscar en Spotify")

def download_spotify_track(track_id: str) -> str:
    try:
        track = sp.track(track_id)
        search_query = f"{track['name']} {track['artists'][0]['name']} official audio"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }],
            'writethumbnail': True,
            'embedthumbnail': True,
            'quiet': False,
            'no_warnings': False,
            'default_search': 'ytsearch',
            'noplaylist': True,
            'extract_flat': False,
            'socket_timeout': 15,
            'retries': 3,
        }

        # Configurar metadatos
        metadata = {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'track_number': str(track['track_number']),
            'release_date': track['album']['release_date'],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=True)
            filename = ydl.prepare_filename(info)
            
            # Asegurar extensión .mp3
            base, _ = os.path.splitext(filename)
            mp3_file = f"{base}.mp3"
            
            if not os.path.exists(mp3_file):
                raise DownloadError("No se pudo convertir a MP3")
            
            return mp3_file

    except yt_dlp.DownloadError as e:
        logger.error(f"YTDL Error: {str(e)}")
        raise DownloadError("Error al descargar el audio")
    except Exception as e:
        logger.error(f"Spotify download error: {str(e)}")
        raise DownloadError("Error inesperado al procesar la canción")
