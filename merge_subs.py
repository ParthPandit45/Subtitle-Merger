#!/usr/bin/env python3
"""
merge_subs - Batch subtitle embedder for TV episodes and video files.

Usage:
    python merge_subs.py                 (opens folder picker)
    python merge_subs.py "C:\\Path\\To\\Folder"
    python merge_subs.py "C:\\Path\\To\\Folder" --lang spanish --jobs 4
    python merge_subs.py "C:\\Path\\To\\Folder" --dry-run
"""

import sys
from merge_subs.cli import main

if __name__ == "__main__":
    sys.exit(main())
