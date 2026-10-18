"""FFmpeg and ffprobe binary discovery and verification."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from merge_subs.config import CONFIG_FILE


def works(exe: str | Path) -> bool:
    """Test if executable runs and responds to -version without errors."""
    if not exe:
        return False
    try:
        p = Path(exe)
        if not p.is_file():
            return False
        r = subprocess.run(
            [str(p), "-version"],
            capture_output=True,
            timeout=4,
        )
        return r.returncode == 0
    except Exception:
        return False


def candidate_paths(extra_dirs: Iterable[Path | str] = ()) -> Iterable[Path | str]:
    """Generate candidate file paths for ffmpeg in order of priority."""
    env = os.environ
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"

    # PyInstaller bundled bundle directory
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        yield Path(sys._MEIPASS) / exe

    # Executable / script directory
    exe_dir = Path(sys.executable).resolve().parent
    yield exe_dir / exe
    yield exe_dir / "bin" / exe

    # Environment variable
    env_path = env.get("FFMPEG_PATH")
    if env_path:
        yield env_path

    # PATH lookup
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        yield which_ffmpeg

    # User saved config
    if CONFIG_FILE.exists():
        try:
            saved = CONFIG_FILE.read_text(encoding="utf-8").strip()
            if saved:
                yield saved
        except Exception:
            pass

    # Extra directories passed by caller (e.g. video folder or root)
    for d in extra_dirs:
        dp = Path(d)
        yield dp / exe
        yield dp / "bin" / exe

    # Script source directory
    source_dir = Path(__file__).resolve().parent
    yield source_dir / exe
    yield source_dir / "bin" / exe

    # Platform specific searches
    if os.name == "nt":
        local_app = Path(env.get("LOCALAPPDATA", ""))
        home = Path.home()

        # WinGet links & packages
        if local_app.exists():
            yield local_app / "Microsoft" / "WinGet" / "Links" / exe
            try:
                winget_pkgs = local_app / "Microsoft" / "WinGet" / "Packages"
                if winget_pkgs.exists():
                    for p in winget_pkgs.glob("*ffmpeg*/**/ffmpeg.exe"):
                        yield p
            except Exception:
                pass

        # Standard installation paths
        fixed_paths = (
            r"C:\ffmpeg\bin",
            r"C:\Program Files\ffmpeg\bin",
            r"C:\Program Files (x86)\ffmpeg\bin",
            r"C:\ProgramData\chocolatey\bin",
            str(home / "scoop" / "shims"),
            str(home / "ffmpeg" / "bin"),
        )
        for fixed in fixed_paths:
            yield Path(fixed) / exe

        # Shallow directory scans in common user folders
        for base in (
            Path("C:/"),
            home,
            home / "Downloads",
            home / "Desktop",
            Path(r"C:\Program Files"),
        ):
            try:
                if base.exists():
                    for p in base.glob("*ffmpeg*/bin/ffmpeg.exe"):
                        yield p
            except Exception:
                pass
    else:
        for d in ("/usr/local/bin", "/opt/homebrew/bin", "/usr/bin", "/snap/bin"):
            yield Path(d) / exe

    # Optional imageio_ffmpeg module
    try:
        import imageio_ffmpeg  # type: ignore

        yield imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass


def find_ffmpeg(
    extra_dirs: Iterable[Path | str] = (),
    cli_path: str | Path | None = None,
    interactive: bool = False,
) -> str | None:
    """
    Locate working ffmpeg binary.

    If cli_path is provided, checks it first.
    Walks through candidate paths.
    If none found and interactive is True, prompts user via GUI file dialog.
    Saves found path to ~/.merge_subs_ffmpeg.txt.
    """
    if cli_path and works(cli_path):
        resolved = str(Path(cli_path).resolve())
        _save_config(resolved)
        return resolved

    for candidate in candidate_paths(extra_dirs):
        if candidate and works(candidate):
            resolved = str(Path(candidate).resolve())
            _save_config(resolved)
            return resolved

    if interactive:
        # Prompt user once via native UI or terminal input
        from merge_subs.ui import pick_file

        selected = pick_file("Locate ffmpeg.exe (one-time setup)")
        if selected and works(selected):
            resolved = str(Path(selected).resolve())
            _save_config(resolved)
            return resolved

    return None


def find_ffprobe(ffmpeg_path: str | None) -> str | None:
    """Find companion ffprobe binary if available for faster stream probing."""
    if not ffmpeg_path:
        return shutil.which("ffprobe")

    probe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    candidate = Path(ffmpeg_path).parent / probe_name
    if works(candidate):
        return str(candidate)

    which_probe = shutil.which("ffprobe")
    if which_probe and works(which_probe):
        return which_probe

    return None


def _save_config(path_str: str) -> None:
    """Persist working ffmpeg path to config file for future executions."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(path_str, encoding="utf-8")
    except Exception:
        pass
