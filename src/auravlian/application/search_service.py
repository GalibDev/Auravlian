from auravlian.domain.models.track import Track


def matches(track: Track, query: str) -> bool:
    """All whitespace-separated words must occur in title, artist or album."""
    text = f"{track.title} {track.artist} {track.album}".casefold()
    return all(word in text for word in query.casefold().split())
