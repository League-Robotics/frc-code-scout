#!/usr/bin/env python3
"""Generate the Jekyll book (docs/book/) from knowledge/ — the single source of truth.

`knowledge/` stays pristine (no committed front matter — it's read by the plugin + skills too).
This mirrors the knowledge tree into docs/book/ and injects just-the-docs nav front matter so the
site renders with a left-nav table of contents. Relative inter-doc links (e.g.
`subsystems/01-linear-position.md`, `../testing.md`) keep working because the tree is preserved and
`jekyll-relative-links` rewrites `.md` links to permalinks.

Run before `jekyll build`; the Pages workflow runs it automatically. docs/book/ is gitignored.

    python3 scripts/build_site.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "knowledge"
OUT = ROOT / "docs" / "book"

# Section landing pages: dir relative to knowledge/ -> (Title, nav_order, parent-title|None)
# A section dir may carry a README.md; if present it becomes the section landing body.
SECTIONS = {
    "corpus-analysis": ("Corpus Analysis", 3, None),
    "build-spec": ("Build Spec", 4, None),
    "build-spec/subsystems": ("Subsystems", 7, "Build Spec"),  # nav_order within Build Spec
    "alternatives": ("Alternatives", 5, None),
    "survey": ("Survey", 6, None),
    "examples": ("Examples", 7, None),
}

# Standalone top-level pages (no parent section): relpath -> (Title, nav_order)
STANDALONE = {
    "rubric/rubric.md": ("Rubric", 2),
}

# Explicit ordering for the build-spec direct files (not numbered in filenames).
BUILDSPEC_ORDER = {
    "elite-architecture.md": 1, "code-review-principles.md": 2, "logging.md": 3,
    "testing.md": 4, "simulation.md": 5, "other-topics.md": 6,
}

SKIP = {"INDEX.md"}  # the repo index; the site home (docs/index.md) replaces it


def h1_title(text: str) -> str:
    """First '# ' heading, trimmed at an em-dash/colon for a tidy sidebar label."""
    for line in text.splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            return re.split(r"\s+[—:]\s+", t)[0].strip()
    return "Untitled"


def strip_first_h1(text: str) -> str:
    """Drop the leading '# ...' line — just-the-docs renders the front-matter title as the H1."""
    out, dropped = [], False
    for line in text.splitlines():
        if not dropped and line.startswith("# "):
            dropped = True
            continue
        out.append(line)
    return "\n".join(out).lstrip("\n")


def fm(**kv) -> str:
    lines = ["---", "layout: default"]
    for k, v in kv.items():
        if v is None:
            continue
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, int):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f'{k}: "{v}"')
    lines.append("---\n")
    return "\n".join(lines)


def section_of(relpath: str):
    """Return (parent, grand_parent, nav_order) for a content file, or None if standalone."""
    p = Path(relpath)
    parent_dir = p.parent.as_posix()
    if parent_dir == "rubric":
        return None  # handled via STANDALONE
    if parent_dir == "build-spec":
        return ("Build Spec", None, BUILDSPEC_ORDER.get(p.name, 50))
    if parent_dir == "build-spec/subsystems":
        # numbered 00..08 -> nav_order 1..9
        m = re.match(r"(\d+)", p.name)
        return ("Subsystems", "Build Spec", int(m.group(1)) + 1 if m else 50)
    title, _, _ = SECTIONS.get(parent_dir, (None, None, None))
    if title:
        return (title, None, None)  # nav_order filled by sort below
    return None


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    files = [p for p in SRC.rglob("*.md") if p.name not in SKIP]
    n_written = 0

    # 1. Section landing pages. A section's README.md, if present, supplies the landing
    #    body (its H1 is dropped — just-the-docs renders the front-matter title); it is then
    #    not re-emitted as a child page.
    readme_used: set[str] = set()
    for d, (title, nav_order, parent) in SECTIONS.items():
        dest = OUT / d / "index.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        readme = SRC / d / "README.md"
        if readme.exists():
            body = strip_first_h1(readme.read_text())
            readme_used.add(readme.relative_to(SRC).as_posix())
        else:
            body = "Select a page from the navigation.\n"
        dest.write_text(
            fm(title=title, nav_order=nav_order, parent=parent, has_children=True) + body
        )

    # 2. Per-section sort order for un-numbered files (survey/examples/corpus-analysis).
    by_parent: dict[str, list[Path]] = {}
    for p in files:
        rel = p.relative_to(SRC).as_posix()
        if rel in STANDALONE or rel in readme_used:
            continue
        sec = section_of(rel)
        if sec and sec[2] is None:
            by_parent.setdefault(sec[0], []).append(p)
    order_index: dict[str, int] = {}
    for parent, plist in by_parent.items():
        for i, p in enumerate(sorted(plist, key=lambda x: x.name), start=1):
            order_index[p.relative_to(SRC).as_posix()] = i

    # 3. Content pages.
    for p in files:
        rel = p.relative_to(SRC).as_posix()
        if rel in readme_used:
            continue
        raw = p.read_text()
        title = h1_title(raw)
        body = strip_first_h1(raw)
        if rel in STANDALONE:
            t, nav = STANDALONE[rel]
            front = fm(title=t, nav_order=nav)
        else:
            sec = section_of(rel)
            if not sec:
                continue
            parent, grand, nav = sec
            if nav is None:
                nav = order_index.get(rel, 99)
            front = fm(title=title, parent=parent, grand_parent=grand, nav_order=nav)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(front + body)
        n_written += 1

    print(f"build_site: wrote {n_written} pages + {len(SECTIONS)} section landings -> {OUT}")


if __name__ == "__main__":
    main()
