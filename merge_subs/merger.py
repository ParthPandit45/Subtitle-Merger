"""FFmpeg stream-copy merging engine with verification and in-place replacement."""

from __future__ import annotations

import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable

from merge_subs.config import FORMATS
from merge_subs.track import SubtitleTrack
from merge_subs.utils import count_sub_streams, fast_validate_subtitle, to_utf8

logger = logging.getLogger("merge_subs.merger")


def build_ffmpeg_command(
    video: Path,
    usable_tracks: list[tuple[SubtitleTrack, Path, str]],
    tmp_out: Path,
    fmt: str,
    pre_sub_count: int,
    default_idx: int,
    ffmpeg_bin: str,
) -> list[str]:
    """Assemble lossless FFmpeg stream-copy command."""
    cmd = [ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error", "-i", str(video)]

    for _, sub_path, _ in usable_tracks:
        cmd.extend(["-i", str(sub_path)])

    # Map existing video, audio, subtitles, and chapters
    cmd.extend(["-map", "0:v", "-map", "0:a?", "-map", "0:s?"])

    for k in range(len(usable_tracks)):
        cmd.extend(["-map", f"{k + 1}:0"])

    cmd.extend(["-map_chapters", "0", "-c", "copy"])

    # Configure each newly appended subtitle track
    for k, (t, _, codec) in enumerate(usable_tracks):
        stream_idx = pre_sub_count + k
        cmd.extend(
            [
                f"-c:s:{stream_idx}",
                codec,
                f"-metadata:s:s:{stream_idx}",
                f"language={t['lang3']}",
                f"-metadata:s:s:{stream_idx}",
                f"title={t['label']}",
                f"-disposition:s:{stream_idx}",
                "default" if k == default_idx else "0",
            ]
        )

    # For MP4 containers, optimize MOOV atom placement for instant seeking
    if fmt in {"mp4", "mov"}:
        cmd.extend(["-movflags", "+faststart"])

    cmd.extend(["-f", fmt, str(tmp_out)])
    return cmd


def _merge_video_impl(
    video: Path,
    tracks: list[SubtitleTrack],
    ffmpeg_bin: str,
    ffprobe_bin: str | None = None,
    pre_sub_count: int | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> tuple[bool, str, Path | None]:
    """Internal implementation of merge logic."""
    ext = video.suffix.lower()
    fmt = FORMATS.get(ext)
    final = video
    if fmt is None:
        # Containers like AVI, WMV that cannot host soft subtitles are converted to Matroska (.mkv)
        fmt, final = "matroska", video.with_suffix(".mkv")
    is_mp4 = fmt in {"mp4", "mov"}

    if pre_sub_count is None:
        pre_sub_count = count_sub_streams(video, ffmpeg_bin, ffprobe_bin)

    tmp_out = video.with_name(video.name + ".part")

    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        usable: list[tuple[SubtitleTrack, Path, str]] = []

        for k, t in enumerate(tracks):
            src = t["path"]
            sext = src.suffix.lower()

            if sext == ".sub" and src.with_suffix(".idx").exists():
                # VobSub image-based subtitle pair
                if is_mp4:
                    msg = f"skipped image-based subtitle (not supported in {ext}): {src.name}"
                    if log_fn:
                        log_fn(msg)
                    logger.warning(msg)
                    continue
                p, codec = src.with_suffix(".idx"), "copy"
            else:
                codec = (
                    "mov_text"
                    if is_mp4
                    else ("ass" if sext in {".ass", ".ssa"} else "srt")
                )
                p = to_utf8(src, temp_dir / f"{k}{sext}")

            if not fast_validate_subtitle(p, ffmpeg_bin):
                msg = f"skipped unreadable subtitle: {src.name}"
                if log_fn:
                    log_fn(msg)
                logger.warning(msg)
                continue

            usable.append((t, p, codec))

        if not usable:
            return False, "no usable subtitles found", None

        default_idx = next(
            (i for i, (t, _, _) in enumerate(usable) if t["default"]), 0
        )

        cmd = build_ffmpeg_command(
            video=video,
            usable_tracks=usable,
            tmp_out=tmp_out,
            fmt=fmt,
            pre_sub_count=pre_sub_count,
            default_idx=default_idx,
            ffmpeg_bin=ffmpeg_bin,
        )

        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                errors="replace",
            )
        except Exception as e:
            return False, f"FFmpeg execution failed: {e}", None

    last_err = (r.stderr.strip().splitlines() or [""])[-1]
    if r.returncode != 0:
        return False, last_err or "ffmpeg failed", None

    # --- Verification checks before replacing original ---
    if not tmp_out.exists() or tmp_out.stat().st_size == 0:
        return (
            False,
            "ffmpeg finished but output file is missing (antivirus or indexer may have locked/removed it)"
            + (f": {last_err}" if last_err else ""),
            None,
        )

    orig_size = video.stat().st_size
    if tmp_out.stat().st_size < 0.8 * orig_size:
        return (
            False,
            f"merged file is unexpectedly small ({tmp_out.stat().st_size} vs {orig_size} bytes); original preserved",
            None,
        )

    out_subs = count_sub_streams(tmp_out, ffmpeg_bin, ffprobe_bin)
    expected_subs = pre_sub_count + len(usable)
    if out_subs < expected_subs:
        return (
            False,
            f"merged file contains {out_subs} subtitle tracks, expected {expected_subs}; original preserved",
            None,
        )

    # --- Atomic in-place swap with retry loop for Windows file locks ---
    for _ in range(10):
        try:
            tmp_out.replace(final)
            break
        except PermissionError:
            time.sleep(1.5)
        except FileNotFoundError:
            return (
                False,
                "temporary file disappeared before swap could complete",
                None,
            )
    else:
        return (
            False,
            "could not replace original file (file in use by media player or indexer)",
            None,
        )

    # If container format changed (e.g. .avi -> .mkv), clean up original file
    if final != video and video.exists():
        try:
            video.unlink()
        except OSError:
            pass

    return True, "", final


def merge_video(
    video: Path,
    tracks: list[SubtitleTrack],
    ffmpeg_bin: str,
    ffprobe_bin: str | None = None,
    pre_sub_count: int | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> tuple[bool, str, Path | None]:
    """
    Safely merge subtitle tracks into video in place.
    Ensures .part file is always cleaned up on errors or interruptions.
    """
    try:
        return _merge_video_impl(
            video=video,
            tracks=tracks,
            ffmpeg_bin=ffmpeg_bin,
            ffprobe_bin=ffprobe_bin,
            pre_sub_count=pre_sub_count,
            log_fn=log_fn,
        )
    finally:
        # Guarantee removal of temporary .part file
        part_path = video.with_name(video.name + ".part")
        if part_path.exists():
            try:
                part_path.unlink()
            except OSError:
                pass
