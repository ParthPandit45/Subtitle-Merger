# Subtitle-Merger (merge_subs)

> Losslessly embed matching subtitles into TV episodes and video files in place using FFmpeg without re-encoding.

[![CI](https://github.com/ParthPandit45/Subtitle-Merger/actions/workflows/ci.yml/badge.svg)](https://github.com/ParthPandit45/Subtitle-Merger/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-25%20passed-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

---

## Key Features

- **Blazing Fast & Lossless**: Stream-copies all video and audio tracks (`-c copy`) without quality loss or re-encoding.
- **Multithreaded Concurrent Merging (`--jobs N`)**: Process multiple episodes simultaneously to saturate SSD/NVMe read-write bandwidth.
- **Smart Episode & Name Matching**:
  - Handles `S03E01`, `3x05`, `Episode 5`, `ep.07`, and multi-episode releases such as `S03E12E13` and `S03E12-14`.
  - Multi-tiered matching: Exact normalized name &rarr; Episode number set &rarr; Fuzzy match (`difflib` ratio &ge; 0.75 when episode numbers are omitted).
  - Safety check: If subtitles cover only part of a multi-episode file, the file is safely flagged as failed rather than paired with incomplete subtitles.
- **Multi-Track Metadata & Disposition**:
  - Embeds every subtitle file as an independent selectable track.
  - Automatically identifies languages from filename tokens across 35+ languages.
  - Generates clear track titles (e.g. `English`, `English (2)`, `English (forced)`, `English (SDH)`).
  - Flags preferred language (`--lang`, default `english`) as default; forced tracks are never set as default.
- **In-Place Atomic Safety**:
  - Temporary files write to `<video>.part` alongside the original.
  - Output is verified before replacing: must exist, be &ge; 80% of original size, and contain all expected subtitle streams.
  - Handles Windows file locking (antivirus, media players, Windows Search indexer) with automatic exponential backoff retries.
  - Interruptions clean up automatically; stale `.part` files are removed on startup.
  - Videos with pre-existing subtitle streams are safely skipped on re-runs.
- **Smart FFmpeg Discovery**:
  - Automatically locates FFmpeg via `--ffmpeg`, `FFMPEG_PATH`, system `PATH`, saved settings, WinGet packages, Scoop shims, Chocolatey, and standard installation paths.
  - Includes companion `ffprobe` detection for rapid stream verification.
- **Standalone Windows Executable**:
  - Single-file executable (`merge_subs.exe`) built with PyInstaller for zero-dependency execution.
  - Double-click friendly: launches native Windows directory browser and pauses before closing so you can inspect results.

---

## Repository Structure

```text
merge_subs/
├── merge_subs/               # Core Python package
│   ├── __init__.py           # Package exports & version
│   ├── __main__.py           # Module execution entry point (python -m merge_subs)
│   ├── cli.py                # CLI parser, orchestration, thread-safe printer
│   ├── config.py             # Formats, extensions, 35+ language lookups
│   ├── discovery.py          # FFmpeg & FFprobe binary auto-detection
│   ├── episode.py            # Episode parsing, multi-episode ranges, normalization
│   ├── matcher.py            # Subtitle group discovery, scoring & matching
│   ├── merger.py             # FFmpeg lossless remux engine & verification
│   ├── track.py              # Track building, language tagging, disposition sort
│   ├── ui.py                 # Native folder & file dialogs (PowerShell / Tkinter)
│   └── utils.py              # Fast in-memory validation, stream counting, UTF-8 conversion
├── tests/                    # Automated test suite (100% pass)
│   ├── test_episode.py       # Episode parsing & match comparisons
│   ├── test_matcher.py       # Grouping, language detection & partial multi-episode safety
│   ├── test_track.py         # Track building, default flags & SDH/forced detection
│   ├── test_discovery.py     # Binary discovery & candidate paths
│   └── test_merger.py        # FFmpeg command generation & container conversions
├── dist/
│   └── merge_subs.exe        # Standalone pre-compiled Windows executable
├── build_exe.py              # Automated PyInstaller packaging script
├── merge_subs.py             # Root runner script
├── pyproject.toml            # PEP 518/621 build configuration & entry points
├── requirements.txt          # Runtime dependencies (pure stdlib)
├── requirements-dev.txt      # Development dependencies (pyinstaller, pytest)
├── LICENSE                   # MIT License
└── README.md
```

---

## Installation & Requirements

### Option A: Using the Pre-Compiled Executable (`merge_subs.exe`)
No Python installation is required! Simply run `dist/merge_subs.exe` directly or copy it anywhere on your system.

### Option B: Running from Python
`merge_subs` is built using only the Python standard library. Python 3.9+ is supported.

```powershell
# Clone or navigate to the repository directory
cd merge_subs

# Optional: Install developer tools
pip install -r requirements-dev.txt
```

### FFmpeg Requirement
Ensure FFmpeg is installed. If you do not have FFmpeg, install it via WinGet:
```powershell
winget install Gyan.FFmpeg
```
Or download FFmpeg from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or [ffmpeg.org](https://ffmpeg.org/download.html).

---

## Usage

### 1. Interactive Mode (Folder Picker)
Run without arguments to open a native folder picker dialog:
```powershell
# Using the executable:
.\dist\merge_subs.exe

# Or using Python:
python merge_subs.py
```
*Note: When run interactively, the console pauses on completion with `Press Enter to close...` so you can view the summary.*

### 2. Command Line Arguments
Pass the target directory directly as a parameter:
```powershell
# Process a folder with default settings:
python merge_subs.py "D:\TV Shows\Breaking Bad"

# Set Spanish as the preferred default subtitle language:
python merge_subs.py "D:\TV Shows\Breaking Bad" --lang spanish

# Accelerate processing with 8 parallel worker threads:
python merge_subs.py "D:\TV Shows\Breaking Bad" --jobs 8

# Dry-run preview (checks matches without modifying files):
python merge_subs.py "D:\TV Shows\Breaking Bad" --dry-run

# Force re-processing of files that already have subtitle tracks:
python merge_subs.py "D:\TV Shows\Breaking Bad" --force

# Specify a custom path to ffmpeg:
python merge_subs.py "D:\TV Shows" --ffmpeg "C:\Custom\ffmpeg.exe"
```

---

## CLI Reference

```text
usage: merge_subs [-h] [--lang LANG] [--ffmpeg FFMPEG] [-j JOBS] [--dry-run] [-f] [root]

Losslessly embed matching subtitles into TV episodes and video files in place.

positional arguments:
  root             Folder containing videos and subtitle directories (omitting opens a folder dialog)

options:
  -h, --help       show this help message and exit
  --lang LANG      Preferred default subtitle language track (default: english)
  --ffmpeg FFMPEG  Path to ffmpeg executable if not in PATH or auto-discovered
  -j, --jobs JOBS  Number of concurrent worker threads for parallel remuxing (default: 4)
  --dry-run        Preview matching subtitles and tracks without modifying files
  -f, --force      Force re-processing of files that already have subtitle tracks
```

---

## Expected Folder Layouts

`merge_subs` handles season subfolders, multiple season directories, and nested `Subs` folders:

```text
TV Series/
  Season 01/
    Show.S01E01.1080p.mkv
    Show.S01E02.1080p.mkv
    Subs/
      Show.S01E01.1080p/
        2_English.srt
        3_Spanish.srt
      Show.S01E02.1080p/
        2_English.srt
```

Loose subtitle files in the same directory as the video are also matched automatically:
```text
Season 02/
  Show.S02E01.720p.mp4
  Show.S02E01.720p.en.srt
  Show.S02E01.720p.fr.srt
```

---

## Efficiency & Architecture

1. **Multithreaded Remuxing (`--jobs`)**:
   Video stream copying is primarily I/O-bound. Running parallel threads allows modern SSDs to process multiple gigabytes per second across multiple files simultaneously.
2. **Fast Subtitle Validation**:
   Validates `.srt`, `.vtt`, `.ass`, and `.ssa` subtitle integrity in-memory without spawning hundreds of external subprocesses.
3. **Optimized Probing with `ffprobe`**:
   Automatically detects and utilizes `ffprobe` for stream counting, which probes container headers up to 3x faster than full FFmpeg parsing.
4. **MOOV Atom Optimization (`-movflags +faststart`)**:
   When muxing MP4 containers, relocates the index metadata atom to the front of the file, allowing media players to begin playback immediately without buffering the entire file.
5. **Lossless Stream Copy**:
   Zero video or audio re-encoding occurs (`-c copy`). Episodes process in seconds rather than minutes.

---

## Building the Executable

To rebuild `dist/merge_subs.exe`:

```powershell
# Build standalone executable (auto-detects system ffmpeg at runtime):
python build_exe.py

# Optionally bundle ffmpeg directly inside the single-file binary:
python build_exe.py --bundle-ffmpeg
```

---

## Running Tests

Run the test suite using Python's built-in `unittest` runner:

```powershell
python -m unittest discover -s tests -v
```

All 25 unit tests validate episode parsing, fuzzy matching, language detection, track ordering, and FFmpeg command generation.

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up the development environment, run tests, and submit pull requests.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a complete list of changes and release history.

---

## Security

Please review [SECURITY.md](SECURITY.md) for our vulnerability reporting policy.

---

## License

This project is licensed under the [MIT License](LICENSE).
