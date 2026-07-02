> **Archived — absorbed into the elite-arch wiki.** See Part I ch. 9 — Other advanced topics (`docs/elite-arch/part-1/09-other-advanced-topics.md`). Retained here for historical reference.

# Other Topics — Additional Elite Techniques

Beyond the three seams (`elite-architecture.md`) and the cross-cutting practices (`logging.md`,
`simulation.md`, `testing.md`), a handful of advanced techniques recur in top FRC codebases. These are
**additive** — they layer onto the elite architecture rather than restructure it (for genuine *architectural
alternatives*, see `../alternatives/`). Prevalence below is measured across the corpus
(`../../data/code-index.duckdb`, 63 teams); some are near-standard among serious teams, others are rare and
worth knowing about. Each is one paragraph with sources and the teams who use it.

## At a glance

- **State-space & model-based control** — model the mechanism as a linear system and use LQR + a Kalman observer instead of hand-tuned PID. The most "control-theory" rung; rare.
- **Swerve setpoint generator** — clamp swerve commands to kinematically feasible slew/accel so the robot doesn't skid or tip. 254-origin, now spreading.
- **High-frequency threaded odometry** — sample drive encoders + gyro at 200–250 Hz on a separate thread for sharper pose, decoupled from the 50 Hz main loop. Near-standard on elite swerve.
- **Neural game-piece detection & opportunistic pickup** — an on-coprocessor object detector feeds auto/telelop routines that drive to and grab the best available piece.
- **Self-check & fault-reporting diagnostics** — a command that exercises each subsystem and a reporter that surfaces device faults to the dashboard. Operational robustness; rare.
- **Replay as regression test** — re-run a logged real match deterministically and assert behavior; the under-used dividend of AdvantageKit logging.
- **Reactive / adaptive autonomous** — autos that re-decide on sensed state (skip a missing piece, take the open branch) rather than running a fixed script.
- **QuestNav (VR-headset localization)** — a Meta Quest as an inside-out 6-DOF tracker streamed over NetworkTables and fused with AprilTags. Emerging frontier.

---

## State-space & model-based control

Instead of hand-tuning a PID loop, you model the mechanism as a linear system (`A`, `B`, `C`, `D`), then
derive an optimal feedback gain with a **Linear-Quadratic Regulator** and estimate unmeasured state with a
**Kalman filter** — WPILib wires the two together as a `LinearSystemLoop`. The payoff is principled gains
from physical constants (mass, gearing, motor curve) rather than trial-and-error, plus an observer that
rejects sensor noise. It is the rarest technique here: full LQR/`LinearSystemLoop` control appears in just
**4 teams** (971 Spartan Robotics, 3128 Aluminum Narwhals, 5137 Iron Kodiaks, 6995), with custom Kalman /
EKF / UKF estimation in **8** (incl. 254 Cheesy Poofs, 1678 Citrus Circuits, 3476 Code Orange, 5190 Green
Hope Falcons). Most teams instead get 80% of the benefit from feedforward + PID, which is why this stays a
niche. Start from the WPILib
[State-Space and Model-Based Control](https://docs.wpilib.org/en/stable/docs/software/advanced-controls/state-space/index.html)
docs; characterize the plant with [SysId](https://docs.wpilib.org/en/stable/docs/software/advanced-controls/system-identification/index.html).

## Swerve setpoint generator

A naive swerve drive will command module states the modules can't physically achieve in one loop — the
result is wheel skid, loss of odometry accuracy, and tipping under aggressive acceleration. A **swerve
setpoint generator** takes the desired chassis speeds and the *current* module states and returns the
closest setpoint that respects each module's steer-slew and drive-accel limits (and friction/voltage). It
originated with **254 Cheesy Poofs** (their `SwerveSetpointGenerator` is in the corpus at
`frc_team_repos/254-cheesy-poofs/…`) and is now packaged in
[PathPlannerLib](https://pathplanner.dev/) and Choreo, which is why it has already spread to **19 teams**
(incl. 1678 Citrus Circuits, 2102 Team Paradox, 2658 Sigma Motion, 3061 Huskie Robotics, 4738 Patribots,
6328 Mechanical Advantage). At ~30% it is the most "trending toward standard" item on this list.

## High-frequency threaded odometry

The main robot loop runs at 50 Hz, but a swerve pose estimate sharpens considerably if you sample the drive
encoders and gyro at 200–250 Hz on a dedicated thread and feed every sample into the pose estimator with its
own timestamp. CTRE Phoenix 6 enables this with time-synchronized `BaseStatusSignal.waitForAll(...)` on a
CANivore bus, and the pattern is baked into the
[AdvantageKit](https://docs.advantagekit.org/) swerve template (a `PhoenixOdometryThread` /
`SparkOdometryThread`). It shows up in **26 teams** (incl. 254 Cheesy Poofs, 6328 Mechanical Advantage, 1114
Simbotics, 1678 Citrus Circuits, 2412 Robototes, 3061 Huskie Robotics) — at ~41% it is close to standard on
elite swerve and could reasonably be folded into the swerve subsystem guide rather than treated as exotic.

## Neural game-piece detection & opportunistic pickup

Beyond AprilTag pose, teams run an on-coprocessor **object detector** — a neural model on a Limelight or a
PhotonVision pipeline — that reports the bearing (and sometimes range) to game pieces, then drive auto or
teleop-assist routines that turn to and intake the best available target. The *detector* is mainstream:
**31 teams** carry one (incl. 254 Cheesy Poofs, 971 Spartan Robotics, 1678 Citrus Circuits, 2056 OP
Robotics, 2706 PhantomCatz). The genuinely differentiating part is the *architecture* on top — closed-loop
"drive-to-piece" with rejection of bad detections and graceful fallback when nothing is seen. See the
[Limelight neural detector](https://docs.limelightvision.io/) and
[PhotonVision object detection](https://docs.photonvision.org/) docs.

## Self-check & fault-reporting diagnostics

An operational, not algorithmic, technique: a `systemCheck` command that drives each subsystem through a
scripted range of motion and asserts it responds, plus a `FaultReporter` that polls every device's fault
flags (CAN timeout, over-temp, low firmware) and surfaces them to the dashboard before a match. This turns
"the robot is acting weird" into a named, pit-actionable fault. It is rare — **4 teams** (1155 SciBorgs,
2658 Sigma Motion, 3015 Ranger Robotics, 3061 Huskie Robotics) — and is the marker the rubric uses for the
top rung of D5 (diagnostics). 3061 and 3015's `FaultReporter` / system-check commands in the corpus are the
reference implementations.

## Replay as regression test

AdvantageKit's deterministic log replay (feed a recorded match's inputs back through the same code and get
bit-identical outputs) is usually framed as a debugging tool, but it is also a **regression-test fixture**:
check in a logged match, and a CI test can re-run it and assert the robot still makes the same decisions
after a refactor. Almost no team collects this dividend even though many have the logging for it — it is the
test-side complement to `simulation.md`'s sim tests and to `../alternatives/02-physical-plant-simulation.md`.
The mechanism lives in [AdvantageKit](https://docs.advantagekit.org/) (6328 Mechanical Advantage's
framework); the discipline of using replays *as tests* is the uncommon part.

## Reactive / adaptive autonomous

Most autos are fixed scripts. A reactive auto instead re-decides mid-routine on sensed state: skip a pickup
if the game piece isn't detected, choose the open scoring branch, or abort and reposition if blocked. In
practice this is built from PathPlanner conditional paths / event markers plus a small decision layer, and it
is the autonomous-mode expression of the coordination ideas in
`../alternatives/03-state-graph-coordination.md` (graph search) and
`../alternatives/04-behavior-trees.md` (a reactive tree). It is hard to count by code signature, but the
capability — an auto that handles a missed first piece without dying — is what separates a robust auto from a
brittle one.

## QuestNav (VR-headset localization)

A Meta Quest headset is a cheap, extremely good inside-out 6-DOF tracker (it has to be, to render VR without
nausea). **QuestNav** mounts one on the robot and streams its pose over NetworkTables, where it is fused with
AprilTag vision as a high-rate, low-drift odometry source. It is the newest item here — **1 team** in the
corpus (7028, 2026, using the `gg.questnav` library) — and genuinely emerging across FRC for the 2026 season.
Source: [QuestNav](https://github.com/QuestNav/QuestNav). It ties back to the localization material in
`subsystems/05-vision-sensor.md` and `subsystems/07-robotstate.md` — the Quest is just another observation
feeding the same `RobotState` pose estimator.

---

## Sources

- WPILib: [state-space control](https://docs.wpilib.org/en/stable/docs/software/advanced-controls/state-space/index.html) · [SysId](https://docs.wpilib.org/en/stable/docs/software/advanced-controls/system-identification/index.html)
- [PathPlannerLib](https://pathplanner.dev/) (swerve setpoint generator, conditional autos) · [AdvantageKit](https://docs.advantagekit.org/) (odometry thread, replay)
- [Limelight](https://docs.limelightvision.io/) · [PhotonVision](https://docs.photonvision.org/) (object detection) · [QuestNav](https://github.com/QuestNav/QuestNav)
- Reference team code lives in the corpus under `frc_team_repos/<team>/` — notably 254 (setpoint generator), 6328 (AdvantageKit odometry/replay), 3061 & 3015 (FaultReporter / system-check).
