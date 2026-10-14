import os
from pathlib import Path
from collections.abc import Callable, Iterator, Iterable
from threading import Event

from auravlian.infrastructure.database.repositories.library_repository import normalized

AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".aiff", ".aif"}


def scan(paths: Iterable[Path], cancelled: Event,
         report: Callable[[str], None]) -> Iterator[Path]:
    seen: set[str] = set()
    for source in paths:
        if cancelled.is_set():
            return
        try:
            if source.is_dir():
                for root, _, names in os.walk(source, followlinks=False,
                                              onerror=lambda exc: report(str(exc))):
                    for name in sorted(names):
                        if cancelled.is_set():
                            return
                        path = Path(root) / name
                        if path.suffix.lower() in AUDIO_EXTENSIONS:
                            key = normalized(path)
                            if key not in seen:
                                seen.add(key)
                                yield path
            elif source.is_file() and source.suffix.lower() in AUDIO_EXTENSIONS:
                key = normalized(source)
                if key not in seen:
                    seen.add(key)
                    yield source
            else:
                report(f"Unavailable or unsupported path: {source}")
        except (OSError, ValueError) as exc:
            report(f"Cannot scan {source}: {exc}")
