#!/usr/bin/env python3
"""Render D2 diagrams to SVG for Hugo.

Two sources:
  1. Standalone .d2 files in docs/elite-arch/diagrams/  →  site/static/diagrams/<name>.svg
  2. ```d2 fenced blocks in .md files                    →  site/static/diagrams/d2_<path>_<n>.svg

The Hugo render hook (render-codeblock-d2.html) embeds the pre-rendered SVGs
by matching .Page.File.Path + .Ordinal to the filename pattern.
"""
import subprocess, sys, hashlib, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_MD = REPO / "docs/elite-arch"
SRC_D2 = SRC_MD / "diagrams"
DST = REPO / "site/static/diagrams"

DST.mkdir(parents=True, exist_ok=True)

rendered = 0


def fix_multiline_strings(d2_text: str) -> str:
    """Convert multi-line double-quoted strings to D2 block string syntax.

    D2:  KEY: "text\nmore text"       → error
    D2:  KEY: |  text\n       more text\n|  → ok
    """
    _pattern = re.compile(r'^(\s*\w+:\s*)"([^"]*\n[^"]*?)"', re.MULTILINE)

    def _replace(m):
        prefix = m.group(1)
        content = m.group(2)
        lines = content.split('\n')
        result = f'{prefix}|  {lines[0].rstrip()}\n'
        indent = ' ' * (len(prefix) - len(prefix.lstrip()) + 2)
        for line in lines[1:]:
            result += f'{indent}{line.rstrip()}\n'
        result += f'{indent[:-2]}|'
        return result

    prev = None
    while prev != d2_text:
        prev = d2_text
        d2_text = _pattern.sub(_replace, d2_text, count=1)
    return d2_text


# ── 1. Standalone .d2 files ──
if SRC_D2.exists():
    for d2_file in sorted(SRC_D2.glob("*.d2")):
        svg_file = DST / f"{d2_file.stem}.svg"
        if svg_file.exists() and svg_file.stat().st_mtime > d2_file.stat().st_mtime:
            continue
        result = subprocess.run(["d2", str(d2_file), str(svg_file)], capture_output=True, text=True)
        if result.returncode == 0:
            size = svg_file.stat().st_size
            print(f"  {d2_file.name} → {svg_file.name} ({size:,} bytes)")
            rendered += 1
        else:
            print(f"  FAILED {d2_file.name}: {result.stderr.strip()}", file=sys.stderr)

# ── 2. ```d2 fenced blocks in markdown ──
# Match EVERY fenced code block, not just ```d2, so the index matches Hugo's
# .Ordinal — which counts all code blocks on the page regardless of language.
# (Numbering only the d2 blocks drifts out of sync on any page that also has
# ```java etc. before a diagram, and the render hook then can't find the SVG.)
FENCE_BLOCK = re.compile(r'^```(\w*)[^\n]*\n(.*?)^```', re.DOTALL | re.MULTILINE)

for md_file in sorted(SRC_MD.rglob("*.md")):
    text = md_file.read_text()
    blocks = list(FENCE_BLOCK.finditer(text))
    if not blocks:
        continue

    rel = md_file.relative_to(SRC_MD)
    # Sanitize path for filename: replace / and . with _
    safe_path = str(rel).replace("/", "_").replace(".md", "")

    for idx, m in enumerate(blocks):
        if m.group(1) != "d2":
            continue
        d2_content = m.group(2).strip()
        if not d2_content:
            continue

        # Fix multi-line quoted strings for D2 compatibility
        d2_content = fix_multiline_strings(d2_content)

        svg_name = f"d2_{safe_path}_{idx}.svg"
        svg_file = DST / svg_name

        # Check if up to date (compare content hash stored in sidecar)
        hash_file = DST / f"d2_{safe_path}_{idx}.txt"
        content_hash = hashlib.sha256(d2_content.encode()).hexdigest()
        if svg_file.exists() and hash_file.exists():
            if hash_file.read_text().strip() == content_hash:
                print(f"  {rel}:{idx} → {svg_name} (up to date)")
                continue

        # Write temp D2 file
        tmp_d2 = DST / f"_tmp_{svg_name}.d2"
        tmp_d2.write_text(d2_content)

        result = subprocess.run(["d2", str(tmp_d2), str(svg_file)], capture_output=True, text=True)
        tmp_d2.unlink()

        if result.returncode == 0:
            hash_file.write_text(content_hash)
            size = svg_file.stat().st_size
            print(f"  {rel}:{idx} → {svg_name} ({size:,} bytes)")
            rendered += 1
        else:
            print(f"  FAILED {rel}:{idx}: {result.stderr.strip()}", file=sys.stderr)

print(f"\n{rendered} diagram(s) rendered")
