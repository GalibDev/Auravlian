"""Immutable local track snapshot shared by the library and playback queue."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Track:
    path: Path
    metadata_title: str = ""
    artist: str = "Unknown artist"
    album: str = "Unknown album"
    duration_ms: int = 0
    artwork_path: str = ""
    missing: bool = False

    @property
    def title(self) -> str:
        return self.metadata_title or self.path.stem
