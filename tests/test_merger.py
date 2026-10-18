"""Unit tests for FFmpeg command line generation and format mapping."""

import unittest
from pathlib import Path
from merge_subs.merger import build_ffmpeg_command


class TestMergerCommand(unittest.TestCase):
    def test_build_ffmpeg_command_mp4(self):
        video = Path("Show.S01E01.mp4")
        tmp_out = Path("Show.S01E01.mp4.part")
        usable = [
            (
                {
                    "path": Path("sub1.srt"),
                    "lang3": "eng",
                    "label": "English",
                    "forced": False,
                    "size": 100,
                    "default": True,
                },
                Path("temp_utf8_1.srt"),
                "mov_text",
            )
        ]

        cmd = build_ffmpeg_command(
            video=video,
            usable_tracks=usable,
            tmp_out=tmp_out,
            fmt="mp4",
            pre_sub_count=0,
            default_idx=0,
            ffmpeg_bin="ffmpeg",
        )

        # Check essential flags
        self.assertIn("-c", cmd)
        self.assertIn("copy", cmd)
        self.assertIn("-map", cmd)
        self.assertIn("0:v", cmd)
        self.assertIn("1:0", cmd)
        self.assertIn("-c:s:0", cmd)
        self.assertIn("mov_text", cmd)
        self.assertIn("-metadata:s:s:0", cmd)
        self.assertIn("language=eng", cmd)
        self.assertIn("title=English", cmd)
        self.assertIn("-disposition:s:0", cmd)
        self.assertIn("default", cmd)
        self.assertIn("-movflags", cmd)
        self.assertIn("+faststart", cmd)

    def test_build_ffmpeg_command_mkv(self):
        video = Path("Show.S01E01.mkv")
        tmp_out = Path("Show.S01E01.mkv.part")
        usable = [
            (
                {
                    "path": Path("sub1.ass"),
                    "lang3": "jpn",
                    "label": "Japanese",
                    "forced": False,
                    "size": 200,
                    "default": True,
                },
                Path("temp_utf8_1.ass"),
                "ass",
            )
        ]

        cmd = build_ffmpeg_command(
            video=video,
            usable_tracks=usable,
            tmp_out=tmp_out,
            fmt="matroska",
            pre_sub_count=1,  # Pre-existing stream count is 1
            default_idx=0,
            ffmpeg_bin="ffmpeg",
        )

        # Pre-existing was 1, so newly appended subtitle stream index is 1 (0-indexed video/audio/sub streams)
        self.assertIn("-c:s:1", cmd)
        self.assertIn("ass", cmd)
        self.assertIn("-metadata:s:s:1", cmd)
        self.assertIn("language=jpn", cmd)
        self.assertIn("-f", cmd)
        self.assertIn("matroska", cmd)


if __name__ == "__main__":
    unittest.main()
