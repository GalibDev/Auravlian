from pathlib import Path
import os
import tempfile

from auravlian.domain.models.track import Track


def read_m3u(path: Path) -> list[Path]:
    if path.stat().st_size > 5_000_000:
        raise ValueError("Playlist exceeds the 5 MB limit.")
    result = []
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        if "://" in entry:
            raise ValueError("Only local file paths are supported in offline playlists.")
        media = Path(entry)
        result.append(media if media.is_absolute() else path.parent / media)
    return result


def write_m3u(path: Path, tracks: tuple[Track, ...]) -> None:
    lines = ["#EXTM3U"]
    for track in tracks:
        title = track.title.replace("\n", " ").replace("\r", " ")
        lines.extend([f"#EXTINF:{track.duration_ms // 1000},{title}", str(track.path.resolve())])
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write("\n".join(lines) + "\n")
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
