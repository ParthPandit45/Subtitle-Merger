"""Unit tests for track building, sorting, and default disposition rules."""

from __future__ import annotations

import unittest
from pathlib import Path
from merge_subs.matcher import Group
from merge_subs.track import build_tracks


class TestTrackBuilding(unittest.TestCase):
    def test_build_tracks_preferred_lang_default(self):
        f1 = Path("3_French.srt")
        f2 = Path("2_English.srt")
        f3 = Path("4_Spanish.srt")

        group = Group("TestShow.S01E01", [f1, f2, f3])
        tracks = build_tracks(group, pref="english")

        # Preferred language (English) must be sorted first
        self.assertEqual(tracks[0]["lang3"], "eng")
        self.assertTrue(tracks[0]["default"])

        # Remaining tracks should not be default
        self.assertFalse(tracks[1]["default"])
        self.assertFalse(tracks[2]["default"])

    def test_forced_tracks_are_never_default(self):
        f1 = Path("English_forced.srt")
        f2 = Path("English.srt")

        group = Group("TestShow.S01E01", [f1, f2])
        tracks = build_tracks(group, pref="english")

        # Non-forced English track must be chosen as default over forced track
        non_forced = next(t for t in tracks if not t["forced"])
        forced = next(t for t in tracks if t["forced"])

        self.assertTrue(non_forced["default"])
        self.assertFalse(forced["default"])
        self.assertIn("(forced)", forced["label"])

    def test_sdh_tag_detection(self):
        f1 = Path("English_SDH.srt")
        group = Group("TestShow.S01E01", [f1])
        tracks = build_tracks(group, pref="english")

        self.assertIn("(SDH)", tracks[0]["label"])

    def test_disambiguate_duplicate_labels(self):
        f1 = Path("1_English.srt")
        f2 = Path("2_English.srt")
        f3 = Path("3_English.srt")

        group = Group("TestShow.S01E01", [f1, f2, f3])
        tracks = build_tracks(group, pref="english")

        labels = [t["label"] for t in tracks]
        self.assertEqual(labels, ["English", "English (2)", "English (3)"])


if __name__ == "__main__":
    unittest.main()
