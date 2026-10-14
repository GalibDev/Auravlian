"""Minimal local track identity; metadata import belongs to Phase 3."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Track:
    path: Path

    @property
    def title(self) -> str:
        return self.path.stem
