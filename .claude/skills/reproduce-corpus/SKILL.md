---
name: reproduce-corpus
description: Re-download every tracked team's code, discover repos for teams not yet tracked, index it all for fast AST search, and answer questions across the whole corpus. Use when the user wants to rebuild or refresh the dataset, add new teams, re-run the full San Diego survey, or ask cross-team questions like "which teams use a state machine" or "who writes tests".
---

# Reproduce / extend the corpus

Rebuild the analysis dataset and query it across teams.

## Steps
1. **Download everything** — `scripts/clone_corpus.sh` (whole manifest). Flags:
   `--with-git` keep history · `--keep-logs` keep replay logs (`.wpilog/.hoot/.rlog`,
   for log-replay analysis) · `--keep-media` keep CAD/video · `--budget N` time-box and
   resume (rerun until it prints ALLDONE) · `--league ftc` for FTC.
   Point `SCOUT_DATA` at a local disk.
2. **Add missing teams** — `scripts/discover_repos.sh --search "San Diego FRC"` to find
   candidates, then `--owner <org> --team-id <n> --name <slug> --append frc` per team.
3. **Index** — `scripts/build_index.sh` (whole corpus). Add `--semantic` to also build a
   cocoindex embedding index for natural-language code search.
4. **Ask the corpus** (examples):
   - State machines: `ast-grep scan --config sgconfig.yml data/repos --json` then filter
     rule id `d2-superstructure-class` / `d2-state-enum`.
   - Who tests: `ast-grep run -l java -p '@Test' data/repos`
   - Every IO interface: `ast-grep run -l java -p 'interface $N' data/repos | grep IO`
   - Choreo adopters: search rule id `d6-choreo` in the scan JSON.
   - Semantic (if `--semantic`): query the cocoindex index for "vision pose rejection".
5. **Re-run the survey** — score each team's latest real season repo with
   `scripts/score_rubric.sh`, confirm levels, and assemble a master CSV in the shape of
   `knowledge/survey/sd-frc-master.csv`. Pair with current Statbotics EPA if redoing the
   correlation analysis (see `knowledge/survey/sd-frc-final-report.md` for method).

Method reference: `knowledge/examples/methodology.md`.
