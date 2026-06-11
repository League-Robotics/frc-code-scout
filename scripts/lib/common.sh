# Shared helpers. Source me. Resolves repo root regardless of caller CWD.
SCOUT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# Downloads + indexes can be large and require real delete perms (.git stripping).
# Default to data/ inside the repo, but override with SCOUT_DATA to point at native disk.
# IMPORTANT: do NOT point downloads at a cloud-synced / network-mounted folder —
# git's file-locking and .git removal can fail there. Use a plain local path.
DATA="${SCOUT_DATA:-$SCOUT_ROOT/data}"
REPOS="$DATA/repos"
INDEX="$DATA/index"
MANIFESTS="$SCOUT_ROOT/data/manifests"   # manifests are version-controlled, always in-repo
log()  { printf '\033[36m[scout]\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[33m[scout:warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31m[scout:err]\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
