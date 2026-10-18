"""Subtitle file grouping and video-to-subtitle matching logic."""

import difflib
import re
from pathlib import Path

from merge_subs.config import LOOKUP, SUB_DIR_NAMES, SUB_EXT
from merge_subs.episode import episodes, eps_match, norm


def detect_lang(stem: str) -> tuple[str | None, str]:
    """
    Detect language name and 3-letter ISO code from a filename stem.

    Returns:
      (canonical_name, iso3), e.g. ("english", "eng") or (None, "und")
    """
    tokens = re.split(r"[^a-z0-9]+", stem.lower())
    for tok in tokens:
        if tok in LOOKUP:
            return LOOKUP[tok]
    return None, "und"


class Group:
    """Represents a candidate group of subtitle files for an episode."""

    def __init__(self, name: str, files: list[Path]):
        self.name = name
        self.files = sorted(files)
        self.eps = episodes(name)
        if not self.eps:
            for f in files:
                self.eps |= episodes(f.stem)

    def __repr__(self) -> str:
        return f"Group(name={self.name!r}, eps={self.eps!r}, files={len(self.files)})"


def sub_files(folder: Path) -> list[Path]:
    """Recursively collect all subtitle files in folder."""
    return sorted(
        p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUB_EXT
    )


def groups_from_subs_dir(sd: Path) -> list[Group]:
    """Parse subtitle groups from a Subs/ directory (handles subfolders & loose files)."""
    groups: list[Group] = []
    try:
        children = sorted(sd.iterdir())
    except (PermissionError, FileNotFoundError):
        return groups

    for child in children:
        if child.is_dir():
            files = sub_files(child)
            if files:
                groups.append(Group(child.name, files))
        elif child.suffix.lower() in SUB_EXT:
            groups.append(Group(child.stem, [child]))
    return groups


def find_groups(
    video: Path, root: Path, cache: dict[tuple[Path, ...], list[Group]]
) -> list[Group]:
    """
    Ascend parent directories from video to find nearest Subs folder.
    Falls back to loose subtitles in the same directory as the video.
    """
    d = video.parent
    while True:
        try:
            subs_dirs = tuple(
                sorted(
                    c
                    for c in d.iterdir()
                    if c.is_dir() and c.name.lower() in SUB_DIR_NAMES
                )
            )
        except (PermissionError, FileNotFoundError):
            subs_dirs = ()

        if subs_dirs:
            if subs_dirs not in cache:
                cache[subs_dirs] = [
                    g for sd in subs_dirs for g in groups_from_subs_dir(sd)
                ]
            return cache[subs_dirs]

        if d == root or d.parent == d:
            break
        d = d.parent

    # Loose subtitle files in the video's directory
    try:
        return [
            Group(p.stem, [p])
            for p in sorted(video.parent.iterdir())
            if p.is_file() and p.suffix.lower() in SUB_EXT
        ]
    except (PermissionError, FileNotFoundError):
        return []


def choose_group(video: Path, groups: list[Group]) -> tuple[Group | None, str]:
    """
    Match a video to its corresponding subtitle group.

    Matching hierarchy:
      1. Exact normalized name match -> ("ok")
      2. Exact episode number set match -> ("ok")
      3. Partial episode match (e.g. 1 episode of double ep) -> ("partial")
      4. Fuzzy string match (ratio >= 0.75, when no episode info on either side) -> ("ok")
      5. Otherwise -> ("none")

    Returns:
      (matched_group, status) where status is "ok", "partial", or "none"
    """
    vname = norm(video.stem)
    veps = episodes(video.stem)

    best: Group | None = None
    best_score: tuple[int, float] = (-1, -1.0)

    for g in groups:
        if norm(g.name) == vname:
            return g, "ok"

        tier = eps_match(veps, g.eps)
        ratio = difflib.SequenceMatcher(None, vname, norm(g.name)).ratio()
        if (tier, ratio) > best_score:
            best, best_score = g, (tier, ratio)

    if best is None:
        return None, "none"

    tier, ratio = best_score
    if tier == 2:
        return best, "ok"
    if tier == 1:
        return best, "partial"
    if ratio >= 0.75 and (not veps or not best.eps):
        return best, "ok"

    return None, "none"
