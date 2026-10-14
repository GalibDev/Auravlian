"""Offline LRC parsing with repeated timestamps and signed global offsets."""
from bisect import bisect_right
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LyricLine:
    milliseconds: int
    text: str


def parse_lrc(text: str) -> list[LyricLine]:
    offset = re.search(r"\[offset:([+-]?\d+)\]", text, re.IGNORECASE)
    shift = int(offset[1]) if offset else 0
    result = []
    for line in text.splitlines():
        stamps = list(re.finditer(r"\[(\d+):([0-5]\d)(?:[.:](\d{1,3}))?\]", line))
        if not stamps:
            continue
        words = line[stamps[-1].end():].strip()
        for stamp in stamps:
            fraction = int((stamp[3] or "").ljust(3, "0"))
            result.append(LyricLine(max(0, (int(stamp[1]) * 60 + int(stamp[2])) * 1000 + fraction + shift), words))
    return sorted(result, key=lambda entry: entry.milliseconds)


def current_line(lines: list[LyricLine], position: int) -> int:
    return bisect_right(lines, position, key=lambda line: line.milliseconds) - 1
