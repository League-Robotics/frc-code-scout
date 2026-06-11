#!/usr/bin/env bash
# Discover repos for a team (or find new teams) on GitHub and emit manifest lines.
#
# Usage:
#   scripts/discover_repos.sh --owner OWNER [--team-id ID] [--name NAME] [--append LEAGUE]
#       List every non-fork repo under a GitHub org/user, newest first.
#   scripts/discover_repos.sh --search "QUERY"
#       Search GitHub for candidate orgs/repos (e.g. "FRC 1234", "San Diego robotics").
#
# Auth: uses `gh` CLI if available (gh auth login), else anonymous GitHub REST
# (rate-limited to 60 req/hr — set GITHUB_TOKEN to raise it).
set -uo pipefail
source "$(dirname "$0")/lib/common.sh"

OWNER=""; QUERY=""; TID=""; NAME=""; APPEND=""
while [ $# -gt 0 ]; do case "$1" in
  --owner) OWNER="$2"; shift 2;; --search) QUERY="$2"; shift 2;;
  --team-id) TID="$2"; shift 2;; --name) NAME="$2"; shift 2;;
  --append) APPEND="$2"; shift 2;;
  -h|--help) sed -n '2,14p' "$0"; exit 0;;
  *) die "unknown arg: $1";;
esac; done

api() { # $1 = path
  if have gh; then gh api "$1" 2>/dev/null
  elif have curl; then curl -fsSL ${GITHUB_TOKEN:+-H "Authorization: Bearer $GITHUB_TOKEN"} "https://api.github.com/$1"
  else die "need gh or curl"; fi
}

if [ -n "$QUERY" ]; then
  log "Searching GitHub repos for: $QUERY"
  api "search/repositories?q=$(printf '%s' "$QUERY" | sed 's/ /+/g')&sort=updated&per_page=20" \
    | python3 -c 'import sys,json;[print(f"{r[\"full_name\"]:45} ⭐{r[\"stargazers_count\"]:<4} {r.get(\"description\") or \"\"}") for r in json.load(sys.stdin).get("items",[])]'
  exit 0
fi

[ -n "$OWNER" ] || die "need --owner or --search"
log "Listing repos for owner: $OWNER"
repos=$(api "users/$OWNER/repos?per_page=100&sort=pushed&type=owner" \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(" ".join(r["name"] for r in d if not r.get("fork")))')
[ -n "$repos" ] || die "no repos found (rate-limited? set GITHUB_TOKEN)"
: "${TID:=UNKNOWN}"; : "${NAME:=$OWNER}"
line=$(printf "%s\t%s\t%s\t%s" "$TID" "$NAME" "$OWNER" "$repos")
echo "$line"
if [ -n "$APPEND" ]; then
  echo "$line" >> "$MANIFESTS/${APPEND}-teams.tsv"; log "appended to ${APPEND}-teams.tsv"
fi
