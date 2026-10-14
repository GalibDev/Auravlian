"""Every operation owns and closes its connection on the calling thread."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from collections.abc import Iterator


@contextmanager
def connection(path: Path) -> Iterator[sqlite3.Connection]:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        with db:
            yield db
    finally:
        db.close()
