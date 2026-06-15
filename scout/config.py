"""Central configuration: seasons, paths, suppression rules, output-root resolution.

Single source of truth for the constants every other module reads. No I/O at
import time except resolving filesystem paths relative to the repo root.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Repo-relative paths ---------------------------------------------------
# config.py lives at <repo>/scout/config.py
REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFESTS_DIR = REPO_ROOT / "data" / "manifests"
CACHE_DIR = REPO_ROOT / "data" / "cache"
DATA_DIR = REPO_ROOT / "data"
DEFAULT_MASTER_JSON = DATA_DIR / "master-dataset.json"
DEFAULT_INVENTORY_MD = DATA_DIR / "corpus-inventory.md"

SD_MANIFEST = MANIFESTS_DIR / "frc-teams.tsv"
NATIONAL_MANIFEST = MANIFESTS_DIR / "national-frc-teams.tsv"

# --- Seasons ---------------------------------------------------------------
# FRC game name per competition year. The window is all five (user choice).
SEASONS: dict[int, str] = {
    2022: "Rapid React",
    2023: "Charged Up",
    2024: "Crescendo",
    2025: "Reefscape",
    2026: "Rebuilt",
}
SEASON_WINDOW: tuple[int, ...] = tuple(sorted(SEASONS))

# Squished / alias spellings used in repo names, mapped to their season year.
SEASON_ALIASES: dict[str, int] = {
    "rapidreact": 2022,
    "chargedup": 2023,
    "crescendo": 2024,
    "reefscape": 2025,
    "rebuilt": 2026,
}

# --- Large-file suppression ------------------------------------------------
# Extensions whose files are truncated to 0 bytes and renamed <name>.sup in the
# working tree (never inside .git/). Seeded from scripts/clone_corpus.sh plus
# documents (user asked to suppress "documents" too).
SUPPRESS_EXTS: frozenset[str] = frozenset(
    {
        # CAD / 3D
        ".stl", ".step", ".stp", ".sldprt", ".sldasm", ".f3d",
        ".dxf", ".dwg", ".iges", ".obj", ".3mf",
        # video
        ".mp4", ".mov", ".avi", ".mkv", ".webm",
        # images / design
        ".psd",
        # archives
        ".7z", ".rar", ".zip", ".tar", ".gz",
        # compiled / binaries
        ".jar", ".apk", ".so", ".dll", ".dylib", ".exe", ".bin",
        # ML model weights
        ".onnx", ".tflite", ".pb", ".pt", ".h5",
        # robot logs
        ".wpilog", ".hoot", ".rlog", ".dslog", ".dsevents", ".bag",
        # documents
        ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    }
)
SUPPRESS_SIZE_BYTES = 2 * 1024 * 1024  # also suppress any file larger than 2 MB

# --- Network ---------------------------------------------------------------
USER_AGENT = "frc-code-scout/0.1 (+https://github.com/jointheleague)"
STATBOTICS_BASE = "https://api.statbotics.io/v3"
GITHUB_API = "https://api.github.com"
CLONE_TIMEOUT_SEC = 600  # full-history clones of big repos can be slow


def github_token() -> str | None:
    """Token from the environment (GITHUB_TOKEN preferred, then GH_TOKEN)."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None


def resolve_output_root(cli_value: str | None) -> Path:
    """Resolve the corpus output root.

    Precedence: --output-root flag > $SCOUT_DATA env > <repo>/frc_team_repos.
    The repo ships a `frc_team_repos` symlink pointing at local disk.
    """
    if cli_value:
        root = Path(cli_value).expanduser()
    elif os.environ.get("SCOUT_DATA"):
        root = Path(os.environ["SCOUT_DATA"]).expanduser()
    else:
        root = REPO_ROOT / "frc_team_repos"
    return root


def warn_if_synced(path: Path) -> None:
    """Warn (don't fail) if the resolved path is the cloud-synced repo tree.

    The project's AGENTS.md warns that git lock handling can fail on mounted /
    cloud-synced volumes. `frc_team_repos` is a symlink to local disk, so we
    only warn when the *real* path is under the repo itself.
    """
    try:
        real = path.resolve()
    except OSError:
        return
    if str(real).startswith(str(REPO_ROOT)):
        print(
            f"[scout:warn] corpus root resolves inside the repo ({real}); if it "
            f"is on a cloud-synced/mounted drive, git clones may fail. Set "
            f"$SCOUT_DATA or --output-root to a plain local path.",
            file=sys.stderr,
        )
