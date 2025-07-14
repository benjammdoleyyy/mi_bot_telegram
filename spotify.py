import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os

# Configura las credenciales de Spotify (obtén las tuyas en https://developer.spotify.com/dashboard)
client_id = os.environ.get("SPOTIFY_CLIENT_ID")
client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

def search_spotify(query: str) -> list:
    results = sp.search(q=query, limit=5)
    tracks = []
    for item in results['tracks']['items']:
        tracks.append({
            "id": item['id'],
            "name": item['name'],
            "artist": item['artists'][0]['name']
        })
    return tracks

def download_spotify_track(track_id: str) -> str:
    track_info = sp.track(track_id)
    query = f"{track_info['name']} {track_info['artists'][0]['name']}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
    except:
        return None


