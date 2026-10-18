#!/usr/bin/env python3
"""
Automated PyInstaller build script for merge_subs.

Builds a self-contained, high-performance Windows executable (merge_subs.exe).
Optionally bundles ffmpeg.exe into the single-file binary.

Usage:
    python build_exe.py
    python build_exe.py --bundle-ffmpeg
    python build_exe.py --bundle-ffmpeg --ffmpeg-path "C:\\path\\to\\ffmpeg.exe"
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure merge_subs can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_subs.discovery import find_ffmpeg


def build_executable(bundle_ffmpeg: bool = False, ffmpeg_path: str | None = None) -> Path:
    """Build the standalone executable with PyInstaller."""
    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    spec_file = root_dir / "merge_subs.spec"

    print("=" * 60)
    print("Building standalone executable with PyInstaller...")
    print(f"Working directory: {root_dir}")
    print("=" * 60)

    # Base PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "merge_subs",
        "--exclude-module",
        "tkinter",
        "--exclude-module",
        "_tkinter",
        "--collect-all",
        "merge_subs",
    ]

    # Optional FFmpeg bundling
    if bundle_ffmpeg:
        target_ffmpeg = ffmpeg_path or find_ffmpeg()
        if not target_ffmpeg or not Path(target_ffmpeg).exists():
            print(f"Warning: ffmpeg binary '{target_ffmpeg}' not found. Skipping bundling.")
        else:
            print(f"Bundling FFmpeg binary: {target_ffmpeg}")
            cmd.extend(["--add-binary", f"{target_ffmpeg};."])

    cmd.append(str(root_dir / "merge_subs.py"))

    print(f"Executing: {' '.join(cmd)}\n")
    proc = subprocess.run(cmd, cwd=root_dir)
    if proc.returncode != 0:
        raise RuntimeError(f"PyInstaller build failed with exit code {proc.returncode}")

    exe_name = "merge_subs.exe" if os.name == "nt" else "merge_subs"
    exe_path = dist_dir / exe_name

    if not exe_path.exists():
        raise FileNotFoundError(f"Expected output binary not found at: {exe_path}")

    alt_exe_name = "Subtitle-Merger.exe" if os.name == "nt" else "Subtitle-Merger"
    alt_exe_path = dist_dir / alt_exe_name
    shutil.copy2(exe_path, alt_exe_path)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL!")
    print(f"Primary executable: {exe_path}")
    print(f"Alias executable:   {alt_exe_path}")
    print(f"Binary size:        {size_mb:.2f} MB")
    print("=" * 60)

    # Verification test
    print("\nVerifying executable with --help ...")
    test_proc = subprocess.run([str(exe_path), "--help"], capture_output=True, text=True)
    if test_proc.returncode == 0:
        print("Verification PASSED: Executable started and displayed help menu successfully.")
    else:
        print(f"Verification FAILED with return code {test_proc.returncode}:\n{test_proc.stderr}")

    return exe_path


def main():
    parser = argparse.ArgumentParser(description="Build merge_subs standalone executable.")
    parser.add_argument(
        "--bundle-ffmpeg",
        action="store_true",
        help="Bundle ffmpeg.exe directly inside the single-file executable",
    )
    parser.add_argument(
        "--ffmpeg-path",
        help="Explicit path to ffmpeg.exe when bundling",
    )
    args = parser.parse_args()

    try:
        build_executable(bundle_ffmpeg=args.bundle_ffmpeg, ffmpeg_path=args.ffmpeg_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
