"""User interface dialogs for folder and file selection."""

import importlib
import os
import subprocess
from pathlib import Path


def pick_folder(title: str = "Select folder with TV episodes and subtitles") -> str | None:
    """
    Prompt user to choose a directory.
    Uses native Windows Forms folder browser on Windows, dynamic Tkinter on POSIX,
    falling back to console input.
    """
    if os.name == "nt":
        try:
            ps_script = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f"$dialog.Description = '{title}'; "
                "$dialog.ShowNewFolderButton = $false; "
                "$top = New-Object System.Windows.Forms.Form; "
                "$top.TopMost = $true; "
                "if ($dialog.ShowDialog($top) -eq [System.Windows.Forms.DialogResult]::OK) { "
                "    Write-Output $dialog.SelectedPath "
                "}"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=180,
            )
            out = r.stdout.strip()
            if out and Path(out).is_dir():
                return out
        except Exception:
            pass

    # Dynamic Tkinter fallback (avoids static imports for PyInstaller)
    try:
        tk = importlib.import_module("tkinter")
        filedialog = importlib.import_module("tkinter.filedialog")
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(title=title)
        root.destroy()
        if selected and Path(selected).is_dir():
            return selected
    except Exception:
        pass

    # Console input fallback
    try:
        entered = input("Enter folder path: ").strip().strip('"')
        return entered if entered else None
    except (EOFError, KeyboardInterrupt):
        return None


def pick_file(title: str = "Locate ffmpeg.exe (one-time setup)") -> str | None:
    """
    Prompt user to choose an executable file.
    Uses native Windows OpenFileDialog on Windows, dynamic Tkinter on POSIX,
    falling back to console input.
    """
    if os.name == "nt":
        try:
            ps_script = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$dialog = New-Object System.Windows.Forms.OpenFileDialog; "
                f"$dialog.Title = '{title}'; "
                "$dialog.Filter = 'FFmpeg Executable (ffmpeg.exe)|ffmpeg*.exe|All Files (*.*)|*.*'; "
                "$top = New-Object System.Windows.Forms.Form; "
                "$top.TopMost = $true; "
                "if ($dialog.ShowDialog($top) -eq [System.Windows.Forms.DialogResult]::OK) { "
                "    Write-Output $dialog.FileName "
                "}"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=180,
            )
            out = r.stdout.strip()
            if out and Path(out).is_file():
                return out
        except Exception:
            pass

    try:
        tk = importlib.import_module("tkinter")
        filedialog = importlib.import_module("tkinter.filedialog")
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            title=title,
            filetypes=[("FFmpeg Executable", "ffmpeg*"), ("All Files", "*")],
        )
        root.destroy()
        if selected and Path(selected).is_file():
            return selected
    except Exception:
        pass

    try:
        ans = input("Full path to ffmpeg executable: ").strip().strip('"')
        return ans if ans else None
    except (EOFError, KeyboardInterrupt):
        return None
