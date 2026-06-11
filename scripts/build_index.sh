#!/usr/bin/env bash
# Prepare downloaded code for agent search.
#   1. Ensure ast-grep is installed (structural AST search — no prebuilt index needed).
#   2. Emit a per-repo symbol map (classes/interfaces/enums/methods -> file:line) as JSON.
#   3. Optional: build a cocoindex semantic index (--semantic) for natural-language code search.
#
# Usage:
#   scripts/build_index.sh [--repo PATH | --team ID --league frc] [--semantic]
set -uo pipefail
source "$(dirname "$0")/lib/common.sh"
REPO=""; TEAM=""; LEAGUE=frc; SEMANTIC=0
while [ $# -gt 0 ]; do case "$1" in
  --repo) REPO="$2"; shift 2;; --team) TEAM="$2"; shift 2;;
  --league) LEAGUE="$2"; shift 2;; --semantic) SEMANTIC=1; shift;;
  -h|--help) sed -n '2,11p' "$0"; exit 0;;
  *) die "unknown arg: $1";; esac; done

ensure_astgrep() {
  have ast-grep && return 0
  log "installing ast-grep…"
  npm i -g @ast-grep/cli 2>/dev/null && return 0
  pip install ast-grep-cli --break-system-packages -q 2>/dev/null && return 0
  have cargo && cargo install ast-grep --locked 2>/dev/null && return 0
  have brew && brew install ast-grep 2>/dev/null && return 0
  die "could not install ast-grep — see https://ast-grep.github.io/guide/quick-start.html"
}
ensure_astgrep

targets=()
if [ -n "$REPO" ]; then targets+=("$REPO")
elif [ -n "$TEAM" ]; then for d in "$REPOS/$LEAGUE/$TEAM"*/*/; do targets+=("$d"); done
else for d in "$REPOS/$LEAGUE"/*/*/; do targets+=("$d"); done; fi
[ ${#targets[@]} -gt 0 ] || die "no target repos (run clone_corpus.sh first)"

for t in "${targets[@]}"; do
  [ -d "$t" ] || continue
  rel="${t#$REPOS/}"; out="$INDEX/${rel%/}"; mkdir -p "$out"
  log "symbol map: $rel"
  ast-grep scan --config "$SCOUT_ROOT/sgconfig.yml" "$t" --json 2>/dev/null \
    > "$out/rubric-hits.json" || echo '[]' > "$out/rubric-hits.json"
  # language-agnostic declaration map via ast-grep patterns (java/kotlin/cpp/python)
  python3 "$SCOUT_ROOT/scripts/lib/symbol_map.py" "$t" > "$out/symbols.json" 2>/dev/null || echo '{}' > "$out/symbols.json"
  log "  -> $out/{rubric-hits,symbols}.json"
done

if [ "$SEMANTIC" -eq 1 ]; then
  log "semantic index (cocoindex)…"
  python3 -m venv "$DATA/.venv" 2>/dev/null || true
  # shellcheck disable=SC1091
  source "$DATA/.venv/bin/activate"
  pip install -q cocoindex 2>/dev/null || warn "cocoindex install failed; skipping semantic index"
  if have cocoindex; then
    ( cd "$REPOS/$LEAGUE" && cocoindex index . --output "$INDEX/_semantic" 2>/dev/null ) \
      || warn "cocoindex index failed (needs an embedding model / config — see cocoindex.io)"
  fi
fi
log "done"
