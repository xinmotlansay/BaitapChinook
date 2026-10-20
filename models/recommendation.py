from dataclasses import dataclass, field

from models.album import Track


@dataclass
class Recommendation:
    album_id: int
    title: str
    artist: str
    genres: str
    score: float
    reasons: list[str] = field(default_factory=list)
    tracks: list[tuple[Track, float]] = field(default_factory=list)  # (track, điểm)
