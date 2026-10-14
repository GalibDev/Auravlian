from pathlib import Path

import pytest

from auravlian.domain.models.track import Track
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.domain.playback.repeat_mode import RepeatMode


def make_queue(count=5, seed=42):
    queue = PlaybackQueue(seed)
    queue.replace(Track(Path(f"{index}.wav")) for index in range(count))
    return queue


def test_empty_queue():
    queue = make_queue(0)
    assert queue.current is None
    assert queue.next() is None
    assert queue.previous() is None
    assert not queue.can_next and not queue.can_previous
    queue.set_shuffle(True)
    queue.set_shuffle(False)
    assert queue.ordered_tracks == ()


def test_order_boundaries_and_previous():
    queue = make_queue(3)
    assert queue.current == queue.tracks[0]
    assert queue.previous() is None
    assert queue.next() == queue.tracks[1]
    assert queue.next() == queue.tracks[2]
    assert queue.next() is None
    assert queue.current == queue.tracks[2]
    assert queue.previous() == queue.tracks[1]


@pytest.mark.parametrize("mode", RepeatMode)
def test_completion_rules(mode):
    queue = make_queue(1)
    queue.repeat = mode
    expected = None if mode == RepeatMode.OFF else queue.current
    assert queue.next(completed=True) == expected


def test_repeat_one_does_not_trap_manual_next():
    queue = make_queue(2)
    queue.repeat = RepeatMode.ONE
    assert queue.next(completed=True) == queue.tracks[0]
    assert queue.next() == queue.tracks[1]
    assert queue.next() is None


def test_repeat_all_wraps_both_directions():
    queue = make_queue(2)
    queue.repeat = RepeatMode.ALL
    assert queue.previous() == queue.tracks[1]
    assert queue.next() == queue.tracks[0]


def test_seeded_shuffle_is_deterministic_and_unique():
    a, b = make_queue(20), make_queue(20)
    a.set_shuffle(True)
    b.set_shuffle(True)
    assert a.ordered_tracks == b.ordered_tracks
    assert a.current == a.tracks[0]
    assert a.ordered_tracks != a.tracks
    visited = [a.current]
    while (track := a.next()) is not None:
        visited.append(track)
    assert len(set(visited)) == len(a.tracks)


def test_shuffle_toggle_keeps_current_and_restores_original_order():
    queue = make_queue()
    queue.next()
    current = queue.current
    queue.set_shuffle(True)
    assert queue.current == current
    queue.set_shuffle(True)
    assert queue.current == current
    queue.next()
    current = queue.current
    queue.set_shuffle(False)
    assert queue.current == current
    assert queue.ordered_tracks == queue.tracks


def test_replacement_clears_old_order():
    queue = make_queue()
    queue.set_shuffle(True)
    queue.replace([Track(Path("new.wav"))])
    assert queue.current.title == "new"
    assert len(queue.ordered_tracks) == 1
    queue.replace([])
    assert queue.current is None
