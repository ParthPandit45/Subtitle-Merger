"""Unit tests for subtitle matching, grouping, and language detection."""

from __future__ import annotations

import unittest
from pathlib import Path
from merge_subs.matcher import detect_lang, Group, choose_group


class TestMatcher(unittest.TestCase):
    def test_detect_lang_standard(self):
        self.assertEqual(detect_lang("2_English.srt"), ("english", "eng"))
        self.assertEqual(detect_lang("Spanish.srt"), ("spanish", "spa"))
        self.assertEqual(detect_lang("Japanese.ass"), ("japanese", "jpn"))

    def test_detect_lang_aliases(self):
        self.assertEqual(detect_lang("sub_fra.srt"), ("french", "fre"))
        self.assertEqual(detect_lang("audio_deu.srt"), ("german", "ger"))
        self.assertEqual(detect_lang("Brazilian.srt"), ("portuguese", "por"))
        self.assertEqual(detect_lang("Farsi.srt"), ("persian", "per"))

    def test_detect_lang_unknown(self):
        name, code = detect_lang("track_unknown_123.srt")
        self.assertIsNone(name)
        self.assertEqual(code, "und")

    def test_choose_group_exact_name(self):
        video = Path("Show.S04E01.1080p.mp4")
        g1 = Group("Show.S04E01.1080p", [Path("2_English.srt")])
        g2 = Group("Show.S04E02.1080p", [Path("2_English.srt")])
        matched, status = choose_group(video, [g1, g2])
        self.assertEqual(status, "ok")
        self.assertIs(matched, g1)

    def test_choose_group_episode_match(self):
        video = Path("SuperShow.S02E05.WEBRip.mp4")
        # Subtitle group has different release tag but identical episode
        g1 = Group("SuperShow.S02E05.HDTV", [Path("sub.srt")])
        g2 = Group("SuperShow.S02E06.HDTV", [Path("sub.srt")])
        matched, status = choose_group(video, [g1, g2])
        self.assertEqual(status, "ok")
        self.assertIs(matched, g1)

    def test_choose_group_partial_double_episode(self):
        # Video is double episode S04E01E02, but subtitle group only has S04E01
        video = Path("Show.S04E01E02.mp4")
        g1 = Group("Show.S04E01", [Path("sub.srt")])
        matched, status = choose_group(video, [g1])
        # Crucial requirement: must return "partial" so file is reported failed
        # rather than given incorrect subtitles
        self.assertEqual(status, "partial")
        self.assertIs(matched, g1)

    def test_choose_group_fuzzy_no_episodes(self):
        video = Path("The.Big.Movie.2024.1080p.mp4")
        g1 = Group("The.Big.Movie.2024.720p", [Path("movie.srt")])
        matched, status = choose_group(video, [g1])
        self.assertEqual(status, "ok")
        self.assertIs(matched, g1)


if __name__ == "__main__":
    unittest.main()
