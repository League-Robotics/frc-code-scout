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
- `05-motor-io-interfaces.md` — how *other* teams talk to motors (prior art): the 6 reusable `MotorIO` contracts in full + the design axes. (Our own design lives in `specs/portable-motor-interface.md`.)
- `06-lessons-from-broader-robotics.md` — outside-in view: what ROS/Nav2/MoveIt/autonomous-driving treat as table stakes that FRC skips. 7 importable runtime/process disciplines, mapped to the seams and rubric.
- `07-code-generators.md` — spec-in/code-out tools (RobotBuilder, CTRE Tuner X swerve gen, YAGSL, AI/LLM) scored against the IO seam. All optimize time-to-drive, not swappability; the fix is "generate the constants, own the architecture" (Tuner X → AdvantageKit).
- `08-drivetrain-as-architecture.md` — what a drivetrain *is*, empirically (55 teams via duckdb): the only universal subsystem (94%), and the only one that's both actuator and primary sensor — its `Pose` is the most-consumed value on the robot (682×). Architecture spectrum (≈63% CTRE-generated, ≈27% own a seam), the 254/2910 elite package layout, seam granularity, and the `CommandSwerveDrivetrain`/`SwerveRequest`/`SwerveDriveState` usage rankings. Evidence companion to specs/portable-swerve-interface.

## build-spec/
- `elite-architecture.md` — foundation-first build spec (three seams). Source of recommendations.
- `code-review-principles.md` — architecture-first code review guide for agents and humans; seam checks, leak detection, severity rubric, and report format.
- `logging.md` — D5: the inputs-struct contract; the println→SmartDashboard→DogLog/Epilogue→AdvantageKit+replay ladder.
- `testing.md` — D4: kinds of tests, the IO-sim-as-mock idea, the HAL/sim-time harness, CI, the system-check trick.
- `simulation.md` — D3: how sim works (run modes, HAL sim, sim time), the environments (WPILib sims, maple-sim, AdvantageScope), replay.
- `other-topics.md` — additive advanced techniques (not architectural alternatives): state-space/LQR control, swerve setpoint generator, threaded high-freq odometry, neural game-piece detection, self-check/fault diagnostics, replay-as-test, reactive autos, QuestNav. One paragraph each, with sources + the teams using them.

## build-spec/subsystems/  (per-subsystem deep dives — one per control archetype)
- `00-anatomy-of-a-subsystem.md` — the shared template, the archetype map, and the
  mock/library/vendor ethic every subsystem doc applies. **Read first.**
- `01-linear-position.md` — Elevator, Climber. `ElevatorSim`; position-in/volts-out. The reference doc.
- `02-rotational-position.md` — Arm, Pivot, Wrist, Turret. `SingleJointedArmSim`; angle + absolute encoder.
- `03-velocity.md` — Shooter, Flywheel. `FlywheelSim`; speed control, "at speed" tolerance.
- `04-roller-gamepiece.md` — Intake, Indexer, Feeder, Manipulator. `DCMotorSim` + the game-piece sensor.
- `05-vision-sensor.md` — Vision. Sensor-only IO (no actuation) feeding `RobotState`; the Photon/Limelight swap.
- `06-swerve-drivetrain.md` — Drivetrain. The multi-interface special case (`ModuleIO` ×4 + `GyroIO`), kinematics, odometry.
- `07-robotstate.md` — the **state seam**. The world model: observations in, fused pose out; pure logic, the most testable class. D7.
- `08-superstructure.md` — the **coordination seam**. Goals in, guarded subsystem setpoints out; where interlocks live. D2.

## alternatives/  (uncommon-but-good patterns — legitimate deviations from the build-spec default)
- `README.md` — what earns a place here: sound, uncommon, situational, guard-railed. Build-spec is canon; these are "also legitimate, for these reasons."
- `01-capability-typed-devices.md` — device-level interfaces named by **capability, not vendor** (`PositionMotor`, not `ITalonMotor`) + a hardware object below the IO line. FOC modeled as an orthogonal opt-in capability.
- `02-physical-plant-simulation.md` — a **plant** (true-state world model) as the dual of `RobotState`; settable truth + a fidelity dial make dynamics/observation/estimator independently testable; control law stays on one side of the seam.
- `03-state-graph-coordination.md` — *(sketch)* coordination as **graph search** over a superstructure state graph; **A\*** over configuration space at the far end. Established but uncommon (254). Extends the superstructure seam (D2).
- `04-behavior-trees.md` — *(overview)* **behavior trees**: a re-ticked SUCCESS/FAILURE/RUNNING tree for reactive priority-driven decisions; the strategy-layer partner to doc 03. Explicit BTs ~absent in FRC; the command-group cousin is universal.

## specs/  (forward-looking design specifications)
- `portable-component-model.md` — **the parent abstraction** the other two specs are instances of. Every active thing (motor, sensor, subsystem, `RobotState`, superstructure) is a *block*: a configured transfer function with memory — `Config` once, then `(State, Command_out[]) = update(Command_in, Observations)`. The fill-pattern of its four channels *is* the component taxonomy; emission is a return value not a side-effect; it's a discipline not a base class; it's the in-process ROS 2 node. Recommends the name `Block`.
- `portable-motor-interface.md` — **our** motor interface (the partner to corpus-analysis/05's survey of others): a language-neutral, ROS-translatable design — two serializable PODs (`Command`/`MotorState`, named `u`/`x` not inputs/outputs), nullable payloads, `oneof` control modes, capability tiers, REP-103 units, proto3 source-of-truth + generated ROS bridge. Appendix A preserves the Java v1 it evolved from.
- `portable-swerve-interface.md` — **our** swerve drivetrain interface, distilled from reading CTRE Phoenix 6, AdvantageKit (6328), YAGSL, and WPILib source. The 5-layer model (L0 WPILib math → L1 `ModuleIO`/`GyroIO` seam → L2 module logic → L3 drive + optional `SwerveSetpointGenerator` → L4 `SwerveRequest` vocabulary); "AdvantageKit's seam + CTRE's vocabulary on WPILib's math." L1 composes the motor interface; the 254→6328→PathPlannerLib setpoint-generator lineage. Twin to corpus-analysis/07.

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
