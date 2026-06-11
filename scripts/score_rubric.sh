#!/usr/bin/env bash
# Generate CANDIDATE rubric levels + evidence for one repo.
# This does the mechanical pass (ast-grep AST hits + filesystem checks).
# An agent/human MUST confirm each level by opening the cited files — the rubric
# rule is "score what's used, not what's present."
#
# Usage: scripts/score_rubric.sh --repo PATH [--md OUTFILE]
set -uo pipefail
source "$(dirname "$0")/lib/common.sh"
REPO=""; MD=""
while [ $# -gt 0 ]; do case "$1" in
  --repo) REPO="$2"; shift 2;; --md) MD="$2"; shift 2;;
  -h|--help) sed -n '2,11p' "$0"; exit 0;; *) die "unknown arg: $1";; esac; done
[ -d "$REPO" ] || die "repo not found: $REPO"
have ast-grep || die "ast-grep not installed (run build_index.sh)"

HITS_FILE=$(mktemp)
ast-grep scan --config "$SCOUT_ROOT/sgconfig.yml" "$REPO" --json 2>/dev/null > "$HITS_FILE" || echo '[]' > "$HITS_FILE"
trap 'rm -f "$HITS_FILE"' EXIT

# filesystem signals
fs() { find "$REPO" "$@" 2>/dev/null; }
grepc() { grep -rIl "$1" "$REPO" --include="$2" 2>/dev/null | wc -l | tr -d ' '; }
TEST_FILES=$(fs -path '*src/test*' -name '*.java' | wc -l | tr -d ' ')
CI_TEST=$( { fs -path '*.github/workflows*' -name '*.yml' -exec grep -l 'gradle.*test\|gradlew test' {} \; ; } | wc -l | tr -d ' ')
CI_ANY=$(fs -path '*.github/workflows*' -name '*.yml' | wc -l | tr -d ' ')
VEND() { ls "$REPO"/vendordeps/*"$1"* >/dev/null 2>&1 && echo yes || echo no; }
PP_PATHS=$(fs -path '*deploy/pathplanner/paths*' -name '*.path' | wc -l | tr -d ' ')
TRAJ=$(fs \( -name '*.traj' -o -name '*.chor' \) | wc -l | tr -d ' ')
README_LINES=$( [ -f "$REPO/README.md" ] && wc -l < "$REPO/README.md" | tr -d ' ' || echo 0)
SPOTLESS=$(grep -rIl 'spotless\|checkstyle' "$REPO" --include=build.gradle 2>/dev/null | wc -l | tr -d ' ')

export REPO TEST_FILES CI_TEST CI_ANY PP_PATHS TRAJ README_LINES SPOTLESS
ADV=$(VEND AdvantageKit); PHO=$(VEND hoton); CHO=$(VEND horeo); export ADV PHO CHO

python3 - "$REPO" "$HITS_FILE" <<'PY'
import json, os, sys, collections
repo = sys.argv[1]
hits = json.load(open(sys.argv[2])) if os.path.getsize(sys.argv[2])>0 else []
bydim = collections.defaultdict(list)
for h in hits:
    rid = h.get("ruleId","")
    dim = rid[:2].upper() if rid[:1]=="d" else "??"
    rng = h.get("range",{}).get("start",{}).get("line",0)+1
    f = os.path.relpath(h.get("file",""), repo)
    bydim[dim].append((rid, f, rng, h.get("text","").splitlines()[0][:70]))
def n(d): return len(bydim.get(d,[]))
g=os.environ.get
out=[]
out.append(f"# Rubric evidence — `{os.path.basename(repo.rstrip('/'))}`\n")
out.append("Mechanical candidates from ast-grep + filesystem. **Confirm every level by opening the cited files.**\n")
# crude candidate heuristics (floor) per dimension
cand={}
cand["D1"]= 3 if n("D1")>=3 else (2 if n("D1")>=1 else 1)
cand["D2"]= 3 if any('superstructure' in x[0] for x in bydim.get("D2",[])) else (2 if n("D2")>=1 else 1)
cand["D3"]= 2 if any('mechanism-sim' in x[0] for x in bydim.get("D3",[])) else (1 if n("D3")>=1 else 0)
nd4=sum(1 for x in bydim.get("D4",[]) if 'junit' in x[0])
cand["D4"]= 0 if (nd4==0 and int(g("TEST_FILES","0"))==0) else (3 if int(g("CI_TEST","0"))>0 else 2)
has_adv = g("ADV")=="yes" or any('autolog' in x[0] or 'process-inputs' in x[0] for x in bydim.get("D5",[]))
cand["D5"]= 3 if has_adv else (1 if n("D5")>=1 else 0)
cand["D6"]= 4 if any('repulsor' in x[0] for x in bydim.get("D6",[])) else (3 if (int(g("TRAJ","0"))>0 or any('choreo' in x[0] or 'pathfinding' in x[0] for x in bydim.get("D6",[]))) else (2 if int(g("PP_PATHS","0"))>0 else 1))
cand["D7"]= 4 if any('robotstate' in x[0] for x in bydim.get("D7",[])) else (3 if any('stddev' in x[0] for x in bydim.get("D7",[])) else (2 if n("D7")>=1 else 0))
cand["D8"]= 3 if int(g("CI_ANY","0"))>0 and int(g("README_LINES","0"))>20 else (2 if int(g("README_LINES","0"))>20 else 1)
names={"D1":"Architecture","D2":"Coordination","D3":"Simulation","D4":"Testing","D5":"Logging","D6":"Auto/Path","D7":"Vision","D8":"Sustain"}
out.append("| Dim | Candidate | AST hits | Key filesystem signal |")
out.append("|---|---|---|---|")
fsig={"D1":f"{n('D1')} IO/inputs decls","D2":f"{n('D2')} state/coord decls","D3":f"sim hits {n('D3')}",
 "D4":f"test files {g('TEST_FILES')}, CI-test {g('CI_TEST')}","D5":f"AdvKit vendordep={g('ADV')}",
 "D6":f"PP paths {g('PP_PATHS')}, traj/chor {g('TRAJ')}","D7":f"{n('D7')} vision hits","D8":f"README {g('README_LINES')}L, CI {g('CI_ANY')}, spotless {g('SPOTLESS')}"}
tot=0
for d in ["D1","D2","D3","D4","D5","D6","D7","D8"]:
    tot+=cand[d]; out.append(f"| {d} {names[d]} | **{cand[d]}** | {n(d)} | {fsig[d]} |")
out.append(f"\n**Heuristic Σ (floor): {tot}/32** — candidates only; confirm before reporting.\n")
out.append("## Evidence (open these)\n")
for d in ["D1","D2","D3","D4","D5","D6","D7","D8"]:
    if bydim.get(d):
        out.append(f"\n### {d} {names[d]}")
        for rid,f,ln,txt in bydim[d][:12]:
            out.append(f"- `{f}:{ln}` — {rid} — `{txt}`")
print("\n".join(out))
PY
