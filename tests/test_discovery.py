"""Unit tests for FFmpeg discovery logic."""

import unittest
from merge_subs.discovery import works, candidate_paths


class TestDiscovery(unittest.TestCase):
    def test_works_with_invalid_path(self):
        self.assertFalse(works("non_existent_ffmpeg_binary_xyz_123.exe"))
        self.assertFalse(works(""))

    def test_candidate_paths_generation(self):
        candidates = list(candidate_paths(["C:\\CustomDir"]))
        self.assertTrue(len(candidates) > 0)


if __name__ == "__main__":
    unittest.main()
