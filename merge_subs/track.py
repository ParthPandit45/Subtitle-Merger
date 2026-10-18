"""Subtitle track metadata building, language tagging, and disposition sorting."""

import re
from pathlib import Path
from typing import TypedDict

from merge_subs.config import LOOKUP
from merge_subs.matcher import Group, detect_lang


class SubtitleTrack(TypedDict):
    path: Path
    lang3: str
    label: str
    forced: bool
    size: int
    default: bool


def build_tracks(group: Group, pref: str = "english") -> list[SubtitleTrack]:
    """
    Build subtitle track metadata from a group of subtitle files.

    Rules:
      - Preferred language track sorted first.
      - First non-forced preferred language track set as default.
      - Forced tracks are never default (unless all tracks are forced).
      - Duplicate track titles are numbered: "English", "English (2)", etc.
      - Tags like SDH and forced are extracted from filename tokens.
    """
    pref_name = pref.lower().strip()
    pref3 = LOOKUP.get(pref_name, (None, pref_name[:3]))[1]

    tracks: list[SubtitleTrack] = []
    for f in group.files:
        name, lang3 = detect_lang(f.stem)
        low_tokens = set(re.split(r"[^a-z0-9]+", f.stem.lower()))

        forced = "forced" in low_tokens
        if name:
            label = name.capitalize()
        else:
            cleaned = re.sub(r"^\d+[_\-. ]*", "", f.stem).replace("_", " ").strip()
            label = cleaned or f.stem

        if forced:
            label += " (forced)"
        elif low_tokens & {"sdh", "hi", "cc"}:
            label += " (SDH)"

        try:
            size = f.stat().st_size
        except OSError:
            size = 0

        tracks.append(
            {
                "path": f,
                "lang3": lang3,
                "label": label,
                "forced": forced,
                "size": size,
                "default": False,
            }
        )

    # Sort tracks: preferred language first, non-forced first, language code, largest file first
    tracks.sort(
        key=lambda t: (
            t["lang3"] != pref3,
            t["forced"],
            t["lang3"],
            -t["size"],
        )
    )

    # Disambiguate duplicate titles: "English", "English (2)", ...
    seen: dict[str, int] = {}
    for t in tracks:
        base_label = t["label"]
        seen[base_label] = seen.get(base_label, 0) + 1
        if seen[base_label] > 1:
            t["label"] = f"{base_label} ({seen[base_label]})"

    # Assign default flag
    for i, t in enumerate(tracks):
        t["default"] = (i == 0 and not t["forced"])

    if tracks and not any(t["default"] for t in tracks):
        tracks[0]["default"] = True

    return tracks
