import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os

# Configuración de Spotify
client_id = os.environ.get("SPOTIFY_CLIENT_ID")
client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise ValueError("❌ Faltan credenciales de Spotify")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

def search_spotify(query: str) -> list:
    try:
        results = sp.search(q=query, limit=5)
        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                "id": item['id'],
                "name": item['name'],
                "artist": item['artists'][0]['name']
            })
        return tracks
    except Exception as e:
        print(f"Error en Spotify: {e}")
        return []

def download_spotify_track(track_id: str) -> str:
    try:
        track_info = sp.track(track_id)
        query = f"{track_info['name']} {track_info['artists'][0]['name']}"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
    except Exception as e:
        print(f"Error al descargar de Spotify: {e}")
        return None
