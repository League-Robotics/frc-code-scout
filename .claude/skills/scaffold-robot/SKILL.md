---
name: scaffold-robot
description: Bootstrap a new WPILib command-based robot project on the elite-track foundation — the three seams (per-subsystem IO layer, RobotState, Superstructure), a REAL/SIM/REPLAY run mode, a swerve Drive with ModuleIO+GyroIO, and a swappable logging facade. Use when starting a robot codebase or laying its foundation ("scaffold a robot", "set up the architecture the right way", "start a new robot project"). Builds the seams; add-subsystem fills them.
---

# Scaffold the foundation

Lay the three seams so every later capability (sim, tests, replay, vision, autos) attaches as an
*addition*, never a rewrite. The canonical spec is **`knowledge/build-spec/elite-architecture.md`**
(bundled with this plugin) — read it first, especially §2 (the seams), §2.6 (package layout), and §7
(build order). The golden rule throughout: **no vendor type (`com.ctre`, `com.revrobotics`,
`org.photonvision`) ever appears above the IO line.**

## Collect first
- Java/WPILib project already? (GradleRIO `build.gradle`, a `Robot`/`Main`.) If empty, generate from
  the WPILib command-based template first.
- Swerve or differential drive? Vendor for the motors (CTRE Phoenix 6 / REV)? Logging preference
  (start DogLog/Epilogue for speed, AdvantageKit if they want replay — see `setup-logging`).

## Build order (each step has a "done when")
1. **Run-mode enum + Robot.** A `Constants.Mode { REAL, SIM, REPLAY }` (or `Robot.isReal()`), and a
   `Robot`/`RobotContainer` skeleton. *Done when:* it builds and teleop is reachable.
2. **The IO seam on Drive.** A `Drive` subsystem holding `ModuleIO[4]` + `GyroIO` (swerve) — see
   `knowledge/build-spec/subsystems/06-swerve-drivetrain.md` — each with an inputs struct, a
   `*IO<device>` impl (the ONLY file importing the vendor SDK), a `*IOSim`, and the selection point
   (`Robot.isReal() ? new ModuleIOTalonFX() : new ModuleIOSim()`). *Done when:* the robot drives in
   SIM without hardware.
3. **The state seam — `RobotState`.** A single class owning a `SwerveDrivePoseEstimator` (or a
   buffered estimator), fed `addOdometryObservation(...)` by Drive, exposing `getPose()` and an
   uncalled `addVisionObservation(...)` (the vision seam, pre-cut). See
   `knowledge/build-spec/subsystems/07-robotstate.md`. **Imports only `edu.wpi.first.math.*` — no
   vendor, no subsystem objects.** *Done when:* AdvantageScope shows the robot pose in SIM.
4. **The logging facade.** Wire it once (`setup-logging`). *Done when:* every subsystem's inputs are
   visible in AdvantageScope.
5. **The coordination seam — `Superstructure` skeleton.** A goal enum + a single `applyGoal`/
   `requestGoal` transition function that fans a goal out to subsystem setpoints (start with a
   `switch`). See `knowledge/build-spec/subsystems/08-superstructure.md`. It holds subsystems, **not
   their IO impls and no vendor type.** *Done when:* a button request routes through `applyGoal`.

## Package layout (from elite-architecture §2.6)
```
frc/robot/
  Robot.java  RobotContainer.java  RobotState.java  Constants.java
  superstructure/ Superstructure.java
  subsystems/ drive/ { Drive, DriveConstants, ModuleIO(+Inputs), ModuleIO<device>, ModuleIOSim, GyroIO(+Inputs), GyroIO<device>, GyroIOSim }
  util/   (later → a versioned team library, D8)
```

## After the foundation
Hand off to the other skills: `add-subsystem` (stamp out each mechanism's IO quartet + test),
`setup-testing`, `setup-simulation`, `setup-logging`. Then `audit-architecture` to check the seams
held. Do **not** add fancy features (autos, vision fusion, state graph) until the seams exist — they
attach to seams (elite-architecture §3).
