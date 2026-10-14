# Pink desktop refresh

Implemented the supplied screenshot direction: light pink content surfaces, white
sidebar and player, dark outlines and text, rose controls and selection states.
The original Auravlian logo remains unchanged.

Playlists open in a wrapping artwork gallery with Create new, M3U import and a
playlist filter. Click a card to open its tracks; All playlists returns to the
gallery. Rename, Delete, Remove, reordering and export remain in the actions menu.
Favorites use a compact heart/artist/title/duration table with artwork, track
filter, play and a Library shortcut for adding favorites. Click a row heart to
remove it. The player heart toggles the currently imported track's favorite state;
it is disabled for tracks not yet imported and while collection operations run.

The persistent player has a full-width seek strip above its cover, track/artist,
icon transport controls, time, mute and volume. Tooltips and accessible names
identify icon actions; all controls still use the same playback engine. Existing
playback assertions now check icon tooltips instead of removed text labels.

Validation: Ruff passed; mypy passed for 75 source files. Initial full test run
passed 106 tests and found a new test's zero-pixel border assumption; adjusted
that assertion for Qt's styled frame border, then all 10 targeted collection and
playback tests passed. Preview screenshots were checked at 1440×900 and 960×700
logical pixels with isolated generated test media. Source playback smoke passed.
Portable EXE and installer were rebuilt; current binary hashes are recorded in
`dist/SHA256SUMS.txt`. No clean VM or human listening test was performed.

Final full run: `python -m pytest -q` — **107 passed in 25.57s**.
Rebuilt portable `--smoke-test` passed: 5000 ms duration, pause/seek to 1500 ms,
one imported track/history start, decoded buffers captured and two local lyric lines.
