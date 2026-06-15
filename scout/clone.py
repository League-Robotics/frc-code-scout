"""Clone one repo with full history, extract the commit log, then discard blobs.

Per-repo pipeline (resumable, atomic):
  1. git clone --quiet <url> <dest>.tmp     (full history)
  2. extract commit activity from .git
  3. suppress large/binary files in the working tree (*.sup stubs)
  4. write history.json (after suppress, so it can't be self-suppressed)
  5. strip .git (unless keep_git)
  6. os.replace(<dest>.tmp, <dest>)          (atomic publish)

Mirrors scripts/clone_corpus.sh's `.tmp`-then-rename resumability so a crash
never leaves a half-written repo in the published tree.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from . import config, history, suppress


def _rmtree(path: Path) -> None:
    def _onerror(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    if path.exists():
        shutil.rmtree(path, onerror=_onerror)


def _bucket(year: int | None) -> str:
    return str(year) if year else "library"


def process_repo(
    team_dir: Path,
    *,
    year: int | None,
    repo_name: str,
    clone_url: str,
    html_url: str,
    keep_git: bool,
    output_root: Path,
) -> dict:
    """Clone + process one repo. Returns its dataset record (never raises)."""
    bucket = _bucket(year)
    dest = team_dir / bucket / repo_name
    tmp = team_dir / bucket / (repo_name + ".tmp")
    rel = dest.relative_to(output_root)

    record = {
        "year": year,
        "repo": repo_name,
        "url": html_url,
        "local_path": str(rel),
        "detected_via": None,  # filled by caller
    }

    # Resume: already published -> reuse its history summary, don't re-clone.
    if dest.exists():
        record["cloned"] = True
        hist_file = dest / "history.json"
        if hist_file.exists():
            try:
                record["history_summary"] = json.loads(hist_file.read_text()).get("summary")
            except (json.JSONDecodeError, OSError):
                pass
        return record

    _rmtree(tmp)  # clear any stale partial from a previous interrupted run
    tmp.parent.mkdir(parents=True, exist_ok=True)

    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = subprocess.run(
            ["git", "clone", "--quiet", clone_url, str(tmp)],
            capture_output=True, text=True, timeout=config.CLONE_TIMEOUT_SEC, env=env,
        )
    except subprocess.TimeoutExpired:
        _rmtree(tmp)
        record["cloned"] = False
        record["error"] = "clone_timeout"
        return record

    if proc.returncode != 0:
        _rmtree(tmp)
        record["cloned"] = False
        record["error"] = "clone_failed"
        record["detail"] = (proc.stderr or "").strip().splitlines()[-1:] or ""
        return record

    # 2. history (reads .git)  3. suppress working tree  4. write history.json
    hist = history.extract_history(tmp)
    suppressed = suppress.suppress_tree(tmp)
    (tmp / "history.json").write_text(
        json.dumps({"repo": repo_name, "url": html_url, **hist}, indent=1)
    )

    # 5. strip blobs
    if not keep_git:
        _rmtree(tmp / ".git")

    # 6. atomic publish
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, dest)

    record["cloned"] = True
    record["suppressed_files"] = suppressed
    record["history_summary"] = hist["summary"]
    return record
