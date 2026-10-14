import base64
import json
import logging
from pathlib import Path
from typing import Any

import mutagen  # type: ignore[import-untyped]

from auravlian.domain.models.track import Track
from auravlian.infrastructure.cache.artwork_cache import ArtworkCache


def _text(tags: Any, *keys: str) -> str:
    for key in keys:
        value = tags.get(key) if tags else None
        if value:
            return str(value[0] if isinstance(value, list) else value).strip()
    return ""


def _artwork(audio: Any) -> bytes:
    pictures = getattr(audio, "pictures", [])
    if pictures:
        return bytes(pictures[0].data)
    tags = audio.tags
    if not tags:
        return b""
    for key, value in tags.items():
        if str(key).startswith("APIC"):
            return bytes(value.data)
    covers = tags.get("covr")
    if covers:
        return bytes(covers[0])
    blocks = tags.get("metadata_block_picture")
    if blocks:
        from mutagen.flac import Picture
        return bytes(Picture(base64.b64decode(blocks[0])).data)
    return b""


def read_track(path: Path, cache: ArtworkCache) -> Track:
    audio = mutagen.File(path)
    if audio is None:
        raise ValueError("Unsupported or unreadable audio format")
    tags = audio.tags
    title = _text(tags, "TIT2", "title", "\xa9nam", "Title")
    artist = _text(tags, "TPE1", "artist", "\xa9ART", "Author") or "Unknown artist"
    album = _text(tags, "TALB", "album", "\xa9alb", "WM/AlbumTitle") or "Unknown album"
    cached = ""
    try:
        artwork = _artwork(audio)
        cached = cache.store(artwork) if artwork else ""
    except Exception as exc:
        logging.getLogger("auravlian").warning(json.dumps(f"Artwork unavailable for {path.name}: {exc}"))
    return Track(path.resolve(), title, artist, album,
                 max(0, int(getattr(audio.info, "length", 0) * 1000)), cached)
