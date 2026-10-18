"""Configuration constants and language lookups for merge_subs."""

from __future__ import annotations

from pathlib import Path

# Supported video container extensions
VIDEO_EXT = {
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".m4v",
    ".webm",
    ".ts",
    ".mpg",
    ".mpeg",
}

# Supported subtitle file extensions
SUB_EXT = {".srt", ".ass", ".ssa", ".sub", ".vtt", ".smi"}

# Common directory names containing subtitle files
SUB_DIR_NAMES = {"sub", "subs", "subtitle", "subtitles"}

# Container format mappings for FFmpeg
FORMATS = {
    ".mkv": "matroska",
    ".mp4": "mp4",
    ".m4v": "mp4",
    ".mov": "mov",
}

# Known languages dictionary: canonical_name -> (iso639-1, iso639-2/B)
LANGS = {
    "english": ("en", "eng"),
    "spanish": ("es", "spa"),
    "french": ("fr", "fre"),
    "german": ("de", "ger"),
    "arabic": ("ar", "ara"),
    "hindi": ("hi", "hin"),
    "nepali": ("ne", "nep"),
    "italian": ("it", "ita"),
    "portuguese": ("pt", "por"),
    "russian": ("ru", "rus"),
    "japanese": ("ja", "jpn"),
    "korean": ("ko", "kor"),
    "chinese": ("zh", "chi"),
    "dutch": ("nl", "dut"),
    "turkish": ("tr", "tur"),
    "polish": ("pl", "pol"),
    "swedish": ("sv", "swe"),
    "indonesian": ("id", "ind"),
    "vietnamese": ("vi", "vie"),
    "thai": ("th", "tha"),
    "greek": ("el", "gre"),
    "hebrew": ("he", "heb"),
    "czech": ("cs", "cze"),
    "romanian": ("ro", "rum"),
    "danish": ("da", "dan"),
    "finnish": ("fi", "fin"),
    "norwegian": ("no", "nor"),
    "hungarian": ("hu", "hun"),
    "urdu": ("ur", "urd"),
    "persian": ("fa", "per"),
    "malay": ("ms", "may"),
    "bengali": ("bn", "ben"),
    "ukrainian": ("uk", "ukr"),
    "croatian": ("hr", "hrv"),
    "serbian": ("sr", "srp"),
    "bulgarian": ("bg", "bul"),
    "slovak": ("sk", "slo"),
    "tagalog": ("tl", "tgl"),
    "filipino": ("fil", "fil"),
}

# Reverse lookup table: token -> (canonical_name, iso3)
LOOKUP: dict[str, tuple[str, str]] = {}
for _name, (_s, _i3) in LANGS.items():
    for _token in (_name, _s, _i3):
        LOOKUP[_token.lower()] = (_name, _i3)

# Common synonyms and alternate ISO codes
LOOKUP.update(
    {
        "fra": ("french", "fre"),
        "deu": ("german", "ger"),
        "zho": ("chinese", "chi"),
        "farsi": ("persian", "per"),
        "brazilian": ("portuguese", "por"),
        "pt-br": ("portuguese", "por"),
        "ptbr": ("portuguese", "por"),
        "es-la": ("spanish", "spa"),
        "latam": ("spanish", "spa"),
    }
)

# Saved FFmpeg configuration path in user home directory
CONFIG_FILE = Path.home() / ".merge_subs_ffmpeg.txt"
