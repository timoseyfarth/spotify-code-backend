from urllib.parse import urlparse

from data_transfer_objects import SpotifyType


def build_spotify_url(spotify_type: SpotifyType, spotify_id: str) -> str:
    return f"https://open.spotify.com/{spotify_type}/{spotify_id}"

def url_to_uri(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.split('/')
    return _build_spotify_uri(parts)

def _build_spotify_uri(parts: list[str]) -> str:
    if len(parts) < 3:
        raise ValueError("URL is not a valid Spotify resource. Expected format: https://open.spotify.com/<type>/<id>")

    spotify_type = parts[1]
    spotify_id = parts[2]
    return f"spotify:{spotify_type}:{spotify_id}".replace(":", "%3A")