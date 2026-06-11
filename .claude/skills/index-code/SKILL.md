---
name: index-code
description: Install ast-grep if needed and build the per-repo search index (symbol map + rubric-hit JSON, plus optional cocoindex semantic index) over downloaded team code. Use before querying or scoring code, or when the user wants to make the corpus searchable by an agent.
---

# Index downloaded code for search

`scripts/build_index.sh [--repo PATH | --team ID --league frc] [--semantic]`

What it does:
1. Ensures **ast-grep** is installed (tries npm, pip, cargo, brew).
2. Writes `data/index/<league>/<team>/<repo>/symbols.json` — a language-aware map of every
   class/interface/enum/method to file:line (Java/Kotlin/C++/Python), so an agent can jump
   to declarations without reading whole files.
3. Writes `rubric-hits.json` — every ast-grep rubric match in that repo.
4. With `--semantic`, builds a **cocoindex** embedding index for natural-language code
   search ("where is vision rejection logic?"). Requires `pip install cocoindex` and an
   embedding model; falls back gracefully if unavailable.

ast-grep needs no persistent index to *search* (it parses on demand) — the JSON maps are a
convenience cache for agents. Query live anytime with
`ast-grep run -l java -p 'PATTERN' data/repos`.
