"""Suppress large / binary / media / document files in a working tree.

Each matching file is truncated to 0 bytes and renamed `<name>.sup` so the tree
stays small and safe for AST/code analysis while still recording that the file
existed. Operates ONLY on the working tree — `.git/` is pruned and never touched
(it is stripped separately after history extraction anyway).
"""

from __future__ import annotations

import os
from pathlib import Path

from . import config


def _should_suppress(path: Path) -> bool:
    if path.suffix.lower() in config.SUPPRESS_EXTS:
        return True
    try:
        return path.stat().st_size > config.SUPPRESS_SIZE_BYTES
    except OSError:
        return False


def suppress_tree(root: Path) -> int:
    """Suppress matching files under `root`. Returns the count suppressed."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # Never descend into git internals.
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".sup"):
                continue
            p = Path(dirpath) / fn
            if p.is_symlink():
                continue
            if _should_suppress(p):
                try:
                    with open(p, "w"):
                        pass  # truncate to 0 bytes
                    os.rename(p, str(p) + ".sup")
                    count += 1
                except OSError:
                    pass
    return count
