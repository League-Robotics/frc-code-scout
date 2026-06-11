---
name: analyze-team
description: Score one FRC/FTC team's code against the 8-dimension sophistication rubric and write a report comparing them to the rubric and to the San Diego peer survey. Use when the user names a team (e.g. "score the Patribots", "analyze team 3128", "how good is 1538's code") or wants a single-team or multi-year code review with prioritized next steps.
---

# Analyze a team

Produce a file-confirmed rubric score and a report for one team, benchmarked against the
rubric anchors and the 24-team San Diego survey.

## Collect first
- Which team (number/name)? Which season(s) — latest only, or a multi-year trajectory?
- If they care about *when* architecture was adopted, you need git history (`--with-git`).

## Steps
1. **Read the rubric** — `knowledge/rubric/rubric.md` (all 8 dimensions, anchors, profile
   shapes). Never score from memory.
2. **Locate the team** in `data/manifests/frc-teams.tsv`. If absent:
   `scripts/discover_repos.sh --owner <org> --team-id <num> --name <slug> --append frc`
3. **Download** — `scripts/clone_corpus.sh --team <num>` (add `--with-git` for trajectory).
   Set `SCOUT_DATA` to a local path if this repo sits on a synced drive.
4. **Index** — `scripts/build_index.sh --team <num>`.
5. **Candidate scores** — for each season repo:
   `scripts/score_rubric.sh --repo data/repos/frc/<num>-<name>/<repo>`
6. **CONFIRM (the core).** Open every cited evidence file; verify each indicator is *used*,
   not just present. Adjust levels (half-steps allowed). Probes:
   - `ast-grep run -l java -p '$E.addVisionMeasurement($$$)' <repo>`  (D7 wiring)
   - `ast-grep run -l java -p 'interface $N' <repo> | grep IO`  then check ≥2 impls (D1)
   - confirm `@AutoLog`/`processInputs` spans most subsystems, not one (D5)
   - open the Superstructure: real goal API + guarded transitions, or a holder? (D2)
7. **Trajectory (if `--with-git`)** — `git -C <repo> log` to find *when* each capability
   landed and whether in build-season or offseason.
8. **Benchmark** — rank within `knowledge/survey/sd-frc-master.csv`; cite which dimensions
   track results (`knowledge/survey/sd-frc-correlations.csv`).
9. **Recommend** — map gaps to seams in `knowledge/build-spec/elite-architecture.md`; give
   ONE highest-leverage next step.
10. **Write** from `templates/team-report.md`; offer a PDF.

Worked reference: `knowledge/examples/patribots-four-year-scoring.md`.
Sample raw engine output: `knowledge/examples/sample-score-output-reefscape2025.md`.
