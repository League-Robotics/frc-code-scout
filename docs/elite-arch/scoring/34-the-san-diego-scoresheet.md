---
title: 34. The San Diego scoresheet
weight: 34
---


**This whole book makes a claim — that the architecture on these pages is what separates elite robot code from the rest — and a claim that big deserves to be checked against reality, not just asserted.** So we ran the rubric on our own backyard. We scored 24 active San Diego FRC teams on the D1–D8 dimensions, paired each with its season-matched [Statbotics](https://www.statbotics.io/) EPA — the modern, normalized strength rating built purely from match results — and asked the blunt question: does better code actually correlate with winning? The short answer is *yes, moderately, and unevenly* — and the uneven part is where the real lessons live. This appendix is the receipt. For what the architecture is *supposed* to predict, see [what the architecture predicts](../appendices/how-we-developed-this/04-what-it-predicts.md); for the scoring instrument itself, see [the rubric in full](33-the-rubric.md).

## What the study was

Twenty-four active San Diego FRC teams, scored on the eight-dimension code-sophistication rubric, each paired with the Statbotics EPA of the exact season repo we scored. Five more teams were excluded as inactive or legacy — their newest competition code predates the 2024 WPILib baseline the rubric measures, or no real season repo exists — and since those teams also carry no recent EPA, dropping them doesn't bias the correlation. Two methodology calls shaped the numbers: D1 uses the lenient reading (a maintained 254-style generic base counts toward the top of D1 even without a Real/Sim IO swap), and D8 credits a team library that demonstrably exists.

The dimensions, abbreviated throughout: **D1** Architecture · **D2** Coordination · **D3** Simulation · **D4** Testing · **D5** Logging · **D6** Autonomous/Path planning · **D7** Vision/Localization · **D8** Sustainability. EPA is season-matched to the scored repo; the state percentile (`st%ile`) is that team's standing within California *for that season*, so a 2023 repo is ranked against 2023 California, not 2026.

The raw data behind every table below lives in two machine-readable files. `sd-frc-master.csv` carries one row per team — team number, name, season, language, the eight rubric scores, the total, and four external metrics (`norm_EPA`, `state_pctile`, `winrate`, `epa_points`). `sd-frc-correlations.csv` carries one row per dimension — its code (D1…D8) and its Spearman ρ against each of the three external measures (`spearman_normEPA`, `spearman_state_pctile`, `spearman_winrate`). The tables here are those two files, read straight.

## The full scoresheet

Twenty-four active teams, ranked by code total. Σ is out of 32.

| # | Team | Season | Lang | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | Σ/32 | normEPA | st%ile | win% |
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| 1 | 3647 Millennium Falcons | 2025 | Java | 3.5 | 3 | 3 | 0 | 2 | 3 | 3 | 2.5 | 20 | 1456 | 28 | 44 |
| 2 | 4738 Patribots | 2025 | Java | 3 | 2.5 | 2 | 0 | 3 | 3 | 3 | 3 | 19.5 | 1735 | 96 | 77 |
| 3 | 5137 Iron Kodiaks | 2026 | Java | 3.5 | 2 | 2.5 | 0 | 3 | 2 | 2.5 | 2 | 17.5 | 1594 | 78 | 46 |
| 4 | 1538 Holy Cows | 2025 | C++ | 3 | 2 | 1.5 | 0.5 | 2 | 3 | 3 | 2 | 17 | 1670 | 92 | 65 |
| 5 | 3128 Aluminum Narwhals | 2025 | Java | 3.5 | 3 | 1 | 0 | 1 | 3 | 2.5 | 3 | 17 | 1721 | 94 | 70 |
| 6 | 6995 NOMAD | 2026 | Java | 3 | 1.5 | 1.5 | 0 | 1.5 | 3 | 3 | 2 | 15.5 | 1669 | 88 | 62 |
| 7 | 3255 SuperNURDs | 2026 | Java | 2 | 2 | 0.5 | 0 | 2 | 3 | 2.5 | 3 | 15 | 1744 | 96 | 62 |
| 8 | 2485 Overclocked | 2026 | Java | 2 | 1.5 | 1 | 0 | 2 | 2.5 | 3 | 2 | 14 | 1537 | 67 | 44 |
| 9 | 2102 Team Paradox | 2026 | Java | 2 | 1 | 3 | 0 | 1.5 | 3 | 2 | 1 | 13.5 | 1658 | 87 | 64 |
| 10 | 3341 Option 16 | 2026 | Java | 2 | 2 | 1.5 | 0 | 1.5 | 2 | 2 | 1.5 | 12.5 | 1447 | 24 | 48 |
| 11 | 1572 Hammer Heads | 2024 | Java | 2 | 1.5 | 1 | 0 | 2 | 2 | 2 | 1.5 | 12 | 1523 | 56 | 54 |
| 12 | 6695 GalvaKnights | 2026 | Kotlin | 1.5 | 1 | 0.5 | 2 | 1 | 2 | 1.5 | 2.5 | 12 | 1564 | 72 | 41 |
| 13 | 2658 Sigma Motion | 2026 | Java | 2 | 1 | 1 | 0 | 2 | 2 | 2 | 1.5 | 11.5 | 1479 | 42 | 52 |
| 14 | 4160 RoBucs | 2026 | Java | 2 | 1 | 1.5 | 0 | 1.5 | 2 | 2 | 1.5 | 11.5 | 1485 | 46 | 41 |
| 15 | 8891 Wild Raccoons | 2024 | Java | 1.5 | 2 | 0.5 | 0 | 1 | 2.5 | 1.5 | 2 | 11 | 1515 | 52 | 52 |
| 16 | 3749 Team Optix | 2023 | Java | 1.5 | 1 | 0.5 | 0 | 1 | 2 | 2.5 | 2 | 10.5 | 1574 | 75 | 47 |
| 17 | 4919 Team Ronin | 2026 | Java | 1.5 | 1 | 1 | 0 | 1.5 | 2 | 2 | 1.5 | 10.5 | 1449 | 26 | 46 |
| 18 | 0812 Midnight Mechanics | 2026 | Java | 1.5 | 1 | 1.5 | 0 | 1 | 1.5 | 2 | 1.5 | 10 | 1546 | 68 | 56 |
| 19 | 9573 MarauderTech | 2026 | Java | 2 | 1 | 1 | 0 | 1 | 1 | 2 | 1 | 9 | 1415 | 12 | 21 |
| 20 | 9730 Metal Maniacs | 2026 | Java | 1 | 1 | 1 | 0 | 1 | 2 | 1.5 | 1 | 8.5 | 1470 | 36 | 33 |
| 21 | 2839 Daedalus | 2026 | Java | 1.5 | 1 | 0.5 | 0 | 0.5 | 1 | 0 | 1 | 5.5 | 1347 | 2 | 25 |
| 22 | 2984 Vikings | 2024 | Python | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 5 | 1462 | 29 | 22 |
| 23 | 4419 Team Rewind | 2024 | C++ | 1 | 1 | 0 | 0.5 | 1 | 0.5 | 0 | 1 | 5 | 1564 | 72 | 46 |
| 24 | 5025 Pacific Steel | 2023 | Java | 1 | 1 | 0 | 0 | 1 | 0.5 | 0 | 1 | 4.5 | 1492 | 46 | 55 |

## What predicts results

Rubric total versus normalized EPA lands at Spearman **ρ = 0.55** (Pearson r = 0.60, p ≈ 0.002). Better software *is* associated with better results — but it explains only about a third of the variance. The headline number is real, and it is modest; anyone who tells you clean code guarantees banners is overselling.

The per-dimension breakdown is the more useful cut. Spearman ρ against each external measure, n = 24, sorted by how strongly the dimension tracks the two most robust measures:

| Dimension | vs normEPA | vs state %ile | vs win rate |
|---|---|---|---|
| D8 Sustainability | 0.60 | 0.62 | 0.45 |
| D6 Autonomous/Path | 0.59 | 0.60 | 0.59 |
| D7 Vision/Localization | 0.51 | 0.52 | 0.47 |
| D2 Coordination | 0.41 | 0.41 | 0.49 |
| D1 Architecture | 0.39 | 0.41 | 0.44 |
| D5 Logging | 0.35 | 0.36 | 0.39 |
| D4 Testing | 0.26 | 0.26 | −0.01 |
| D3 Simulation | 0.17 | 0.20 | 0.33 |
| **Total Σ** | **0.55** | **0.56** | **0.51** |

Three dimensions carry the signal: **Sustainability (D8, ρ ≈ 0.61)**, **Autonomous/Path planning (D6, ρ ≈ 0.59)**, and **Vision/Localization (D7, ρ ≈ 0.52)**. Two barely register: **Simulation (D3, ρ ≈ 0.18)** and **Testing (D4, ρ ≈ 0.26)**.

That split has a clean reading. D6 and D7 are the dimensions that put points on the board *directly* — a team that runs real autos and aligns to targets with vision scores more, immediately. D8 (CI, a carried team library, real docs, a formatter) is a proxy for overall program maturity and resourcing, which sustains competitiveness across a season. D3 and D4 — simulation and testing — are internal engineering-quality investments whose payoff is robustness and developer velocity, not raw match points; teams adopt them for reasons largely orthogonal to a given season's standings. And a caution on D4: it is near-constant here — almost every team scores 0 — so its low correlation is partly a low-variance artifact, not evidence that testing hurts. The one team that genuinely tests, 6695 GalvaKnights, finished mid-pack.

## The outliers are the interesting part

A correlation of 0.55 is loose enough that the mismatches carry most of the signal. Three profiles are worth memorizing.

**Sophisticated code, weak results — 3647 Millennium Falcons.** The single most feature-complete codebase in San Diego (Σ = 20: maple-sim whole-robot simulation, AdvantageKit, 254-style architecture, multi-camera vision, Choreo, spotless + CI) finished in the *bottom third* of California in 2025 — state percentile 28, a 44% win rate. Their software is a model the rest of this book could be written from; their 2025 on-field result was not. This is the textbook case that code sophistication and competition performance are different axes, and that a robot is more than its repo.

**Modest code, strong results — 4419 Team Rewind and 3749 Team Optix.** Rewind's minimal 14-file C++ repo (Σ = 5) paired with a top-quartile 2024 EPA (state percentile 72); Optix's 2023 repo (Σ = 10.5) with percentile 75. Whatever drove those results, it wasn't software the rubric can see — a fast, reliable mechanism and a good driver don't show up in an AST scan.

**The aligned top — 4738 Patribots and 3128 Aluminum Narwhals.** Patribots is the cleanest case of code and results agreeing: Σ = 19.5 (a real AdvantageKit IO layer across *every* mechanism) and the best competition record in the set — state percentile 96, 77% wins. 3128 pairs Σ = 17 with percentile 94. When the architecture is real and the program is strong, the two axes line up — which is the outcome this book is arguing for. The Patribots' four-year climb to that point is its own study; see [the Patribots case study](35-the-patribots-four-years.md).

## A few per-team notes worth keeping

- **5137 Iron Kodiaks** — the most balanced sophisticated codebase: a generalized `MotorIO` layer with three hardware implementations, AdvantageKit across six subsystems, physics sims (Shooter/Intake/SwerveModule). Highest D3 among the AdvantageKit teams.
- **1538 Holy Cows** — the only C++ program of note: a custom framework (CowLib, a hand-rolled command system, a threaded `Localizer` with PhotonVision pose fusion, Choreo). Sophistication reached without WPILib's Java idioms — and it shows in the results (state percentile 92).
- **6995 NOMAD** — a Real/Sim/None vision-and-climb IO layer *without* AdvantageKit logging: architecture-forward, telemetry-light.
- **6695 GalvaKnights** — the only team that writes real unit tests (4 Kotlin suites with assertions), though CI runs `spotlessCheck`, not the tests. The rarest marker in the set, sitting on an otherwise baseline codebase.
- **2102 Team Paradox** — the strongest simulation profile (physics sims across six mechanisms plus maple-sim and replay vendordeps) on an otherwise mid-tier architecture.

## Caveats — read these before you quote the number

The 0.55 is honest, but it is a small, imperfect study, and it deserves to be reported with its limits attached.

1. **Correlation, not causation, and a likely confound.** That D8 (sustainability / program maturity) tops the list suggests a lurking variable: older, better-resourced programs have both better software hygiene *and* better results. Team age (rookie year) plausibly drives both. The rubric measures code, not budget, mentorship, or build quality — all of which move EPA.
2. **Small n, mixed game years.** Twenty-four teams across four FRC seasons (2023–2026). Normalized EPA and within-season state percentile are designed to be comparable across years, which justifies pooling, but the games differ. A 2025/2026-only cut (n = 20) gives a materially similar ranking of dimensions.
3. **Repos are shallow clones with `.git` stripped**, so D8 is artifact-only — no commit history, CI run logs, or release discipline — and should be read as a floor. D4 is near-constant and its correlation is statistically weak.
4. **EPA measures the whole robot and its alliance context**, not the software. A great drivetrain controller can't compensate for a slow intake or a no-show alliance partner.

The takeaway is not "write clean code and you will win." It is narrower and more defensible: the dimensions that either put points on the board (D6, D7) or index a mature, well-resourced program (D8) track results; the dimensions that are pure internal engineering investment (D3, D4) do not track a single season's standings — which is exactly what you'd expect, and exactly why you should still do them. The architecture in this book is the machinery that makes D6 and D7 *cheap and reliable* to build, and makes D8 a byproduct rather than a chore.

*Performance data: Statbotics v3 API (api.statbotics.io), season-matched per team, retrieved June 10, 2026.*

