---
title: 4. What the architecture predicts
weight: 4
---
A rubric is only worth trusting if its scores mean something. So the scores were tested: 24 San Diego
teams scored on the eight dimensions, each paired with season-matched Statbotics EPA (a normalized
strength rating built from match results), and the two correlated. The answer is honest rather than
triumphant. The full per-team scoresheet and the raw correlation tables are
[the San Diego scoresheet](../../scoring/34-the-san-diego-scoresheet.md).

## The headline: moderate, not decisive

Code sophistication correlates **moderately** with competition results — rubric total versus
normalized EPA is Spearman ρ ≈ 0.55. Better software is associated with better results, but it
explains only about a third of the variance. The full per-team scoresheet and the per-dimension
correlation table live in [the San Diego scoresheet](../../scoring/34-the-san-diego-scoresheet.md);
what matters here is the shape of the result, not the rows.

The per-dimension split has a clean reading. The signal concentrates in D8, D6, and D7, and nearly
vanishes in D3 and D4. D6 and D7 put points directly on the board — a team that runs real autos and
aligns to targets with vision scores more, immediately. D8 (CI, a carried library, docs, a
formatter) proxies overall program maturity, which sustains competitiveness across a season. D3 and
D4 — simulation and testing — are internal engineering investments whose payoff is robustness and
developer velocity, not raw match points; teams adopt them for reasons mostly orthogonal to a given
season's standings. (D4 is also near-constant — almost every team scores 0 — so its low correlation is
partly a low-variance artifact, not evidence that testing hurts.)

Because the link is loose, the mismatches carry most of the lesson — the sophisticated codebase that
finished in the bottom third of the state, and the minimal repo that posted a 72nd-percentile EPA.
Those outlier profiles are worked through in
[the scoresheet chapter](../../scoring/34-the-san-diego-scoresheet.md#the-outliers-are-the-interesting-part);
the conclusion they force is that code sophistication and competition performance are different
axes. The rubric measures the first; it does not pretend to measure the second.

## The confound, stated plainly

The most important caveat is that **most of what predicts EPA from "code" is size and program age, not
engineering quality.** A model of raw code features hits ρ ≈ 0.58 — but codebase size plus program
maturity *alone* scores ≈ 0.60, while the sophistication features with size removed score ≈ 0.38, and
a within-team view collapses to ≈ 0.05. Bigger, older, better-resourced programs have both more code
and better results. That D8 (program maturity) tops the dimension list is the same lurking variable
showing through. Do not read a high correlation as "good code wins," and do not reward sheer volume.

Other limits are real: n = 24 across mixed game years; shallow `.git`-stripped clones make D8 a floor;
EPA measures the whole robot and alliance context, not the software. A great controller can't
compensate for a slow intake or a no-show partner.

## What only the history could show

The validation across teams is a snapshot; the four-year deep dive on the Patribots is the
time-series. Re-cloned with full commit history and scored season by season, they show a clean
monotonic climb — Σ ≈ 5 → 10 → 17.5 → 20 (2024's 17.5 is the repo's final, post-rebuild state; the
robot that actually competed that season scored closer to ~12). The finding only the history could
reveal: the leap to elite-track scores happened **in the 2024 offseason, not in any build season.** The 2024 competition
robot ran on simple logging with no IO layer; the IO-layer/AdvantageKit rebuild landed in
July–August. That is [the "rewrite in the offseason" rule](03-the-maturity-ladder.md) showing up in a
real team's git log. The persistent gap across all four years, verified against every branch: not one
unit test has ever been written — which became the team's single highest-leverage next step. The full
four-season deep dive, with the year-by-year scoresheet and the commit evidence, is
[the Patribots, four years](../../scoring/35-the-patribots-four-years.md).

The honest conclusion: the architecture is worth building because it makes a program *faster and more
durable*, and it modestly tracks results — but it is not a substitute for a good robot. The next
section turns from "is it true" to "how do you build it," starting with [the foundation-first
order](05-foundation-first.md).
