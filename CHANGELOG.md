# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-18

### Added
- **Core CLI**: High-performance batch subtitle embedder for TV shows and video files.
- **Multithreading**: Concurrent episode processing via `--jobs N` (default 4 threads) for maximum SSD/NVMe utilization.
- **Matching Engine**: Multi-tiered matching supporting `S01E01`, `3x05`, `Episode 5`, multi-episode ranges (`S03E12E13`, `S03E12-14`), and fuzzy fallback.
- **Partial Multi-Episode Safety Guard**: Detects if subtitles only cover part of a double episode and flags as failed rather than embedding wrong subs.
- **In-Memory Subtitle Validation**: Zero-overhead header and timestamp integrity checking for `.srt`, `.vtt`, `.ass`, `.ssa`.
- **Lossless FFmpeg Stream Copy**: Remuxes containers (`.mp4`, `.mkv`, `.m4v`, `.mov`) without video/audio re-encoding (`-c copy`).
- **Metadata & Disposition**: Language code detection across 35+ languages, custom titles (`English (forced)`, `English (SDH)`), and default disposition sorting.
- **Atomic File Operations**: Safe in-place replacement via `.part` files with output stream verification, 80% file size guard, and Windows file-lock exponential backoff retries.
- **FFmpeg Auto-Discovery**: Comprehensive search covering `--ffmpeg`, `FFMPEG_PATH`, `PATH`, WinGet, Scoop, Chocolatey, local folders, and interactive folder picker fallback.
- **Standalone Windows Executable**: Automated PyInstaller builder script `build_exe.py` producing single-file executable `dist/merge_subs.exe`.
- **Native GUI Fallback**: Tkinter / PowerShell folder and file browser dialogs for double-click execution.
- **CI/CD**: GitHub Actions workflow matrix for automated testing on Linux, Windows, macOS across Python 3.9–3.13, and automated release builds.
