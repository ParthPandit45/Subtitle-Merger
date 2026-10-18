"""Episode parsing and title normalization."""

import re

# S03E01, S04E01E02, S03E12-13, S01E01-E04
SE = re.compile(
    r"(?<![a-z0-9])s(\d{1,2})[ ._-]?e(\d{1,3})((?:[ ._-]?(?:e|-e?)\d{1,2}(?!\d))*)",
    re.I,
)
# 3x05, 12x08
NX = re.compile(r"(?<![a-z0-9])(\d{1,2})x(\d{2,3})(?!\d)", re.I)
# Episode 5, Ep. 05, E05
EP = re.compile(r"(?<![a-z0-9])(?:episode|ep|e)[ ._-]?(\d{1,3})(?!\d)", re.I)


def episodes(text: str) -> set[tuple[int | None, int]]:
    """
    Extract set of (season, episode) pairs from a string.

    Supports:
      - Standard: S03E01, S3E1
      - Multi-episode: S03E01E02, S03E12-13, S03E12-E14
      - X-notation: 3x05
      - Lone episode notation: Episode 5, Ep.05, E05
    """
    eps: set[tuple[int | None, int]] = set()

    # Try SxxExx first
    for m in SE.finditer(text):
        s = int(m.group(1))
        prev = int(m.group(2))
        eps.add((s, prev))
        extra = m.group(3)
        if extra:
            for dash, num in re.findall(r"(-)?e?(\d{1,2})", extra, re.I):
                n = int(num)
                if dash and prev < n <= prev + 10:
                    eps.update((s, k) for k in range(prev + 1, n + 1))
                else:
                    eps.add((s, n))
                prev = n

    if eps:
        return eps

    # Try NxNN (e.g. 3x05)
    eps = {(int(m.group(1)), int(m.group(2))) for m in NX.finditer(text)}
    if eps:
        return eps

    # Try loose episode tags (e.g. Episode 5)
    return {(None, int(m.group(1))) for m in EP.finditer(text)}


def eps_match(a: set[tuple[int | None, int]], b: set[tuple[int | None, int]]) -> int:
    """
    Compare two sets of episode tuples.

    Returns:
      2: Exact match (all episodes match)
      1: Partial match (subset / overlap, e.g. multi-episode mismatch)
      0: No match or empty
    """
    if not a or not b:
        return 0

    # If season is missing on either side, compare episode numbers only
    if any(s is None for s, _ in a | b):
        a_eps = {e for _, e in a}
        b_eps = {e for _, e in b}
    else:
        a_eps = a
        b_eps = b

    if a_eps == b_eps:
        return 2
    if a_eps & b_eps:
        return 1
    return 0


def norm(s: str) -> str:
    """Normalize string by lowercasing and replacing non-alphanumeric chars with spaces."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
