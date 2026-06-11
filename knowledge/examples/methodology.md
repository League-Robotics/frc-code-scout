# How We Did It: Methodology for the San Diego FRC Code-Sophistication Study

*A reconstruction of the full pipeline — from a national corpus of robot code, to a scoring rubric, to a ranked survey of every active San Diego FRC team, to a four-year deep dive on the Patribots (FRC 4738). Written from the project's own artifacts.*

---

## What we were trying to answer

Two questions sit underneath everything here. First, the practical one: **what does sophisticated student robot code actually look like, concretely enough to teach and to grade?** Second, the local one: **how do San Diego's FRC teams stack up against that standard, and does better code actually correlate with winning?** The work tied back to a market thesis — that San Diego has no coherent year-round high-school robotics instruction pipeline — so understanding the real engineering ceiling of local teams was the groundwork for designing curriculum against it.

The method below is the path from "we have a hunch that good robot code has a recognizable shape" to "we can score any team's repo on eight dimensions and say where they sit relative to 24 of their neighbors and four years of their own history."

---

## The pipeline at a glance

| Stage | What happened | Key artifact(s) |
|---|---|---|
| 1. Corpus teardown | Read real public repos to find the recurring architecture | national-corpus analyses (uploads) |
| 2. Pattern extraction | Named the shared structures: IO layer, coordination paradigms, the ladder | IO-layer analysis, consolidated survey, progression plan |
| 3. Local inventory | Found every San Diego team with public code | `sd-frc-inventory.md`, `sd-ftc-inventory.md` |
| 4. Bulk download | Cloned and cleaned all their repos | `work/clone.sh`, `work/manifest.txt`, `sd-frc-code.zip` |
| 5. Rubric design | Turned the patterns into an 8-dimension anchored rubric | `frc-code-sophistication-rubric.md` |
| 6. Pilot + refinement | Scored 3 teams to test the instrument, fixed two scoring rules | `sd-frc-scores-pilot.md` |
| 7. Full scoring + validation | Scored 24 teams, paired with EPA, measured what predicts results | `sd-frc-master.csv`, `sd-frc-correlations.csv`, `sd-frc-final-report.md` |
| 8. Build spec | Synthesized an elite-track architecture to grow into | `frc-elite-architecture.md` |
| 9. Patribots deep dive | Full-history clones of four seasons, year-by-year scoring | `patribots-four-year-scoring.md` |

A point worth stating plainly: stages 1–2 were done against a **national** corpus, not San Diego. We learned what good looks like from the best teams in the country first, *then* brought that lens home. The rubric is San-Diego-applied, but it is nationally-derived.

---

## Stage 1–2 — Establish the standard from real code

We did not invent a quality bar from first principles. We read source. Three teardowns, all from public repositories cloned in June 2026, established the vocabulary:

- **The broad baseline (21 repos, three leagues).** A structural teardown of Botball, FIRST LEGO League, and World Robot Olympiad programs across eleven seasons (2014–2025) and four code formats (C/C++, Python, EV3-G, SPIKE blocks). The finding that mattered: despite different hardware, languages, and games, **every program converges on the same three-layer structure** — a constants/device map, a motion-primitive layer, and a mission layer. The game changes yearly; the architecture doesn't. That stability is what makes it teachable.

- **The FRC survey (37 teams, four languages, six coordination paradigms).** A consolidated teardown of top FRC codebases established that FRC software has converged on a small set of architectural ideas, and that the best teams differ mainly in **how far they push decoupling past the WPILib command-based baseline.** It identified the six coordination paradigms (command composition, wanted/current FSM, centralized RobotManager FSM, state graph with path search, behavior tree, and inter-process message bus) and framed modularity as **a ladder, not a binary**.

- **The IO-layer deep dive.** The single most widely shared idea — present in roughly two-thirds of the Java/Kotlin codebases — got its own analysis, read from the source of 6328, SciBorgs, 254, PhantomCatz, 3636, and 2056. Its central claim: the "IO layer" is FRC's house name for **the Strategy pattern**, and the reason it matters is that it makes simulation, log replay, and unit tests into interchangeable implementations of one interface rather than separate rewrites.

- **The progression plan.** These patterns were sequenced into a five-phase novice→elite plan governed by three rules that recur later in our findings: *you rewrite in the offseason, never during build season*; *sequence by pain, not by prestige*; and *the architecture is the vehicle for teaching habits (simulation, code review, knowledge retention), not the goal.*

This is the stage the project framing calls "comparing teams to find the similarities in their identifiable architectural structures." The output was not a score — it was a shared vocabulary of observable structures.

---

## Stage 3 — Inventory every San Diego team with public code

With the vocabulary in hand, we turned to San Diego. We catalogued every local FRC team that publishes code on GitHub: **29 FRC organizations** (and, on a parallel track, **12 FTC teams**). For each team we recorded its GitHub owner and the full list of season repositories, annotated with code-file counts and sizes — e.g. a team's `FRC_2026` repo at 98 files / 1.5 MB next to its `FRC_2011` at 1 file / 24 KB. This is what let us later pick, per team, the *latest real competition-season repo* rather than a training or template repo.

The machine-readable version of this inventory is `work/manifest.txt`: one line per team in the form `path | github-owner | space-separated-repos`, which became the input to the downloader.

---

## Stage 4 — Download and clean the repositories

Cloning dozens of teams' entire repo histories would pull gigabytes of CAD, video, and binary artifacts irrelevant to a code analysis. The downloader (`work/clone.sh`) was built to avoid that:

- **Shallow clones** (`git clone --depth 1`) of each repo named in the manifest.
- **Aggressive pruning** immediately after each clone: delete `.git`, then strip CAD (`.stl/.step/.sldprt/.f3d/.dxf/...`), media (`.mp4/.mov/...`), archives, compiled artifacts, ML model weights, robot logs (`.wpilog/.hoot/.rlog`), and **any file over 2 MB**.
- **Time-budgeted and resumable.** Each repo clone gets an 18-second timeout; the script runs against a wall-clock budget, skips already-completed targets, and is rerun until it prints `ALLDONE`. This made the bulk download robust to flaky network and session limits.

The cleaned corpus was packaged as `sd-frc-code.zip` (and `sd-ftc-code.zip`). Note the tradeoff this bought us and its cost: shallow, `.git`-stripped clones are small and fast, but they **erase commit history** — which is why the sustainability dimension (below) had to be treated as a floor, and why the later Patribots deep dive went back and re-cloned with full history.

---

## Stage 5 — Build the rubric

The patterns from Stage 2 were turned into a scoring instrument: **eight dimensions, each scored 0–4 against anchored, observable indicators**, with half-steps allowed.

| | Dimension | What it measures |
|---|---|---|
| D1 | Hardware decoupling | How far subsystem logic is separated from physical devices |
| D2 | Coordination & decision logic | How the robot decides and keeps mechanisms from fighting |
| D3 | Simulation | Can the code run without the robot |
| D4 | Testing & verification | Are there real, run, asserted tests |
| D5 | Logging & diagnostics | How you know why the robot misbehaved |
| D6 | Autonomous & path planning | Authored paths, optimal trajectories, reactive avoidance |
| D7 | Localization & vision | What the robot believes about where it is |
| D8 | Sustainability & process | Will the codebase survive its seniors graduating |

Three design decisions defined the instrument. First, **dimensions, not a single ladder score** — because real teams adopt unevenly (a clean IO layer with zero tests; logging bolted onto spaghetti), and the *shape* of the profile is more informative than the sum. This explicitly decomposed the progression plan's bundled phases into independently-scored axes. Second, **score what's used, not what's present** — every grep hit is confirmed by opening a file; a Choreo vendordep with no trajectories is not Choreo adoption; an empty `src/test` folder is not testing. Third, each dimension shipped with a **grep cheat-sheet** of concrete tokens (`interface .*IO`, `@AutoLog`, `addVisionMeasurement`, `.github/workflows/*.yml` containing `test`) to generate candidate levels fast, before the confirm-by-reading pass.

---

## Stage 6 — Pilot, then refine

Before scoring two dozen teams, we scored **three** — chosen as a deliberate high/mid/baseline spread (3128, 2485, 9730) — to answer one question: *does the rubric discriminate and surface distinct profile shapes?* It did (17 / 14 / 8.5, three different profiles), and the pilot surfaced **two scoring ambiguities that were resolved before scaling**:

1. **D1 for the generic-base route.** How to score a team that decouples through a reused 254-style parameterized base class rather than the canonical AdvantageKit Real/Sim/Replay interface. Resolved toward a lenient reading (a maintained generic base counts near the top of D1).
2. **D8 library credit.** How much to reward a season-independent team library that *exists* versus one *demonstrably consumed* as a dependency — unanswerable precisely with `.git` stripped, so D8 was fixed as a floor.

Settling these on three teams, rather than discovering them halfway through twenty-four, is what kept the full scoring internally consistent.

---

## Stage 7 — Score everyone, then test against reality

We scored **all 24 active San Diego teams** against the rubric (`sd-frc-master.csv`), excluding five teams whose latest code predates the 2024 WPILib baseline the rubric measures. Then we did the step that turns a scoring exercise into a finding: **we paired each team's code score with an external measure of competition results** — season-matched Statbotics EPA (normalized strength, within-California state percentile, and win rate) — and computed Spearman rank correlations per dimension.

The headline: code sophistication correlates **moderately** with results (total Σ vs normalized EPA, ρ ≈ 0.55) — real but explaining only about a third of the variance. The per-dimension split was the useful part:

- **Tracks results best:** D8 Sustainability (ρ ≈ 0.60), D6 Autonomous/Path (≈ 0.59), D7 Vision (≈ 0.51) — the dimensions that either put points directly on the board (D6/D7) or proxy overall program maturity (D8).
- **Barely tracks results:** D3 Simulation (≈ 0.17), D4 Testing (≈ 0.26) — internal engineering-quality investments whose payoff is robustness and developer velocity, not raw match points. (D4 is also near-constant — almost every team scores 0 — so its low correlation is partly a low-variance artifact, not evidence that testing hurts.)

The outliers carried the signal: the most feature-complete codebase in San Diego (3647, Σ = 20) finished in the bottom third of the state in 2025, while two minimal repos (4419, 3749) posted top-quartile results — a clean demonstration that **code sophistication and competition performance are different axes.** The honest confound is stated in the report: D8 topping the list suggests a lurking variable (older, better-resourced programs have both better hygiene and better results), so the rubric measures code, not budget or mentorship.

---

## Stage 8 — A target to build toward

The same corpus that produced the *descriptive* rubric also produced a *prescriptive* spec: `frc-elite-architecture.md`, a foundation-first build plan organized around **three seams** (the IO seam, the state/`RobotState` seam, the coordination/`Superstructure` seam) that a team builds in week one so that every advanced capability — replay, simulation, tests, vision fusion, trajectory optimization — later attaches as an *addition* rather than a *rewrite*. It maps directly onto the rubric's eight dimensions and is what later turns a Patribots score into actionable next steps.

---

## Stage 9 — The Patribots deep dive

Finally, we applied the whole apparatus to one team across time. Because the corpus clones had `.git` stripped, we **re-cloned all four Patribots season repos in full, with complete commit history** (RapidReact2022, ChargedUp2023, Crescendo2024, Reefscape2025), then scored each year against the rubric and read the commits to reconstruct what each season was actually doing.

The result was a clean monotonic climb (Σ ≈ 5 → 10 → 17.5 → 20) and a finding only the full history could reveal: the leap to elite-track scores happened **in the 2024 offseason, not in any build season** — the 2024 *competition* robot ran on Monologue logging with no IO layer, and the IO-layer/AdvantageKit rebuild landed in July–August 2024, which is exactly the "rewrite in the offseason" rule from Stage 2 showing up in a real team's git log. (Re-scoring with full history nudged their 2025 total from the survey's 19.5 to 20.) The persistent gap across all four years — verified against every branch — is testing: not one unit test has ever been written. That became the team's single highest-leverage next step, grounded in the Stage 8 build spec.

---

## Reproducibility and provenance

- **Source code:** public GitHub repositories, cloned June 10–11, 2026. Team→owner→repo mapping in `work/manifest.txt`; clone+clean logic in `work/clone.sh`.
- **Performance data:** Statbotics v3 API (`api.statbotics.io`), season-matched per team, retrieved June 10, 2026.
- **Scoring unit:** each team's most recent real competition-season repo; adjacent library/training repos count toward D8 only.
- **Known limitations carried throughout:** shallow `.git`-stripped clones make D8 a floor and D4 near-constant; n = 24 across mixed game years (2023–2026); EPA measures the whole robot and alliance context, not the software; correlation is not causation and team age is a plausible confound for both code hygiene and results.

---

## The shape of the method, in one line

Read the best code in the country to learn what good looks like → name the recurring structures → inventory and download every local team's code → turn the structures into an anchored eight-dimension rubric → pilot it on three teams and fix the rules → score all 24 and test the scores against real competition results → distill a build spec to grow into → and apply the whole lens, with full history, to one team across four years.
