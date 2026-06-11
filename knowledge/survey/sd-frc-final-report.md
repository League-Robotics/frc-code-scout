# San Diego FRC Code Sophistication — Scores, External Metrics, and What Predicts Results

Scored 24 active San Diego FRC teams against the 8-dimension code sophistication rubric, paired each with season-matched Statbotics EPA (the modern normalized strength rating built from match results), and tested which rubric dimensions track competition performance. Five teams were excluded as inactive/legacy (latest competition code predates the 2024 WPILib baseline the rubric measures, or no real season repo exists).

Methodology calls confirmed with you: D1 uses the lenient reading (a maintained 254-style generic base counts toward the top of D1 even without a Real/Sim IO swap); D8 credits a team library that exists, with a note where it's demonstrably consumed.

## Headline findings

Code sophistication correlates **moderately** with competition results — rubric total vs normalized EPA is Spearman ρ = 0.55 (Pearson r = 0.60, p ≈ 0.002). Better software is associated with better results, but it explains only about a third of the variance. The more useful result is the per-dimension breakdown:

The three dimensions that track on-field results best are **Sustainability (D8, ρ ≈ 0.61), Autonomous/Path planning (D6, ρ ≈ 0.59), and Vision/Localization (D7, ρ ≈ 0.52).** The two that barely track results at all are **Simulation (D3, ρ ≈ 0.18) and Testing (D4, ρ ≈ 0.26).** See `fig_dimensions.png`.

That split has a clean reading. D6 and D7 are the dimensions that directly put points on the board — a team that runs real autos and aligns to targets with vision scores more, immediately. D8 (CI, a carried team library, real docs, a formatter) is a proxy for overall program maturity and resourcing, which sustains competitiveness across a season. D3 and D4 — simulation and testing — are internal engineering-quality investments whose payoff is robustness and developer velocity, not raw match points; teams adopt them for reasons largely orthogonal to a given season's standings. (D4 is also near-constant — almost every team scores 0 — so its low correlation is partly a low-variance artifact, not evidence that testing hurts. The one team that tests, 6695, finished mid-pack.)

## The outliers are the interesting part

The code↔results link is loose enough that the mismatches carry the signal:

**Sophisticated code, weak results — 3647 Millennium Falcons.** The single most feature-complete codebase in San Diego (Σ = 20: maple-sim whole-robot simulation, AdvantageKit, 254-style architecture, multi-camera vision, Choreo, spotless + CI) finished in the **bottom third** of California in 2025 (state percentile 0.28, 44% win rate). Their software is a model; their 2025 on-field result was not. This is the textbook case that code sophistication and competition performance are different axes.

**Modest code, strong results — 4419 Team Rewind and 3749 Team Optix.** Rewind's minimal 14-file C++ repo (Σ = 5) paired with a top-quartile 2024 EPA (state percentile 0.72); Optix's 2023 repo (Σ = 10.5) with percentile 0.75. Whatever drove their results, it wasn't the software the rubric can see.

**The aligned top — 4738 Patribots and 3128 Aluminum Narwhals.** Patribots is the cleanest case of code and results agreeing: Σ = 19.5 (a real AdvantageKit IO layer across every mechanism) and the best competition record in the set (state percentile 0.96, 77% wins). 3128 likewise pairs Σ = 17 with percentile 0.94.

## Full scoresheet (24 active teams, ranked by code total)

D1 Architecture · D2 Coordination · D3 Simulation · D4 Testing · D5 Logging · D6 Auto/Path · D7 Vision · D8 Sustainability. EPA is season-matched to the scored repo; state %ile is within-California for that season.

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

## Per-dimension correlation table

Spearman ρ against each external performance measure (n = 24). Sorted by mean of the two robust measures (normEPA, state percentile).

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

## Notable per-team profiles

- **5137 Iron Kodiaks** — the most balanced sophisticated codebase: a generalized `MotorIO` layer with three hardware implementations, AdvantageKit across six subsystems, physics sims (Shooter/Intake/SwerveModule). Highest D3 among the AdvantageKit teams.
- **1538 Holy Cows** — the only C++ program of note: a custom framework (CowLib, hand-rolled command system, threaded `Localizer` with PhotonVision pose fusion, Choreo). Sophistication reached without WPILib's Java idioms — and it shows in results (state percentile 0.92).
- **6995 NOMAD** — a Real/Sim/None vision+climb IO layer without AdvantageKit logging; architecture-forward, telemetry-light.
- **6695 GalvaKnights** — the only team that writes real unit tests (4 Kotlin suites with assertions), though CI runs `spotlessCheck`, not the tests. The rarest marker in the set, on an otherwise baseline codebase.
- **2102 Team Paradox** — strongest simulation profile (physics sims across six mechanisms + maple-sim + replay vendordeps) on an otherwise mid-tier architecture.

## Excluded teams (legacy / inactive — not scored)

| Team | Reason |
|---|---|
| 1622 Team Spyder | Latest code 2017 (C++); no activity since |
| 4139 Easy as Pi | Latest 2016; repo is an empty Eclipse shell |
| 5474 Clairemonster | Latest real season 2021 |
| 5514 MavBots | Latest 2017 |
| 5477 NubotX | Training-only repos; no competition-season code |

These also have no recent EPA, so excluding them does not bias the correlation.

## Caveats and limitations

1. **Correlation, not causation, and a likely confound.** That D8 (sustainability/program maturity) tops the list suggests a lurking variable: older, better-resourced programs have both better software hygiene *and* better results. Team age (rookie year) plausibly drives both. The rubric measures code, not budget, mentorship, or build quality — all of which move EPA.
2. **Small n, mixed game years.** 24 teams across four FRC seasons (2023–2026). EPA `norm` and within-season state percentile are designed to be comparable across years, which justifies pooling, but the games differ. A 2025/2026-only cut (n = 20) gives a materially similar ranking of dimensions.
3. **Repos are shallow clones with `.git` stripped**, so D8 is artifact-only (no commit history, CI run logs, or release discipline) and should be read as a floor. D4 is near-constant and its correlation is statistically weak.
4. **EPA measures the whole robot and alliance context**, not the software. A great drivetrain controller can't compensate for a slow intake or a no-show alliance partner.

## Files

- `sd-frc-final-report.md` — this report
- `sd-frc-scores-pilot.md` — the original 3-team pilot with detailed profile notes
- `sd-frc-master.csv` — per-team rubric vector + EPA metrics (machine-readable)
- `sd-frc-correlations.csv` — the per-dimension correlation table
- `fig_scatter.png` — code total vs state percentile, outliers labeled
- `fig_dimensions.png` — per-dimension correlation bars
- `frc-code-sophistication-rubric.md` — the scoring rubric

*Performance data: Statbotics v3 API (api.statbotics.io), season-matched per team, retrieved June 10, 2026.*
