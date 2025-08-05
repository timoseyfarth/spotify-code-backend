from dataclasses import dataclass
from enum import Enum


@dataclass
class ColorDTO:
    rgb: tuple
    hex: str
    name: str

@dataclass
class AlbumImageColorDTO:
    accent_color: ColorDTO
    code_color: ColorDTO

@dataclass
class SpotifyCodeBarsDTO:
    data_bars: list[int]
    octal_part1: int
    octal_part2: int

@dataclass
class SpotifyCodeDTO:
    job_id: str
    title: str
    type: str
    spotify_id: str
    spotify_url: str
    bars: SpotifyCodeBarsDTO
    album_image_color: AlbumImageColorDTO

class SpotifyType(str, Enum):
    TRACK = "track"
    ALBUM = "album"
    EPISODE = "episode"
    PLAYLIST = "playlist"
