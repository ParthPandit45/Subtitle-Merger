"""Command-line interface and batch orchestration for merge_subs."""

import argparse
import concurrent.futures
import os
import sys
import threading
import time
from pathlib import Path

from merge_subs.config import SUB_DIR_NAMES, VIDEO_EXT
from merge_subs.discovery import find_ffmpeg, find_ffprobe
from merge_subs.matcher import choose_group, find_groups
from merge_subs.merger import merge_video
from merge_subs.track import build_tracks
from merge_subs.utils import cleanup_stale_parts, count_sub_streams


class SafePrinter:
    """Thread-safe synchronized printer with optional color support."""

    def __init__(self, use_colors: bool = True):
        self.lock = threading.Lock()
        self.use_colors = use_colors and sys.stdout.isatty()

    def print(self, message: str, flush: bool = True) -> None:
        with self.lock:
            print(message, flush=flush)

    def status(
        self,
        idx: int,
        total: int,
        action: str,
        rel_path: Path | str,
        extra: str = "",
        color: str | None = None,
    ) -> None:
        with self.lock:
            tag = f"[{idx}/{total}]"
            color_start = ""
            color_end = ""
            if self.use_colors and color:
                colors = {
                    "green": "\033[92m",
                    "yellow": "\033[93m",
                    "red": "\033[91m",
                    "cyan": "\033[96m",
                    "bold": "\033[1m",
                }
                color_start = colors.get(color, "")
                color_end = "\033[0m"

            act_str = f"{color_start}{action:<7}{color_end}"
            msg = f"{tag} {act_str} {rel_path}"
            if extra:
                msg += f"  ({extra})"
            print(msg, flush=True)


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Configure and parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="merge_subs",
        description="Losslessly embed matching subtitles into TV episodes and video files in place.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "root",
        nargs="?",
        help="Folder containing videos and subtitle directories (omitting opens a folder dialog)",
    )
    parser.add_argument(
        "--lang",
        default="english",
        help="Preferred default subtitle language track",
    )
    parser.add_argument(
        "--ffmpeg",
        help="Path to ffmpeg executable if not in PATH or auto-discovered",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=min(os.cpu_count() or 1, 4),
        help="Number of concurrent worker threads for parallel remuxing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview matching subtitles and tracks without modifying files",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force re-processing of files that already have subtitle tracks",
    )
    return parser.parse_args(argv)


from merge_subs.ui import pick_folder


def process_video_item(
    item: tuple[int, Path],
    total: int,
    root: Path,
    ffmpeg_bin: str,
    ffprobe_bin: str | None,
    preferred_lang: str,
    group_cache: dict,
    cache_lock: threading.Lock,
    printer: SafePrinter,
    dry_run: bool = False,
    force: bool = False,
) -> str:
    """
    Process an individual video file.

    Returns: "merged" | "skipped" | "failed"
    """
    idx, video = item
    rel = video.relative_to(root)

    # 1. Check existing subtitle streams
    sub_count = count_sub_streams(video, ffmpeg_bin, ffprobe_bin)
    if sub_count > 0 and not force:
        printer.status(
            idx,
            total,
            "SKIP",
            rel,
            extra=f"{sub_count} stream(s) already embedded",
            color="yellow",
        )
        return "skipped"

    # 2. Locate subtitle groups
    with cache_lock:
        groups = find_groups(video, root, group_cache)

    group, status = choose_group(video, groups) if groups else (None, "none")
    if status != "ok":
        why = (
            "no matching subtitles"
            if status == "none"
            else f"subs '{group.name}' cover only part of this multi-episode file"
        )
        printer.status(idx, total, "FAIL", rel, extra=why, color="red")
        return "failed"

    tracks = build_tracks(group, preferred_lang)
    if not tracks:
        printer.status(
            idx, total, "FAIL", rel, extra="no valid subtitle tracks found", color="red"
        )
        return "failed"

    track_desc = f"{len(tracks)} track(s): " + ", ".join(t["label"] for t in tracks[:3])
    if len(tracks) > 3:
        track_desc += f", +{len(tracks) - 3} more"

    if dry_run:
        printer.status(
            idx,
            total,
            "PLAN",
            rel,
            extra=f"Would embed {track_desc}",
            color="cyan",
        )
        return "merged"

    printer.status(
        idx,
        total,
        "MERGE",
        rel,
        extra=f"Embedding {track_desc}...",
        color="cyan",
    )

    try:
        ok, err, _ = merge_video(
            video=video,
            tracks=tracks,
            ffmpeg_bin=ffmpeg_bin,
            ffprobe_bin=ffprobe_bin,
            pre_sub_count=sub_count,
            log_fn=lambda m: printer.print(f"          {m}"),
        )
    except Exception as e:
        ok, err = False, f"{type(e).__name__}: {e}"

    if ok:
        printer.status(
            idx,
            total,
            "DONE",
            rel,
            extra=f"Embedded {len(tracks)} tracks",
            color="green",
        )
        return "merged"
    else:
        printer.status(idx, total, "FAIL", rel, extra=err, color="red")
        return "failed"


def main(argv: list[str] | None = None) -> int:
    """Main orchestrator entry point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    args = parse_arguments(argv)
    interactive = args.root is None

    folder_path = args.root
    if interactive:
        folder_path = prompt_for_folder()

    if not folder_path:
        print("No folder selected. Exiting.")
        return 1

    root = Path(folder_path).expanduser().resolve()
    if not root.is_dir():
        print(f"Error: '{root}' is not a valid directory.")
        return 1

    # Discover FFmpeg and FFprobe
    search_dirs = [root, root.parent]
    ffmpeg_bin = find_ffmpeg(
        extra_dirs=search_dirs,
        cli_path=args.ffmpeg,
        interactive=interactive,
    )
    if not ffmpeg_bin:
        print(
            "Error: FFmpeg not found.\n"
            "Please install FFmpeg (e.g. 'winget install Gyan.FFmpeg') or pass --ffmpeg <path>."
        )
        return 1

    ffprobe_bin = find_ffprobe(ffmpeg_bin)
    print(f"FFmpeg binary: {ffmpeg_bin}")
    if ffprobe_bin:
        print(f"FFprobe binary: {ffprobe_bin}")
    if args.dry_run:
        print("[DRY-RUN MODE] No files will be modified.")

    # Clean leftover .part files
    stale_count = cleanup_stale_parts(root)
    if stale_count > 0:
        print(f"Cleaned up {stale_count} stale .part file(s) from previous interrupted runs.")

    # Collect video files excluding sample clips and subs folders
    videos = sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in VIDEO_EXT
        and not any(part.lower() in SUB_DIR_NAMES for part in p.relative_to(root).parts)
        and "sample" not in p.name.lower()
    )

    if not videos:
        print(f"No video files found in '{root}'.")
        return 0

    total = len(videos)
    jobs = max(1, args.jobs)
    print(
        f"Found {total} video(s). Processing with {jobs} worker(s)... (Preferred language: {args.lang})\n"
    )

    printer = SafePrinter()
    group_cache: dict = {}
    cache_lock = threading.Lock()

    merged_count = 0
    skipped_count = 0
    failed_count = 0
    start_time = time.time()

    indexed_videos = list(enumerate(videos, start=1))

    if jobs == 1:
        for item in indexed_videos:
            res = process_video_item(
                item=item,
                total=total,
                root=root,
                ffmpeg_bin=ffmpeg_bin,
                ffprobe_bin=ffprobe_bin,
                preferred_lang=args.lang,
                group_cache=group_cache,
                cache_lock=cache_lock,
                printer=printer,
                dry_run=args.dry_run,
                force=args.force,
            )
            if res == "merged":
                merged_count += 1
            elif res == "skipped":
                skipped_count += 1
            else:
                failed_count += 1
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
            future_to_item = {
                executor.submit(
                    process_video_item,
                    item,
                    total,
                    root,
                    ffmpeg_bin,
                    ffprobe_bin,
                    args.lang,
                    group_cache,
                    cache_lock,
                    printer,
                    args.dry_run,
                    args.force,
                ): item
                for item in indexed_videos
            }
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    res = future.result()
                    if res == "merged":
                        merged_count += 1
                    elif res == "skipped":
                        skipped_count += 1
                    else:
                        failed_count += 1
                except Exception as exc:
                    item = future_to_item[future]
                    printer.print(f"Worker exception processing {item[1].name}: {exc}")
                    failed_count += 1

    elapsed = time.time() - start_time
    print(
        f"\nSummary: {merged_count} merged, {skipped_count} skipped, {failed_count} failed in {elapsed:.1f}s."
    )

    if interactive:
        try:
            input("\nPress Enter to close...")
        except (EOFError, KeyboardInterrupt):
            pass

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
