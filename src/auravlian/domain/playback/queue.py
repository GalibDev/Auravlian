"""The only queue: pure Python, stable seeded shuffle and explicit completion rules."""
from random import Random
from collections.abc import Iterable

from auravlian.domain.models.track import Track
from auravlian.domain.playback.repeat_mode import RepeatMode


class PlaybackQueue:
    def __init__(self, seed: int = 0) -> None:
        self._tracks: tuple[Track, ...] = ()
        self._order: list[int] = []
        self._cursor = -1
        self.seed = seed
        self.shuffle = False
        self.repeat = RepeatMode.OFF

    @property
    def tracks(self) -> tuple[Track, ...]:
        return self._tracks

    @property
    def ordered_tracks(self) -> tuple[Track, ...]:
        return tuple(self._tracks[index] for index in self._order)

    @property
    def current(self) -> Track | None:
        return self._tracks[self._order[self._cursor]] if self._cursor >= 0 else None

    def replace(self, tracks: Iterable[Track]) -> None:
        self._tracks = tuple(tracks)
        self._order = list(range(len(self._tracks)))
        self._cursor = 0 if self._tracks else -1
        if self.shuffle:
            self._shuffle_remaining()

    def _shuffle_remaining(self) -> None:
        # Keep the active track anchored; visit every other track once per cycle.
        active = self._order[self._cursor] if self._cursor >= 0 else None
        remaining = [index for index in range(len(self._tracks)) if index != active]
        Random(self.seed).shuffle(remaining)
        self._order = ([active] if active is not None else []) + remaining
        self._cursor = 0 if self._order else -1

    def set_shuffle(self, enabled: bool) -> None:
        if self.shuffle == enabled:
            return
        self.shuffle = enabled
        if enabled:
            self._shuffle_remaining()
        else:
            active = self._order[self._cursor] if self._cursor >= 0 else -1
            self._order = list(range(len(self._tracks)))
            self._cursor = active

    def next(self, *, completed: bool = False) -> Track | None:
        if self.current is None:
            return None
        if completed and self.repeat == RepeatMode.ONE:
            return self.current
        if self._cursor + 1 < len(self._order):
            self._cursor += 1
        elif self.repeat == RepeatMode.ALL:
            self._cursor = 0
        else:
            return None
        return self.current

    def previous(self) -> Track | None:
        if self.current is None:
            return None
        if self._cursor > 0:
            self._cursor -= 1
        elif self.repeat == RepeatMode.ALL:
            self._cursor = len(self._order) - 1
        else:
            return None
        return self.current

    @property
    def can_next(self) -> bool:
        return bool(self._order) and (
            self._cursor + 1 < len(self._order) or self.repeat == RepeatMode.ALL)

    @property
    def can_previous(self) -> bool:
        return bool(self._order) and (self._cursor > 0 or self.repeat == RepeatMode.ALL)
