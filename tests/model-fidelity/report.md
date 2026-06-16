# Model-fidelity pilot — which agent should score the corpus?

**Question.** The agent-confirmation tier ("score what's USED, not present") is the only way past the
~0.38 mechanical sophistication ceiling. Running it on the full corpus is expensive, so before that
spend we test **how much fidelity we lose** by using a cheaper model than Opus 4.8.

**Design.** Score **6 teams stratified across the mechanical sophistication range** (5025 lowest →
3476 highest, plus the Patribots 4738 anchor) with **three models** — Opus 4.8 (reference), Sonnet
4.6, the latest Haiku 4.5 — using the identical evidence packet (`scripts/agent_score.py`). Each model
opened the actual repo files and returned confirmed D1–D8. **Opus is the reference;** I (the Opus main
loop) adjudicate how close the cheaper models land. Raw score vectors: `tests/model-fidelity/scores.csv`;
full per-model rationales are in the pilot run transcript.

## Quantitative agreement (vs. Opus reference, 6 teams × 8 dims)

| Model | mean abs deviation / dim | mean abs total error (/32) | Spearman of team totals |
|---|---|---|---|
| **Sonnet 4.6** | **0.17** | **1.33** | **1.00** (identical ranking) |
| Haiku 4.5 | 0.49 | 3.58 | 0.89 |

Per-dimension mean-abs-deviation vs Opus — where the models drift:

| | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|---|
| Sonnet | 0.33 | 0.0 | 0.33 | 0.08 | 0.25 | 0.17 | 0.08 | 0.08 |
| Haiku | 0.50 | 0.17 | **1.08** | 0.17 | 0.42 | **0.67** | **0.50** | 0.42 |

## Qualitative read of the rationales

**What all three models got right** — the hard "present vs. used" calls the mechanical pass cannot make:
- **D4 = 0 everywhere** despite JUnit deps + a CI `gradlew test` step, because no `src/test` exists
  (3476's "tests" are on-robot `SequentialCommandGroup` routines; 4099's `Test.java` is a log helper).
- **3341's maple-sim is commented-out dead code** → all three scored D3 ≈ 1.5–2, not the mechanical-implied 3.
- **3476's Choreo `.traj` files have `choreoAuto:false`** and are never driven → all three discounted Choreo.
- **4099 genuinely loads Choreo** (`Choreo.loadTrajectory(...).get()` → `FollowChoreoPath`) → all three
  credited D6 ≈ 3, correcting the mechanical lead's `choreo_USED=0`.

This confirms the agent tier works and the discipline survives even on the cheapest model.

**Where Haiku breaks down** — magnitude on the sophisticated repos:
- **D3 (simulation), MAD 1.08.** Haiku scored **4738 D3 = 0** and **7028 D3 = 0**, claiming "no physics
  sim," but Opus *and* Sonnet both found a real `DCMotorSim` wired into 4738's `Kraken.java` and ticked
  in `simulationPeriodic`, and a live CTRE swerve `updateSimState` in 7028. Haiku read too shallowly.
- **3476 total 18.5 vs Opus 26** and **7028 total 10 vs 15.5** — Haiku under-detects wired-in
  sophistication exactly on the teams where the distinctions matter most (D3/D6/D7).

**Sonnet's only drift** is a mild conservatism at the very top: it gives D1 = 3 where Opus gives 4 on
the two most architecturally elite teams (4099, 3476). Ranking and every hard call are identical.

## Decision

**Run the full corpus on Sonnet 4.6.** It is faithful to Opus (perfect total ranking, 0.17 mean
per-dimension deviation, totals within ~1.3/32), makes the same "used not present" judgments, and costs
far less than Opus. **Haiku 4.5 is rejected** — at the tolerance limit overall and systematically lossy
on D3/D6/D7 for sophisticated repos, with two outright factual misses (D3 = 0 where real sim exists).
**Opus is reserved as the periodic reference**, not the bulk scorer (the user's cost constraint).
