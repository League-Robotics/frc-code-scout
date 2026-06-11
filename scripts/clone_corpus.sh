#!/usr/bin/env bash
# Download (and clean) team repositories listed in a manifest.
#
# Usage:
#   scripts/clone_corpus.sh [options]
#   --manifest FILE   TSV: team_id<TAB>name<TAB>owner<TAB>space-separated-repos
#                     (default: data/manifests/frc-teams.tsv)
#   --league frc|ftc  Sets default manifest + dest subdir (default: frc)
#   --team ID         Only this team (repeatable)
#   --dest DIR        Output root (default: data/repos/<league>)
#   --with-git        Keep full .git history (default: shallow depth=1, .git stripped)
#   --keep-media      Keep CAD/video/large binaries (default: strip them)
#   --keep-logs       Keep replay/match logs (.wpilog/.hoot/.rlog/.dslog) for log-replay analysis
#   --budget SECONDS  Stop after N seconds (resumable; rerun to continue). 0 = no limit
#   --depth N         Shallow clone depth when not --with-git (default 1)
#   -h|--help
set -uo pipefail
source "$(dirname "$0")/lib/common.sh"

LEAGUE=frc; MANIFEST=""; DEST=""; WITH_GIT=0; KEEP_MEDIA=0; KEEP_LOGS=0; BUDGET=0; DEPTH=1
declare -a ONLY=()
while [ $# -gt 0 ]; do case "$1" in
  --manifest) MANIFEST="$2"; shift 2;;
  --league) LEAGUE="$2"; shift 2;;
  --team) ONLY+=("$2"); shift 2;;
  --dest) DEST="$2"; shift 2;;
  --with-git) WITH_GIT=1; shift;;
  --keep-media) KEEP_MEDIA=1; shift;;
  --keep-logs) KEEP_LOGS=1; shift;;
  --budget) BUDGET="$2"; shift 2;;
  --depth) DEPTH="$2"; shift 2;;
  -h|--help) sed -n '2,20p' "$0"; exit 0;;
  *) die "unknown arg: $1";;
esac; done
: "${MANIFEST:=$MANIFESTS/${LEAGUE}-teams.tsv}"
: "${DEST:=$REPOS/$LEAGUE}"
[ -f "$MANIFEST" ] || die "manifest not found: $MANIFEST"
mkdir -p "$DEST"
START=$SECONDS

strip_repo() {
  local d="$1"
  [ "$WITH_GIT" -eq 1 ] || rm -rf "$d/.git"
  if [ "$KEEP_MEDIA" -eq 0 ]; then
    find "$d" -type f \( -iname '*.stl' -o -iname '*.step' -o -iname '*.stp' -o -iname '*.sldprt' \
      -o -iname '*.sldasm' -o -iname '*.f3d' -o -iname '*.dxf' -o -iname '*.dwg' -o -iname '*.iges' \
      -o -iname '*.obj' -o -iname '*.3mf' -o -iname '*.mp4' -o -iname '*.mov' -o -iname '*.avi' \
      -o -iname '*.mkv' -o -iname '*.webm' -o -iname '*.psd' -o -iname '*.7z' -o -iname '*.rar' \
      -o -iname '*.jar' -o -iname '*.apk' -o -iname '*.so' -o -iname '*.dll' -o -iname '*.dylib' \
      -o -iname '*.onnx' -o -iname '*.tflite' -o -iname '*.pb' -o -iname '*.pt' -o -iname '*.h5' \) -delete 2>/dev/null
    find "$d" -type f -size +2M -delete 2>/dev/null
  fi
  if [ "$KEEP_LOGS" -eq 0 ]; then
    find "$d" -type f \( -iname '*.wpilog' -o -iname '*.hoot' -o -iname '*.rlog' -o -iname '*.dslog' -o -iname '*.bag' \) -delete 2>/dev/null
  fi
  find "$d" -type d -empty -delete 2>/dev/null
}

want_team() { [ ${#ONLY[@]} -eq 0 ] && return 0; for t in "${ONLY[@]}"; do [ "$t" = "$1" ] && return 0; done; return 1; }

tail -n +2 "$MANIFEST" | while IFS=$'\t' read -r tid name owner repos; do
  [ -z "${tid:-}" ] && continue
  want_team "$tid" || continue
  for repo in $repos; do
    tgt="$DEST/${tid}-${name}/${repo}"
    [ -d "$tgt" ] && { log "skip (exists) $tid/$repo"; continue; }
    if [ "$BUDGET" -gt 0 ] && [ $((SECONDS-START)) -ge "$BUDGET" ]; then log "BUDGET_REACHED — rerun to continue"; exit 0; fi
    mkdir -p "$(dirname "$tgt")"
    if [ "$WITH_GIT" -eq 1 ]; then args=(); else args=(--depth "$DEPTH"); fi
    if timeout 60 git clone -q "${args[@]}" "https://github.com/$owner/$repo.git" "$tgt.tmp" 2>/dev/null; then
      strip_repo "$tgt.tmp"; mv "$tgt.tmp" "$tgt"
      log "OK   $tid/$repo ($(du -sh "$tgt" 2>/dev/null | cut -f1))"
    else
      rm -rf "$tgt.tmp"; warn "FAIL $owner/$repo"
    fi
  done
done
log "ALLDONE"
