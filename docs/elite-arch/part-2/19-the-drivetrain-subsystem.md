---
title: 19. The drivetrain subsystem
weight: 19
---

*The drivetrain is the one subsystem that breaks the single-IO rule. It is built from two interfaces (`ModuleIO` ×4 plus `GyroIO` ×1), a module is two control loops behind one contract, and it carries the only real math that belongs above the IO line. This chapter is the deep dive that [Part I, chapter 6](../part-1/06-the-drivetrain.md) deferred: where chapter 6 made the empirical case that the drivetrain is both an actuator and the robot's primary sensor, here we build it.*

[Part I, chapter 6](../part-1/06-the-drivetrain.md) established the facts. The drivetrain is the only subsystem that is both an actuator and the robot's primary sensor; its most-consumed output is `Pose`, read 682 times across the 684-repo full clone — more than any actuator field on any subsystem. Of the ~49 classified swerve drivetrains in the 55-repo season index, about 63% stand on CTRE's generated drivetrain in some form (48% as-is, 14% wrapped), and only about 27% own a real IO seam. This chapter takes those facts as given and shows how the seam is built — at both granularities teams cut it.

The drivetrain is the load-bearing example for everything earlier in Part II: the IO seam ([chapter 16](16-hardware-abstraction.md)), the motor interface that a module composes ([chapter 17](17-motor-interfaces.md)), and the velocity and position archetypes a module fuses into one contract ([chapter 18](18-subsystem-archetypes.md)). It is also the bridge to [the world model](20-the-world-model.md): the pose it estimates is the value the rest of the robot reads.

---

## 19.1 Two control problems, four times, plus kinematics

A swerve drivetrain moves and rotates the robot by independently steering and driving four corner modules, and it maintains odometry — where am I, computed from wheel motion plus gyro. It is the most complex subsystem on the robot, but it is the same IO pattern scaled up. The `Drive` subsystem holds four `ModuleIO`s and one `GyroIO`, runs kinematics above them, and never names a motor.

Three pieces of logic live in or around the subsystem:

- A **module** is a velocity loop (the drive wheel, the velocity archetype) *and* a position loop (the turn/azimuth, the rotational-position archetype) behind one `ModuleIO`. Two control problems, one contract, four copies.
- **Kinematics** (`SwerveDriveKinematics`) lives in the `Drive` subsystem, above the line. It converts a robot-level `ChassisSpeeds` into four `SwerveModuleState`s and back. This is the one subsystem with real math above the IO line, and that is correct — kinematics is vendor-free geometry.
- **Odometry**: each module reports its drive distance and turn angle, the gyro reports yaw, and a `SwerveDrivePoseEstimator` fuses them into a pose. Vision then corrects it ([chapter 21](21-vision-systems.md)).

```d2
Drive: {
  shape: class
  -modules: "ModuleIO[4]"
  -gyro: GyroIO
  -kinematics: SwerveDriveKinematics
  -estimator: SwerveDrivePoseEstimator
  +drive(ChassisSpeeds)
  +pose(): Pose2d
}
ModuleIO: {
  shape: class
  +updateInputs(ModuleIOInputs)
  +runDriveVelocitySetpoint(v, ff)
  +runTurnPositionSetpoint(angle)
}
GyroIO: {
  shape: class
  +updateInputs(GyroIOInputs)
}
ModuleIOTalonFX: { shape: class }
ModuleIOSim: { shape: class }
GyroIOPigeon2: { shape: class }
GyroIOSim: { shape: class }
Drive -> ModuleIO: "holds (4)"
Drive -> GyroIO: holds
ModuleIOTalonFX -> ModuleIO: implements
ModuleIOSim -> ModuleIO: implements
GyroIOPigeon2 -> GyroIO: implements
GyroIOSim -> GyroIO: implements
```

### High-frequency odometry

Good drivetrains sample module positions and gyro yaw at 250 Hz, not the 50 Hz robot loop, so odometry does not smear during fast motion. That is why the inputs carry *arrays* — `odometryDrivePositionsMeters[]`, `odometryTurnPositions[]`, `odometryYawPositions[]` — a batch of timestamped samples per cycle, not a single reading. This is the swerve-specific detail that distinguishes a serious drivetrain from a working one. The thread only produces the samples; the loop that consumes them is shown in §19.2.

---

## 19.2 The per-module seam — `ModuleIO` + `GyroIO`

When you build the drivetrain from motors, the seam is cut per module. Each module gets one `ModuleIO`; the heading sensor gets its own `GyroIO`. This is the AdvantageKit template, used by the six per-module teams in the 55-repo season index (6328 and 2637 among them).

### `ModuleIO` — drive (velocity) + turn (position) in one interface

| Method | Crosses as | Archetype |
|---|---|---|
| `runDriveVelocitySetpoint(v, ff)` | command | velocity |
| `runTurnPositionSetpoint(angleRads)` | command | rotational position |
| `runDriveVolts` / `runCharacterization` | command | open-loop / characterization |
| `setDrivePID` / `setTurnPID` | config | on-motor loops |
| `updateInputs(inputs)` | input | positions, velocities, odometry sample arrays |

The 6328 AdvantageKit drive is the most-forked swerve base in FRC and the reference for the per-module pattern:

*6328 Mechanical Advantage — `RobotCode2024Public/.../subsystems/drive/ModuleIO.java`*

```java
public interface ModuleIO {
  @AutoLog class ModuleIOInputs {
    public double drivePositionRads, driveVelocityRadsPerSec, driveAppliedVolts;
    public Rotation2d turnAbsolutePosition, turnPosition;          // azimuth (rotational)
    public double turnVelocityRadsPerSec;
    public double[] odometryDrivePositionsMeters = new double[] {}; // 250 Hz batches
    public Rotation2d[] odometryTurnPositions = new Rotation2d[] {};
  }
  default void updateInputs(ModuleIOInputs inputs) {}
  default void runDriveVelocitySetpoint(double velocityRadsPerSec, double feedForward) {} // velocity loop
  default void runTurnPositionSetpoint(double angleRads) {}                                // position loop
  default void setDrivePID(double kP, double kI, double kD) {}
  default void setTurnPID(double kP, double kI, double kD) {}
  default void setDriveBrakeMode(boolean enable) {}
  default void stop() {}
}
```

One interface, two control problems. `runDriveVelocitySetpoint` is the velocity command; `runTurnPositionSetpoint` is the position command. The inputs struct carries both single-cycle readings and the 250 Hz odometry arrays.

### `GyroIO` — the second, tiny interface

A heading sensor is not a module, so it gets its own interface. It is the smallest IO in the codebase — yaw and odometry yaw samples, no actuation. Like vision, the gyro is sensor-only.

*6328 Mechanical Advantage — `RobotCode2024Public/.../subsystems/drive/GyroIO.java`*

```java
public interface GyroIO {
  @AutoLog class GyroIOInputs {
    public boolean connected = false;
    public Rotation2d yawPosition = new Rotation2d();
    public Rotation2d[] odometryYawPositions = new Rotation2d[] {};
    public double yawVelocityRadPerSec = 0.0;
  }
  default void updateInputs(GyroIOInputs inputs) {}
}
```

`ModuleIOTalonFX` and `GyroIOPigeon2` are the device implementations, where the vendor SDK is confined. `ModuleIOSim` and `GyroIOSim` wrap `DCMotorSim`s (or maple-sim). Neither interface names a `TalonFX`, `Pigeon2`, or `CANcoder`; neither carries kinematics — that is the subsystem's job — and neither carries field or auto logic.

### The subsystem takes its IO by constructor

The `Drive` subsystem takes its IOs by constructor — the cleanest expression of the seam. From SciBorgs' construction:

```java
drive = new Drive(gyro, frontLeft, frontRight, rearLeft, rearRight);  // 1 GyroIO + 4 ModuleIO
```

`Drive` owns the `SwerveDriveKinematics`, the `SwerveDrivePoseEstimator`, and the 250 Hz odometry thread. It converts `ChassisSpeeds` to module setpoints and reads odometry back — all above five IO seams, none of which name a vendor.

The consuming side of the 250 Hz thread from §19.1 lives in `Drive.periodic()`. The thread only fills the sample arrays; each 20 ms loop drains every batched sample into the pose estimator in timestamp order, so the estimate integrates at 250 Hz even though the robot loop runs at 50:

```java
// Drive.periodic(), abridged — drain the 250 Hz batches into the estimator
for (int i = 0; i < sampleTimestamps.length; i++) {        // several samples per 20 ms loop
  for (int m = 0; m < 4; m++)
    positions[m] = new SwerveModulePosition(
        moduleInputs[m].odometryDrivePositionsMeters[i],
        moduleInputs[m].odometryTurnPositions[i]);
  poseEstimator.updateWithTime(
      sampleTimestamps[i], gyroInputs.odometryYawPositions[i], positions);
}
```

---

## 19.3 Two granularities of the seam

The per-module template is not the only place to cut. The corpus shows there are two granularities at which teams cut the IO seam, and the right one depends on what is below it.

| Granularity | seam | who | when it's right |
|---|---|---|---|
| **Per-module** | `ModuleIO` + `GyroIO` (one drive + steer + encoder ×4) | AdvantageKit template, the 6 per-module teams | you **build from motors** |
| **Per-drivetrain** | one `DriveIO`/`SwerveIO` wrapping the whole CTRE swerve | 254, 2910 | you **wrap a vendor's swerve** |

Both are the same seam — data-struct on the read side, intent on the write side, vendor types below only — cut at different heights. The deciding factor is what is below the line. If you build from motors, there is no swerve abstraction yet, so you cut per module. If you wrap CTRE's swerve, the vendor has already abstracted the modules for you; re-cutting per-module below `CommandSwerveDrivetrain` would be redundant. So 254 and 2910 cut once, around the whole thing.

The coarse, per-drivetrain contract is tiny: **`SwerveRequest` in, `SwerveDriveState` out.** That is the whole surface, and the rest of this chapter is about that surface and how elite teams keep `com.ctre` behind it.

---

## 19.4 The CTRE `CommandSwerveDrivetrain` device surface

About 63% of teams stand on CTRE's generated drivetrain, so its surface is the de-facto drive API. What it is:

```java
class CommandSwerveDrivetrain extends TunerSwerveDrivetrain implements Subsystem
//    TunerSwerveDrivetrain extends SwerveDrivetrain<TalonFX, TalonFX, CANcoder>
```

CTRE's generic `SwerveDrivetrain<TalonFX, TalonFX, CANcoder>` plus the one `implements Subsystem` that makes it command-schedulable. The generated subclass adds a tight surface. These are the consensus methods, by team prevalence, across the 19 of the 55 season repos that define a class named `CommandSwerveDrivetrain`. (Nineteen is a class-name count, so it undershoots the ~31 of 49 swerve repos — the 63% above — that stand on the generator in some form: renamed and customized copies escape it.)

| Method | teams | role |
|---|---|---|
| `applyRequest(Supplier<SwerveRequest>)` | 16 | the control entry point (`= run(() -> setControl(req))`) |
| `startSimThread()` | 15 | 5 ms `Notifier` → `updateSimState(dt, V)` |
| `periodic()` | 12 | applies alliance/operator perspective |
| `addVisionMeasurement(...)` | 11 | pose fusion (often overridden for `fpgaToCurrentTime`) |
| `sysIdQuasistatic` / `sysIdDynamic` | 10 | characterization |
| `configureAutoBuilder` | 6 | PathPlanner wiring |

Everything substantive — `setControl`, `getState`, `registerTelemetry`, `resetPose`, `setOperatorPerspectiveForward` — is inherited from CTRE's `SwerveDrivetrain`. Two leaks force a wrap if you want vendor-neutrality: the class *is* a `SwerveDrivetrain<TalonFX,…>`, and `getModule(i)` / `getPigeon2()` return raw `TalonFX` / `Pigeon2`. Strip it to the contract and it is exactly the coarse `DriveIO` of §19.3 — request in, state out.

### The two contract types

The two CTRE types that *are* the drive contract, ranked by real corpus usage.

`SwerveRequest` is the control vocabulary — intent objects, not method calls:

```java
interface SwerveRequest { StatusCode apply(SwerveControlParameters params, SwerveModule<?,?,?>... modules); }
```

| Request (by corpus uses) | uses | purpose |
|---|---|---|
| `FieldCentric` | 324 | field-relative translate + rotate (default teleop) |
| `SysIdSwerveRotation` | 129 | rotation characterization |
| `SwerveDriveBrake` | 119 | X-lock the wheels |
| `FieldCentricFacingAngle` | 115 | field translate, heading held by a θ-PID |
| `ApplyRobotSpeeds` (+ `ApplyFieldSpeeds` 25) | 102 | raw `ChassisSpeeds` (path-follower entry) |
| `SysIdSwerveTranslation` / `SysIdSwerveSteerGains` | 92 / 91 | translation / steer characterization |
| `RobotCentric` | 80 | robot-relative drive |
| `PointWheelsAt` | 74 | aim modules at one angle |
| `Idle` | 48 | do nothing |

Builder usage confirms the modifier surface: `withVelocityX/Y` (368 / 353), `withDriveRequestType` (337, the open-vs-closed-loop switch), `withRotationalRate` (294), `withDeadband` / `withRotationalDeadband` (148 / 126), `withTargetDirection` (101, for FacingAngle), `withForwardPerspective` (58), and `withWheelForceFeedforwardsX/Y` (44 / 40) — the channel by which a setpoint generator's per-module forces reach the wheels.

`SwerveDriveState` is the output, modeled as a flat, PascalCase, public-field POD. Field-access counts:

| Field | accesses | | Field | accesses |
|---|---|---|---|---|
| `Pose` | **682** | | `ModulePositions` | 55 |
| `ModuleStates` | 322 | | `FailedDaqs` / `SuccessfulDaqs` | 19 / 17 |
| `Speeds` | 243 | | `RawHeading` | 17 |
| `ModuleTargets` | 154 | | `Timestamp` | ~0 |
| `OdometryPeriod` | 101 | | | |

`Pose` is read 682 times — more than any actuator field on any subsystem in the corpus. That number is the proof that the drivetrain's most important output is not its motion command but its state estimate, *where am I*, because auto, aiming, and vision all consume it. CTRE shipped this state as a flat data struct — the same inputs-struct-as-data idea AdvantageKit formalizes with `@AutoLog`, arrived at independently. Modeling a neutral `DriveIOInputs` on these fields adopts a convergent consensus rather than inventing one.

---

## 19.5 Demoting CTRE below the line — the 254/2910 pattern

The clearest evidence of the elite pattern is what the strongest teams' `drive/` directories contain. Two examples, verbatim from disk:

```
254 (2025)  subsystems/drive/          2910 (2026)  subsystems/drive/
  DriveSubsystem.java   <- Subsystem      SwerveSubsystem.java   <- Subsystem
  DriveIO.java  @AutoLog <- IO SEAM        SwerveIO.java  @AutoLog <- IO SEAM (two inputs structs)
  DriveIOHardware.java  <- real impl       SwerveIOCTRE.java      <- real impl
  DriveIOSim.java       <- sim impl        SwerveIOSim.java       <- sim impl
  CommandSwerveDrivetrain.java <- CTRE     CommandSwerveDrivetrain.java <- CTRE device
  Comp/Prac/SimTunerConstants  <- owned    SetModulePositionsRequest.java <- custom SwerveRequest
  DriveViz.java         <- telemetry
```

Three things this layout proves:

1. **The three roles are split into separate files.** `DriveSubsystem` (the command target) sits on top of `DriveIO` (the seam to the device), with the pose estimator inside the subsystem.
2. **The generated `CommandSwerveDrivetrain` is demoted to a device.** In both repos it does *not* `implements Subsystem` — it is a plain class wrapped by `DriveIOHardware` / `SwerveIOCTRE` so `com.ctre` stops at the seam and never reaches the subsystem. Contrast the 48% who let the generated class be their subsystem directly.
3. **They ingest the generator's constants but own the architecture.** 254 keeps three `TunerConstants` variants (`Comp` / `Prac` / `Sim`) as owned files: generate the numbers, own the architecture.

The hand-rolled end of the spectrum reaches for a seam in spirit too. Team 868's Ri3D `Drivetrain extends SubsystemBase implements BaseSwerveDrive` — a team-defined `BaseSwerveDrive` interface — shows even a one-week robot wants a contract in front of the hardware.

The vendor rule, stated plainly:

> **Banned above the line:** `com.ctre.*`, `com.revrobotics.*`, the Pigeon/NavX SDK. They live in `ModuleIOTalonFX` / `GyroIOPigeon2`, or in `DriveIOHardware` / `SwerveIOCTRE` when wrapping a vendor swerve. Allowed above: WPILib `kinematics`, `geometry`, `SwerveDrivePoseEstimator`.

The honest exception: CTRE's Tuner X generator produces a `SwerveDrivetrain` you call directly, and YAGSL is a swerve library with its own internal seam. Both put a vendor or library type above *your* IO line. That is a deliberate trade — you give up the clean seam (and the simple sim and test below) in exchange for a configured drivetrain in an afternoon. If you take it, keep the generated drivetrain behind your own thin `DriveIO`-style wrapper so the rest of the robot still does not import `com.ctre`. Otherwise a swerve-vendor change becomes a robot-wide refactor. Teams that hand-roll `ModuleIO` (6328) keep the seam — as does 254, whose 2025 code wraps the generated swerve behind a per-drivetrain `DriveIO` instead; teams that generate and stop there trade it away knowingly.

---

## 19.6 The optional `SwerveSetpointGenerator`

The `withWheelForceFeedforwardsX/Y` builders above hint at a third tier of control. A `SwerveSetpointGenerator` sits between the desired `ChassisSpeeds` and the module setpoints, enforcing module slew limits and traction constraints so the drivetrain does not command states the wheels cannot achieve. It produces per-module force feedforwards that ride into the request through those `withWheelForceFeedforwards` channels.

This is elite-practice tail, not baseline. `SwerveSetpointGenerator` appears in 9 teams and maple-sim in 11 — the same small set that owns the seam. It is optional; the contract works without it. But when present it lives above the IO line, like kinematics, because it is constraint math over geometry, not a vendor call.

---

## 19.7 Mock below, test above

The swerve test is the richest mock-below example in the corpus. Construct `Drive` from four `SimModule`s and a `NoGyro`, command velocities, and assert both the chassis speeds *and* the odometry pose:

*1155 SciBorgs — `Reefscape-2025/src/test/java/.../robot/SwerveTest.java`*

```java
@BeforeEach public void setup() {
  setupTests();
  drive = new Drive(new NoGyro(),
                    new SimModule("FL"), new SimModule("FR"),
                    new SimModule("RL"), new SimModule("RR"));   // 5 IO mocks
}

@RepeatedTest(5) public void reachesRobotVelocity() {
  double vx = rand(), vy = rand();
  run(drive.drive(() -> vx, () -> vy, () -> Rotation2d.kZero, () -> 0));
  fastForward(500);
  ChassisSpeeds s = drive.fieldRelativeChassisSpeeds();
  assertEquals(vx, s.vxMetersPerSecond, DELTA);                 // kinematics correct
  assertEquals(vy, s.vyMetersPerSecond, DELTA);
}

@RepeatedTest(5) public void testModuleDistance() {
  // command a field-relative velocity for deltaT seconds...
  run(c); fastForward(Seconds.of(deltaT));
  Pose2d pose = drive.pose();
  assertEquals(deltaX, pose.getX(), DELTA * 4);                 // odometry integrates correctly
  assertEquals(deltaY, pose.getY(), DELTA * 4);
}
```

This single test exercises kinematics *and* odometry with no hardware. `reachesRobotVelocity` checks the `ChassisSpeeds`-to-module-state math; `testModuleDistance` drives for a fixed time and asserts the pose moved the integrated distance. SciBorgs leaves `systemCheck` and the align-to-pose test `@Disabled` — honest about which parts the sim is tuned for. It works only because `Drive` takes its five IOs by constructor; swap in real `ModuleIOTalonFX` / `GyroIOPigeon2` and the same `Drive` runs the robot.

Sim has two levels. Per-module `DCMotorSim` simulates each motor independently — enough to test kinematics and odometry. maple-sim runs whole-drivetrain rigid-body physics including wheel slip and collisions — the rung where sim can surprise you. The 11 teams with maple-sim back `ModuleIOSim` with whole-drivetrain dynamics rather than four independent motors.

---

## 19.8 Rip it out as a library

The drivetrain is the subsystem teams most successfully extract. `3061-lib`, YAGSL, and CTRE's generator are all "swerve as a dependency." The `drive/` package needs WPILib geometry and kinematics plus its IO interfaces; its only outward coupling is feeding pose to `RobotState`, or owning the estimator itself. It must not import `Arm`, `Intake`, or `Superstructure`.

That it is the most commonly published-as-a-library subsystem is proof the seam holds when you keep kinematics vendor-free and the motors (or the whole vendor swerve) behind an IO. The seam at either granularity buys the same thing: a drivetrain you can test in sim, swap vendors under, and lift into the next season's robot.

---

## 19.9 Checklist — is your drivetrain intact?

- [ ] A seam cut at the right granularity: per-module `ModuleIO` + `GyroIO` if you build from motors, a single per-drivetrain `DriveIO` / `SwerveIO` if you wrap a vendor swerve.
- [ ] `ModuleIO` carries both `runDriveVelocitySetpoint` (velocity) and `runTurnPositionSetpoint` (position), plus odometry sample arrays for high-frequency integration.
- [ ] A separate, sensor-only `GyroIO` (yaw + odometry yaw).
- [ ] `Drive` takes its IO by constructor; kinematics and pose estimator live in the subsystem, vendor-free.
- [ ] If you generate the drivetrain (Tuner X / YAGSL), `CommandSwerveDrivetrain` does not `implements Subsystem` — it is demoted behind your own IO so `com.ctre` stops at the line.
- [ ] A test builds `Drive` from sim modules + a no-op gyro and asserts chassis speeds *and* odometry pose.
- [ ] (Stretch) `ModuleIOSim` uses maple-sim for whole-drivetrain physics; a `SwerveSetpointGenerator` enforces traction limits above the line.

---

The drivetrain owns the pose, but it does not own the *world*. Pose is one input to a larger estimate that fuses vision, game-piece tracking, and field state. The next chapter follows that pose off the drivetrain and into [the world model](20-the-world-model.md).
