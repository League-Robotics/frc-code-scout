"""Extract a repo's commit-activity log from .git BEFORE the blobs are stripped.

For each check-in we record when it happened, who made it, which files changed,
and the size of the change (insertions/deletions = line churn). This is the
data the historical/trajectory analysis needs — the .git blobs themselves are
discarded afterward.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

# SOH sentinel separates commits; fields are tab-separated. core.quotepath=false
# keeps non-ASCII paths literal. --no-renames -> plain add/delete paths.
_FORMAT = "%x01%H%x09%an%x09%ae%x09%ad%x09%s"
_LOG_CMD = [
    "git", "-c", "core.quotepath=false", "log",
    "--numstat", "--date=iso-strict", "--no-renames",
    f"--pretty=format:{_FORMAT}",
]


def _parse_int(tok: str) -> int | None:
    return None if tok == "-" else int(tok)


def extract_history(repo_dir: Path) -> dict:
    """Run git log in `repo_dir`, return {commits:[...], summary:{...}}.

    Safe on repos with no commits / no .git: returns empty commits + summary.
    """
    try:
        # errors="replace": git log can carry non-UTF-8 bytes (latin-1 author
        # names, commit messages); decode tolerantly rather than abort the team.
        out = subprocess.run(
            _LOG_CMD, cwd=repo_dir, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
    except (subprocess.TimeoutExpired, OSError):
        return {"commits": [], "summary": _summarize([])}
    if out.returncode != 0:
        return {"commits": [], "summary": _summarize([])}

    commits: list[dict] = []
    for chunk in out.stdout.split("\x01"):
        if not chunk.strip():
            continue
        lines = chunk.split("\n")
        head = lines[0].split("\t", 4)
        if len(head) < 5:
            continue
        h, an, ae, ad, subject = head
        files = []
        ins_total = dels_total = 0
        for ln in lines[1:]:
            if not ln.strip():
                continue
            parts = ln.split("\t")
            if len(parts) < 3:
                continue
            ins, dels, path = parts[0], parts[1], "\t".join(parts[2:])
            i, d = _parse_int(ins), _parse_int(dels)
            binary = i is None and d is None
            if i:
                ins_total += i
            if d:
                dels_total += d
            files.append(
                {"path": path, "ins": i, "del": d, "binary": binary}
                if binary
                else {"path": path, "ins": i, "del": d}
            )
        commits.append(
            {
                "hash": h,
                "author": an,
                "email": ae,
                "date": ad,
                "subject": subject,
                "files_changed": len(files),
                "insertions": ins_total,
                "deletions": dels_total,
                "files": files,
            }
        )
    return {"commits": commits, "summary": _summarize(commits)}


def _summarize(commits: list[dict]) -> dict:
    if not commits:
        return {
            "commits": 0, "first": None, "last": None, "contributors": 0,
            "insertions": 0, "deletions": 0, "files_touched": 0,
        }
    dates = []
    for c in commits:
        try:
            dates.append(datetime.fromisoformat(c["date"]))
        except (ValueError, KeyError):
            pass
    contributors = {c.get("email") or c.get("author") for c in commits}
    files_touched = {f["path"] for c in commits for f in c["files"]}
    return {
        "commits": len(commits),
        "first": min(dates).isoformat() if dates else None,
        "last": max(dates).isoformat() if dates else None,
        "contributors": len(contributors),
        "insertions": sum(c["insertions"] for c in commits),
        "deletions": sum(c["deletions"] for c in commits),
        "files_touched": len(files_touched),
    }


def write_history(repo_dir: Path, repo: str, url: str) -> dict:
    """Extract history and write `history.json` into the repo dir. Returns summary."""
    hist = extract_history(repo_dir)
    payload = {"repo": repo, "url": url, **hist}
    (repo_dir / "history.json").write_text(json.dumps(payload, indent=1))
    return hist["summary"]
