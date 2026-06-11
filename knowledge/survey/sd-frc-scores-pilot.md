# San Diego FRC Code Sophistication — Pilot Scores (3 teams)

Scored against `frc-code-sophistication-rubric.md`. Three teams chosen as a deliberate spread (likely-high / mid / baseline) to test whether the rubric discriminates and surfaces distinct profile shapes. Each level confirmed by opening the files behind the grep hits, not presence alone. Half-steps used where a team sits between anchors.

## Scoresheet

| Team | Repo scored | D1 Arch | D2 Coord | D3 Sim | D4 Test | D5 Log | D6 Auto | D7 Vision | D8 Sustain | Σ /32 |
|---|---|---|---|---|---|---|---|---|---|---|
| 3128 Aluminum Narwhals | 3128-robot-2025 (Java) | 3.5 | 3 | 1 | 0 | 1 | 3 | 2.5 | 3 | **17** |
| 2485 Overclocked | frc-2026 (Java) | 2 | 1.5 | 1 | 0 | 2 | 2.5 | 3 | 2 | **14** |
| 9730 Metal Maniacs | 2026RebuiltCode (Java) | 1 | 1 | 1 | 0 | 1 | 2 | 1.5 | 1 | **8.5** |

## 3128 Aluminum Narwhals — 17/32 — "library-grade architecture without verification"

The most sophisticated of the three, and it took the road less traveled. Instead of the AdvantageKit IO-interface layer the rubric's D1 spine is built around, 3128 decouples through their maintained `3128-common` library: every mechanism extends a generic parameterized base (`PositionSubsystemBase`, `FSMSubsystemBase`) over a `NAR_Motor` hardware wrapper, and the robot is coordinated by a real `RobotManager` superstructure — an `FSMSubsystemBase` driven by a `TransitionMap` that fans `RobotStates` out to per-subsystem state enums (D2=3). Autos are PathPlanner with `LocalADStar` on-the-fly pathfinding and `alignScoreCoral` drive-to-pose commands (D6=3). Vision is AprilTag pose feeding `addVisionMeasurement` through their `Camera`/`Limelight` abstraction, plus a Python object-detection pipeline running on the Limelight (D7=2.5).

And then it stops dead at verification: one empty `simulationPeriodic`, zero tests, CI that runs `gradlew build` (not `test`), and dashboard-only telemetry. They built the exact base-class infrastructure that makes subsystems testable and never collected the dividend. Highest-leverage next step: one sim-backed unit test on a `PositionSubsystemBase` mechanism.

## 2485 Overclocked — 14/32 — "tooling adopter"

Uneven in the opposite direction from 3128: elite-grade *peripherals* on a baseline *core*. Vision is the strongest of the three teams — dual-camera PhotonVision with a `PhotonPoseEstimator`, tag-whitelist rejection, and tuned vision std-devs feeding `addVisionMeasurement` (D7=3). Logging is structured: NetworkTables struct publishers, CTRE `SignalLogger`, AdvantageKit `Logger` output, `Mechanism2d` (D5=2). Autos use a large PathPlanner path set with on-the-fly target tracking (D6=2.5).

Underneath, the architecture is ordinary: the drivetrain is CTRE Tuner-generated (`TunerSwerveDrivetrain`, a vendored abstraction → D1=2) but the mechanisms (Shooter, Intake, Angler, Feeder) are hardware-welded with no IO interfaces, coordination is command composition plus an auto-only state machine (D2=1.5), and there are no tests or physics sim. The tools were installable; the architecture wasn't. Highest-leverage next step: an IO layer on one mechanism, then sim + a test.

## 9730 Metal Maniacs — 8.5/32 — "baseline / template inheritor"

A REV MAXSwerve template with PathPlanner bolted on. Subsystems own their motors and encoders directly (with `PLACEHOLDER DIO PINS -- PLEASE CHANGE` still in the drivetrain), button-binding command composition, scattered `SmartDashboard`, empty `simulationPeriodic` stubs, no tests. Autos are a working PathPlanner `AutoBuilder` setup mixed with hand-coded command autos (D6=2). The one bright spot is half-built: a `Limelight` subsystem with MegaTag2 pose estimation and basic rejection logic — but the class is never instantiated in `RobotContainer` and the drivetrain runs vision-free `SwerveDriveOdometry`, so the vision code isn't wired in (D7=1.5). A stray `eick_bob.txt` sits in the source tree. Highest-leverage next step: connect the Limelight pose estimate they already wrote into the drivetrain, then clean up constants and the repo.

## What the pilot shows

The rubric discriminates cleanly (17 / 14 / 8.5) and the *shape* is more informative than the sum: 3128 and 2485 land one point apart on totally different profiles — 3128 strong on core architecture and weak on tooling integration, 2485 the reverse. The "everyone scores 0 on D4" prediction holds even for the strongest team here.

## Two methodology calls I want you to confirm before I run the other 29

1. **D1 for the generic-base route (3128).** The rubric's D1 ladder is written around the AdvantageKit Real/Sim/Replay IO interface. 3128 has no such swap, but it *does* have reused generic parameterized bases from a maintained library — which is the level-4 anchor's own "254-style `ServoMotorSubsystem`" marker. I scored it 3.5: library-grade base abstraction, docked half a step because the decoupling never extends to a swappable sim/replay implementation (the dimension's real point). If you'd rather the IO-interface path be a hard ceiling for anything below 4 (so 3128 caps at ~2.5), say so — it'll change several teams that use NAR/CTRE-style base classes.

2. **D8 library credit.** I gave 3128 a 3 (CI on the season repo + a season-independent `3128-common` carried across years) and 2485 a 2 (`WarlordsLib` exists in the org but this repo doesn't clearly consume it — the imports are commented out). The open question is how much to reward a library that *exists* versus one *demonstrably consumed as a dependency*. With `.git` stripped I can't see release/version discipline, so D8 stays a floor. Tell me if you want library-exists to count more or less.
