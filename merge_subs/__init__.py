"""
merge_subs - Batch subtitle embedder for TV episodes and video files.

Embeds all matching subtitles into video files in-place using FFmpeg
without re-encoding.
"""

from __future__ import annotations

__version__ = "1.0.1"
__author__ = "Parth Pandit"

from merge_subs.config import (
    VIDEO_EXT,
    SUB_EXT,
    SUB_DIR_NAMES,
    FORMATS,
    LANGS,
    LOOKUP,
)
from merge_subs.episode import episodes, eps_match, norm
from merge_subs.matcher import Group, choose_group, find_groups, detect_lang
from merge_subs.track import build_tracks
from merge_subs.merger import merge_video, count_sub_streams
from merge_subs.discovery import find_ffmpeg, find_ffprobe

__all__ = [
    "__version__",
    "VIDEO_EXT",
    "SUB_EXT",
    "SUB_DIR_NAMES",
    "FORMATS",
    "LANGS",
    "LOOKUP",
    "episodes",
    "eps_match",
    "norm",
    "Group",
    "choose_group",
    "find_groups",
    "detect_lang",
    "build_tracks",
    "merge_video",
    "count_sub_streams",
    "find_ffmpeg",
    "find_ffprobe",
]
