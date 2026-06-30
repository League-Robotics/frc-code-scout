#!/usr/bin/env python3
"""Render all .d2 files in docs/elite-arch/diagrams/ to site/static/diagrams/ as SVG."""
import subprocess, os, sys
from pathlib import Path

REPO = Path("/Volumes/Proj/proj/RobotProjects/frc-code-scout")
SRC = REPO / "docs/elite-arch/diagrams"
DST = REPO / "site/static/diagrams"

if not SRC.exists():
    print("No diagrams directory — nothing to render")
    sys.exit(0)

DST.mkdir(parents=True, exist_ok=True)

rendered = 0
for d2_file in sorted(SRC.glob("*.d2")):
    svg_file = DST / f"{d2_file.stem}.svg"
    # Only re-render if source is newer
    if svg_file.exists() and svg_file.stat().st_mtime > d2_file.stat().st_mtime:
        print(f"  skip {d2_file.name} (up to date)")
        continue
    result = subprocess.run(
        ["d2", str(d2_file), str(svg_file)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        size = svg_file.stat().st_size
        print(f"  rendered {d2_file.name} → {svg_file.name} ({size:,} bytes)")
        rendered += 1
    else:
        print(f"  FAILED {d2_file.name}: {result.stderr.strip()}", file=sys.stderr)

print(f"\n{rendered} diagram(s) rendered")
