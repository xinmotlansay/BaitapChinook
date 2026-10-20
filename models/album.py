from dataclasses import dataclass


@dataclass
class Track:
    track_id: int
    name: str
    album_id: int
    genre: str
    composer: str
    milliseconds: int
    unit_price: float


@dataclass
class Album:
    album_id: int
    title: str
    artist: str
    genres: str
