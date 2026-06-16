# Knowledge index

Embedded research behind the rubric. Read `rubric/rubric.md` first for any scoring task.

## rubric/
- `rubric.md` — the 8-dimension (D1-D8) scoring rubric: anchors, grep cheat-sheet, profile shapes.

## corpus-analysis/  (national derivation — why the rubric looks the way it does)
- `00-sd-education-landscape.md` — market context for the whole project.
- `01-botball-fll-wro-teardown.md` — 21 non-FRC repos; the universal three-layer structure.
- `02-frc-37-team-survey.md` — 37 FRC teams, six coordination paradigms, the modularity ladder.
- `03-io-layer-strategy-pattern.md` — the IO layer = Strategy pattern; the D1 spine.
- `04-novice-to-elite-progression.md` — the five-phase ladder; "rewrite in the offseason".

## build-spec/
- `elite-architecture.md` — foundation-first build spec (three seams). Source of recommendations.

## build-spec/subsystems/  (per-subsystem deep dives — one per control archetype)
- `00-anatomy-of-a-subsystem.md` — the shared template, the archetype map, and the
  mock/library/vendor ethic every subsystem doc applies. **Read first.**
- `01-linear-position.md` — Elevator, Climber. `ElevatorSim`; position-in/volts-out. The reference doc.
- `02-rotational-position.md` — Arm, Pivot, Wrist, Turret. `SingleJointedArmSim`; angle + absolute encoder.
- `03-velocity.md` — Shooter, Flywheel. `FlywheelSim`; speed control, "at speed" tolerance.
- `04-roller-gamepiece.md` — Intake, Indexer, Feeder, Manipulator. `DCMotorSim` + the game-piece sensor.
- `05-vision-sensor.md` — Vision. Sensor-only IO (no actuation) feeding `RobotState`; the Photon/Limelight swap.
- `06-swerve-drivetrain.md` — Drivetrain. The multi-interface special case (`ModuleIO` ×4 + `GyroIO`), kinematics, odometry.

## survey/  (the San Diego results the rubric produced)
- `sd-frc-final-report.md` — 24 teams scored + correlated with Statbotics EPA.
- `sd-frc-master.csv` — per-team D1-D8 vectors + external metrics (peer-benchmark table).
- `sd-frc-correlations.csv` — which dimensions track competition results.
- `sd-frc-scores-pilot.md` — the 3-team pilot that refined the rubric.
- `sd-frc-inventory.md`, `sd-ftc-inventory.md` — the team/repo inventories.

## examples/  (worked outputs to imitate)
- `patribots-four-year-scoring.md` (+ `.pdf`) — full single-team, multi-year analysis.
- `methodology.md` — how the whole study was conducted, end to end.
- `sample-score-output-reefscape2025.md` — raw `score_rubric.sh` output for reference.
