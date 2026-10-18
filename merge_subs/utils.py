"""File utilities, fast subtitle validation, encoding, and stream counting."""

import re
import subprocess
from pathlib import Path

from merge_subs.config import VIDEO_EXT


def to_utf8(sub: Path, dest: Path) -> Path:
    """
    Ensure subtitle text is converted to clean UTF-8 without BOM.
    Tries utf-8-sig, utf-8, then falls back to cp1252 / latin-1.
    """
    raw = sub.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")

    dest.write_text(text, encoding="utf-8")
    return dest


def fast_validate_subtitle(sub: Path, ffmpeg_bin: str | None = None) -> bool:
    """
    Validate subtitle file. Uses fast in-memory heuristic for common text formats
    to avoid spawning unnecessary FFmpeg subprocesses, falling back to FFmpeg if needed.
    """
    if not sub.exists() or sub.stat().st_size == 0:
        return False

    ext = sub.suffix.lower()

    # Fast validation for text formats (.srt, .vtt, .ass, .ssa)
    if ext in {".srt", ".vtt", ".ass", ".ssa"}:
        try:
            with open(sub, "rb") as f:
                header = f.read(4096)

            try:
                text = header.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = header.decode("cp1252", errors="replace")

            if ext == ".srt" and ("-->" in text or re.search(r"\d+\r?\n\d{2}:", text)):
                return True
            if ext == ".vtt" and ("WEBVTT" in text or "-->" in text):
                return True
            if ext in {".ass", ".ssa"} and (
                "[Script Info]" in text or "Dialogue:" in text or "Format:" in text
            ):
                return True
        except Exception:
            pass

    # If heuristic didn't conclusively validate, or format is binary (VobSub .idx), test with FFmpeg
    if ffmpeg_bin:
        try:
            r = subprocess.run(
                [
                    ffmpeg_bin,
                    "-v",
                    "error",
                    "-i",
                    str(sub),
                    "-map",
                    "0:s:0",
                    "-c:s",
                    "copy",
                    "-f",
                    "null",
                    "-",
                ],
                capture_output=True,
                timeout=5,
            )
            return r.returncode == 0
        except Exception:
            return False

    return ext in {".srt", ".vtt", ".ass", ".ssa", ".sub"}


def count_sub_streams(
    video: Path, ffmpeg_bin: str, ffprobe_bin: str | None = None
) -> int:
    """
    Count existing subtitle streams in video.
    Prefers ffprobe for speed, falls back to ffmpeg.
    """
    if ffprobe_bin:
        try:
            r = subprocess.run(
                [
                    ffprobe_bin,
                    "-v",
                    "error",
                    "-select_streams",
                    "s",
                    "-show_entries",
                    "stream=index",
                    "-of",
                    "csv=p=0",
                    str(video),
                ],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=6,
            )
            if r.returncode == 0:
                return len([line for line in r.stdout.strip().splitlines() if line.strip()])
        except Exception:
            pass

    try:
        r = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-i", str(video)],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=8,
        )
        return len(re.findall(r"Stream #\d+:\d+.*?: Subtitle", r.stderr))
    except Exception:
        return 0


def cleanup_stale_parts(root: Path) -> int:
    """Find and clean up any leftover .part files from previous interrupted runs."""
    cleaned = 0
    try:
        for stale in root.rglob("*.part"):
            if stale.is_file() and Path(stale.stem).suffix.lower() in VIDEO_EXT:
                try:
                    stale.unlink(missing_ok=True)
                    cleaned += 1
                except OSError:
                    pass
    except (PermissionError, FileNotFoundError):
        pass
    return cleaned
