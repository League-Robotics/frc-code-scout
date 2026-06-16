---
name: audit-architecture
description: Review the CURRENT robot project against the 8-dimension rubric and the elite build-spec — which of the three seams exist, where vendor types leak above the IO line, whether subsystems are tested in sim — and report a candidate D1–D8 profile with the single highest-leverage next step. Use to self-assess your own codebase ("audit my architecture", "how good is our code", "what should we improve", "check our IO layer").
---

# Audit this project's architecture

A self-review of the *current* repo (not someone else's download) against the rubric and build-spec.
Score what's **used**, not merely present — confirm every grep hit by opening the file. The rubric is
**`knowledge/rubric/rubric.md`** (bundled; read it first — anchors, the measured-prevalence
calibration table, and the corrected grep tokens). Recommendations map to the seams in
`knowledge/build-spec/`.

## Steps
1. **Read the rubric** (D1–D8, anchors, the "Corpus prevalence" table — a marker in 3 teams is a
   ceiling signal; one in 45 is table stakes).
2. **Find the source** (`src/main/java/...`). Probe each seam (confirm by reading, don't trust counts):
   - **D1 IO seam** — `interface *IO` with ≥2 impls, one a `*IOSim`. Hardware impls are named by
     device (`*IOTalonFX`/`*IOSparkMax`/…), **not** `*IOReal`. An inputs struct (`@AutoLog`/`*Inputs`)?
   - **D7 state seam** — a `RobotState` owning the pose estimator (vs. Drive privately owning it)?
   - **D2 coordination seam** — a real `Superstructure`/`RobotManager` with a goal API + a single
     transition function, or a holder with jog buttons (level-1 wearing a level-3 name)?
   - **D3 sim / D4 tests** — `*IOSim` with real physics; a `src/test` tree with sim-backed asserts; CI
     `gradle test`?
   - **D5 logging** — AdvantageKit/`@AutoLog`/`processInputs` (coverage across subsystems) or DogLog?
   - **D6 auto** — PathPlanner/Choreo with real `.path`/`.traj`; **D8** — a team lib, CI, README.
3. **The two flags that matter most:**
   - **Vendor leak** — grep for `com.ctre`/`com.revrobotics`/`org.photonvision` **above the IO line**
     (in subsystem/command/superstructure files, i.e. NOT `*IO<device>`/`*IOSim`). Any hit is a leak.
   - **Architecture without verification** — IO layer present (D1≥3) but no real tests (D4≤1). The
     single most common, highest-leverage gap.
4. **Report:** a D1–D8 candidate vector with one line of evidence each; the seams present vs. missing;
   the vendor leaks (file:line); and **one** highest-leverage next step (usually: a unit test on an
   existing subsystem, or confining a leaked vendor type). Point each gap at the relevant build-spec
   chapter and the `setup-*`/`add-subsystem` skill that closes it.

## Notes
- This is the rubric pass turned inward — same discipline as the `analyze-team` skill, but on the
  user's own code, with no clone/index step needed.
- Be honest and specific (file:line). A candidate score is a starting point; the value is the named
  next step, not the number.
