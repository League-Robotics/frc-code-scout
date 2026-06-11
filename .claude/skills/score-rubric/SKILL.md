---
name: score-rubric
description: Run the mechanical rubric pass (ast-grep AST matches + filesystem checks) on a single already-downloaded repo to get candidate D1-D8 levels and the evidence behind each. Use as a sub-step of analyze-team, or when the user wants a quick candidate score of one repo path.
---

# Score one repo against the rubric

`scripts/score_rubric.sh --repo <path>` prints candidate levels D1-D8, a heuristic
floor total, and the file:line evidence for every AST hit, grouped by dimension.

These are **candidates only.** The script cannot tell "used" from "present" — it counts
`@AutoLog` but not whether coverage spans subsystems; it sees a `Superstructure` class but
not whether it has guarded transitions. Always open the evidence files and adjust before
reporting. The rubric anchors and the confirm-don't-assume rule are in
`knowledge/rubric/rubric.md`.

To refine by hand, run ast-grep patterns directly, e.g.
`ast-grep run -l java -p 'new ElevatorSim($$$)' <repo>` or scan with the project rules
`ast-grep scan --config sgconfig.yml <repo>`.
