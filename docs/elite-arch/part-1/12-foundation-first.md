---
title: 12. Foundation-first
weight: 12
---
[Chapter 4](04-at-a-glance.md) said *what* the architecture is. This chapter says *in what order you
build it and why that order is safe.* The organizing idea: **build the seams, defer the payoffs.**
Every advanced capability attaches to one of the three seams, so if you cut the seams correctly in
week one, each later feature is an *addition at a named point* rather than a refactor.

## Each rung attaches to a seam

The progression is a map, not a wish list. Every rung names the seam it plugs into and roughly how
much new code it costs.

| Rung | Capability | Attaches to | New code |
|---|---|---|---|
| 1 | Mechanism physics in sim | fill `XxxIOSim` | a WPILib sim inside the Sim impl |
| 2 | Unit tests | construct subsystem with `XxxIOSim` | `@Test`: step sim, assert |
| 3 | Vision pose fusion | `RobotState.addVisionMeasurement` + `VisionIO` | a camera impl + std-dev tuning |
| 4 | Authored autos | Superstructure goals as named commands | PathPlanner paths/autos |
| 5 | Time-optimal trajectories | swap the path source | Choreo where time matters |
| 6 | On-the-fly pathfinding | reads `RobotState.getPose()` | pathfind-to-pose |
| 7 | Deterministic log replay | `REPLAY` run mode (already wired) | **none in subsystems** — flip the mode |
| 8 | Smart coordination | replace `applyGoal` body | guarded table → planner → state graph |
| 9 | Versioned team library | promote `util/` + generic IO base | extract, version, consume |

Nothing in rungs 1–9 modifies the seams; they only fill them. That is the whole promise: a team that
cut the seams can climb this ladder without the offseason rewrites that sink most programs.

## The dividends teams skip

The deferred-dividend rungs — sim (1), tests (2), and replay (7) — are the ones teams build the seam
for and then never collect. Filling `IOSim` costs an afternoon and unlocks both testing and replay,
yet the corpus finding is blunt: almost every team that builds the IO seam never writes the test or
flips the replay mode. Collecting them is the clearest marker of real software culture, and the
foundation already paid for them.

## The build order

The architecture has a definition-of-done sequence. Steps 1–6 are the foundation; 7–10 are the climb,
and none of them touches the seams:

1. **Command-based skeleton** — *done when:* teleop drives.
2. **IO seam on Drive** — interface, inputs struct, real/sim/replay impls. *Done when:* it runs in SIM
   with a stub and doesn't crash.
3. **`RobotState`** — pose estimator fed by drive odometry. *Done when:* the pose shows on the field in
   sim.
4. **Logging facade** — every subsystem's inputs published. *Done when:* every mechanism is visible in
   AdvantageScope.
5. **One mechanism, full quartet** — e.g. an elevator with sim physics. *Done when:* a unit test steps
   the sim and asserts it reaches a setpoint.
6. **Superstructure** — goal enum plus one real interlock. *Done when:* an illegal request is provably
   sequenced safely.
7. **Vision** → 8. **Autos** → 9. **Collect the dividends (replay, broader tests)** → 10. **Extract the
   library** once patterns have repeated three times.

## Tools attach at seams, too

The architecture is tool-agnostic *at defined seams*, so picking or swapping a tool is a localized
change: PhotonVision or Limelight is a `VisionIO` impl into `RobotState`; YAGSL or CTRE Tuner X is a
`DriveIO` impl; maple-sim lives inside `IOSim`; AdvantageKit or DogLog is a logging backend; Choreo
swaps PathPlanner where seconds decide matches. AdvantageScope sits on top of all of it as the viewer.

## The one rule that carries it

A vendor type — a `TalonFX`, a `PhotonCamera` — must **never appear in a subsystem, a command, or the
superstructure.** Only inside an IO implementation. If a `com.ctre` or `org.photonvision` import shows
up above the IO line, the seam has leaked and a tool swap has become a refactor.

This is the discipline teams actually skip. Of the 24 corpus teams that built an IO seam, **22 still
import a vendor type above the line.** Building the interface is the easy 80%; keeping vendor types out
of everything above it is the unglamorous 20% almost no one finishes — which is exactly why it deserves
a lint rule rather than good intentions, and why clean vendor confinement is a distinguishing top-tier
marker rather than a given.

That confinement rule, generalized, is also where Part III begins. But first, [the next
chapter](13-lessons-from-outside.md) looks at what the broader robotics field treats as table stakes
that this architecture still skips.
