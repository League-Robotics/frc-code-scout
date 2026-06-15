"""Detect the FRC competition season a repo belongs to, from its name alone.

Name-based only: a repo's GitHub `pushed_at` is unreliable (e.g. Reefscape2025
gets pushed in 2026), so we never use timestamps for season classification.
"""

from __future__ import annotations

import re

from . import config

# A standalone 4-digit 20xx not glued to other digits (so "5137_VSCode2024" ->
# 2024 but a part number like "120249" doesn't match a year).
_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")
# The "2k25" shorthand (team 190's "2k25-Robot-Code").
_2K_RE = re.compile(r"(?<![0-9a-z])2k(\d{2})(?![0-9])", re.IGNORECASE)


def detect_season(repo_name: str) -> int | None:
    """Return the in-window season year for `repo_name`, or None.

    1. Any 4-digit 20xx in the name -> pick the most-recent in-window year.
    2. "2k25" shorthand -> 20xx.
    3. Season-name alias substring (reefscape, crescendo, ...) -> its year.
    Out-of-window years (e.g. 2014, 2020) return None: not a current-window repo.
    A None result means "season-independent / library / out-of-window".
    """
    candidates: list[int] = []

    for m in _YEAR_RE.finditer(repo_name):
        candidates.append(int(m.group(1)))
    for m in _2K_RE.finditer(repo_name):
        candidates.append(2000 + int(m.group(1)))

    in_window = [y for y in candidates if y in config.SEASONS]
    if in_window:
        return max(in_window)
    if candidates:
        # A year was found but it's outside the window -> explicitly not selected.
        return None

    # Fallback: season-name keyword (no digits in the name).
    squished = re.sub(r"[^a-z0-9]", "", repo_name.lower())
    for alias, year in config.SEASON_ALIASES.items():
        if alias in squished and year in config.SEASONS:
            return year
    return None


def detected_year_any(repo_name: str) -> int | None:
    """Like detect_season but also returns OUT-of-window years (for reporting).

    Used to label discovered repos as "skipped: old season 2014" in manifests.
    """
    years = [int(m.group(1)) for m in _YEAR_RE.finditer(repo_name)]
    years += [2000 + int(m.group(1)) for m in _2K_RE.finditer(repo_name)]
    if years:
        return max(years)
    squished = re.sub(r"[^a-z0-9]", "", repo_name.lower())
    for alias, year in config.SEASON_ALIASES.items():
        if alias in squished:
            return year
    return None
