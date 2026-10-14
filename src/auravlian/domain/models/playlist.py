from dataclasses import dataclass, field

from auravlian.domain.models.track import Track


@dataclass(frozen=True)
class Playlist:
    id: int
    name: str
    tracks: tuple[Track, ...] = ()


@dataclass
class CollectionSnapshot:
    playlists: list[Playlist] = field(default_factory=list)
    favorites: list[Track] = field(default_factory=list)
    history: list[Track] = field(default_factory=list)
    play_count: int = 0
