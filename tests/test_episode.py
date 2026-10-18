"""Unit tests for episode parsing, normalization, and episode comparison."""

from __future__ import annotations

import unittest
from merge_subs.episode import episodes, eps_match, norm


class TestEpisodeParsing(unittest.TestCase):
    def test_standard_season_episode(self):
        self.assertEqual(episodes("Show.S03E01.1080p.BluRay"), {(3, 1)})
        self.assertEqual(episodes("Show.s3e5"), {(3, 5)})
        self.assertEqual(episodes("Show.S01_E09"), {(1, 9)})

    def test_multi_episode_concatenated(self):
        self.assertEqual(episodes("Show.S04E01E02.1080p"), {(4, 1), (4, 2)})
        self.assertEqual(episodes("Show.S01E03E04E05"), {(1, 3), (1, 4), (1, 5)})

    def test_multi_episode_dashed_range(self):
        self.assertEqual(episodes("Show.S03E12-14"), {(3, 12), (3, 13), (3, 14)})
        self.assertEqual(episodes("Show.S03E12-E14"), {(3, 12), (3, 13), (3, 14)})
        self.assertEqual(episodes("Show.S02E01-02"), {(2, 1), (2, 2)})

    def test_x_notation(self):
        self.assertEqual(episodes("Show.3x05.HDTV"), {(3, 5)})
        self.assertEqual(episodes("Series.12x08"), {(12, 8)})

    def test_loose_episode_notation(self):
        self.assertEqual(episodes("Show.Episode.5.mp4"), {(None, 5)})
        self.assertEqual(episodes("Show.ep.07"), {(None, 7)})
        self.assertEqual(episodes("Show.E12"), {(None, 12)})

    def test_normalization(self):
        self.assertEqual(
            norm("Show.S04E01E02.1080p.BluRay.x265-RARBG"),
            "show s04e01e02 1080p bluray x265 rarbg",
        )
        self.assertEqual(norm("  Foo---Bar___Baz.!!  "), "foo bar baz")

    def test_eps_match_exact(self):
        a = {(4, 1), (4, 2)}
        b = {(4, 1), (4, 2)}
        self.assertEqual(eps_match(a, b), 2)

    def test_eps_match_partial(self):
        double_ep = {(4, 1), (4, 2)}
        single_ep = {(4, 1)}
        self.assertEqual(eps_match(double_ep, single_ep), 1)

    def test_eps_match_none(self):
        a = {(4, 1)}
        b = {(4, 2)}
        self.assertEqual(eps_match(a, b), 0)
        self.assertEqual(eps_match(set(), {(4, 1)}), 0)

    def test_eps_match_with_missing_season(self):
        with_season = {(3, 5)}
        without_season = {(None, 5)}
        self.assertEqual(eps_match(with_season, without_season), 2)


if __name__ == "__main__":
    unittest.main()
