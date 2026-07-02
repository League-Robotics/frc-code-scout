# A Portable, Layered Swerve Drivetrain Interface

*A vendor-neutral specification for a swerve drive — the design that fell out of reading the
source of four reference systems (CTRE Phoenix 6's `SwerveDrivetrain`, Team 6328's AdvantageKit
swerve template, YAGSL, and WPILib's kinematics/estimator math) and asking what they actually
disagree about. The answer: almost nothing. They share the same math floor and differ on exactly
two decisions — **where the hardware seam goes** and **whether there is a control-intent
vocabulary**. This spec makes the rubric-correct choice at each layer and composes the result with
the [portable motor interface](portable-motor-interface.md).*

The corpus and the wider ecosystem gave us four good swerve abstractions, each optimizing a
different axis: CTRE optimizes time-to-drive and odometry fidelity, AdvantageKit optimizes
replay/testability, YAGSL optimizes zero-experience setup, WPILib optimizes nothing (it's the
neutral math everyone builds on). This spec extracts the durable structure as **five layers with
one seam**, and shows that the right swerve is "AdvantageKit's IO seam + CTRE's request vocabulary,
on WPILib's math" — each layer the best-of-breed already proven in the field.

> This is the **mid-level instance** of the [portable component model](portable-component-model.md):
> the drive subsystem is a *block* whose children are four module blocks, each two motor blocks. Its
> `Command_in` is the L4 `SwerveRequest` union, its `State` is `SwerveDriveState`, and its
> `Command_out` is four module setpoints. "Seam granularity" (§3.3) is just *at what level you draw a
> block boundary*.

---

## 0. The central finding: they already agree

Put the four systems' source side by side and the apparent diversity collapses. Every one of them
computes module setpoints with the **same WPILib types** — `SwerveDriveKinematics`,
`SwerveModuleState`, `SwerveModulePosition`, `ChassisSpeeds`, `SwerveDrivePoseEstimator`. That is
the shared substrate. On top of it:

- **CTRE** writes the module math *once* against device-type generics
  `SwerveDrivetrain<DriveMotor, SteerMotor, Encoder>` and exposes control as **`SwerveRequest`
  intent objects** — but the type parameters are CTRE classes, so there is no point below which a
  REV motor could substitute.
- **AdvantageKit** cuts a **`ModuleIO`/`GyroIO` inputs-struct seam** that isolates the vendor below
  a five-method line and makes the whole drivetrain replayable — but has no unified control
  vocabulary (you call `runVelocity(ChassisSpeeds)` and hand-roll teleop/heading-lock yourself).
- **YAGSL** cuts a seam too (`SwerveMotor`/`SwerveAbsoluteEncoder`/`SwerveIMU` abstract classes) and
  drives it from JSON — but the seam is leak-tolerant (`getMotor()` returns the raw vendor `Object`),
  non-replayable, and folds every layer into one ~1,600-line `SwerveDrive` class.

So the design space is not "four architectures." It is **one architecture with two open choices**,
and the field has already produced the best answer to each. This spec just names them and bolts
them together.

---

## 1. The layered model (the spine of this spec)

```
┌─ L4  Control vocabulary ──── intent objects (CTRE SwerveRequest, made vendor-neutral)
│        FieldCentric · RobotCentric · FacingAngle · ApplyChassisSpeeds · Brake · PointWheels · Idle
├─ L3  Drive coordination ──── kinematics + pose estimator + high-freq odometry thread
│        (optional) SwerveSetpointGenerator — dynamic-feasibility filter, sits here, above modules
├─ L2  Module logic ────────── pure: optimize() · open/closed-loop selection · drive feedforward   ◄ NO vendor types
├─ L1  Hardware seam ───────── ModuleIO + inputs struct  ·  GyroIO + inputs struct                  ◄ THE seam
│        impls: …TalonFX · …Spark · …ThriftyNova · …Sim   ◄ the ONLY place com.ctre / com.revrobotics appear
└─ L0  Math substrate ──────── WPILib SwerveModuleState/Position · ChassisSpeeds · Kinematics · PoseEstimator (given)
```

The two load-bearing rules, inherited from the build-spec and the rubric:

1. **Vendor SDK types (`com.ctre.*`, `com.revrobotics.*`, `org.photonvision.*`) appear only at L1.**
   Everything L2 and above is WPILib-and-our-own-types only. This is the D1 rule applied to swerve.
2. **The seam is a data struct, not a method bag.** L1's read side is a serializable *inputs
   struct*, which makes it simultaneously the replay seam (D5), the sim-mock seam (D3/D4), and the
   vendor-swap seam (D1) — one cut buys all three.

---

## 2. The four reference systems, mapped to the layers

| | **CTRE Phoenix 6** | **AdvantageKit (6328)** | **YAGSL** | **WPILib (L0)** |
|---|---|---|---|---|
| Spec format | constants (`TunerConstants`) | constants + hand-wired IO | JSON config dir | — |
| **Where the seam is** | device-type generics + `SwerveRequest` | **`ModuleIO`/`GyroIO` + `@AutoLog` struct** | `SwerveMotor`/`…Encoder`/`…IMU` abstract classes | none |
| **Vendor types live…** | *are* the drivetrain (top to bottom) | **only in `ModuleIOTalonFX`/`…Sim` (L1)** | in wrappers, but `getMotor()→Object` leaks | none |
| Control vocabulary (L4) | **`SwerveRequest` (rich)** | none (raw `ChassisSpeeds`) | `SwerveInputStream` (teleop only) | none |
| Odometry thread | 250 Hz CANivore / 100 Hz RIO, signal-synced | 250/100 Hz, signal-synced (`PhoenixOdometryThread`) | `Notifier`, 50 Hz real / 250 Hz sim, **not** signal-synced | — |
| Deterministic replay | no | **yes** | no | — |
| Multi-vendor | no (CTRE only) | yes (swap the IO impl) | yes (REV/CTRE/Thrifty, reflective) | — |
| Setpoint generator (L3) | external (PathPlanner) | 254-port (accel-limited) | built-in optimizations only | — |
| Sim | built-in, idealized | `ModuleIOSim` (+ maple-sim forks) | maple-sim **vendored in** | sim primitives |

**Read each row as "who to borrow from":** the seam from AdvantageKit, the control vocabulary from
CTRE, the math from WPILib, the setpoint generator from the 254→PathPlannerLib lineage. YAGSL is the
cautionary column — a real seam undermined by leak-tolerance, no replay, and god-class coupling.

---

## 3. L1 — the hardware seam (the one decision that matters)

This is the cut. Borrow AdvantageKit's shape verbatim, because it is already minimal and already
proven: a per-module **`ModuleIO`** with a read-side **inputs struct** and a handful of write verbs,
plus a **`GyroIO`**. Here is the actual AdvantageKit `ModuleIO` (BSD, Littleton Robotics) — the
reference this spec adopts:

```java
public interface ModuleIO {
  class ModuleIOInputs {                       // the serializable read side = replay/sim/swap seam
    boolean   driveConnected;
    double    drivePositionRad, driveVelocityRadPerSec, driveAppliedVolts, driveCurrentAmps;
    boolean   turnConnected, turnEncoderConnected;
    Rotation2d turnAbsolutePosition, turnPosition;
    double    turnVelocityRadPerSec, turnAppliedVolts, turnCurrentAmps;
    double[]  odometryTimestamps;              // ← high-freq samples, drained from the odom thread
    double[]  odometryDrivePositionsRad;
    Rotation2d[] odometryTurnPositions;
  }
  void updateInputs(ModuleIOInputs inputs);    // read
  void setDriveOpenLoop(double output);        // write: drive, open-loop (volts/duty)
  void setDriveVelocity(double velocityRadPerSec);  // write: drive, closed-loop velocity
  void setTurnOpenLoop(double output);         // write: steer, open-loop
  void setTurnPosition(Rotation2d rotation);   // write: steer, closed-loop position
}

public interface GyroIO {
  class GyroIOInputs {
    boolean    connected;
    Rotation2d yawPosition;  double yawVelocityRadPerSec;
    double[]   odometryYawTimestamps;  Rotation2d[] odometryYawPositions;
  }
  void updateInputs(GyroIOInputs inputs);
}
```

Five write verbs, two read structs. Implementations (`ModuleIOTalonFX`, `ModuleIOSpark`,
`ModuleIOThriftyNova`, `ModuleIOSim`) are the **only** files that import a vendor SDK.

### 3.1 Compose, don't duplicate: L1 *is* two `MotorIO`s + an encoder

The five `ModuleIO` verbs are exactly two motors' worth of the [portable motor
interface](portable-motor-interface.md): the drive motor used in velocity/open-loop mode, the steer
motor used in position/open-loop mode, plus an absolute encoder for steer feedback. The clean
formulation of this spec is therefore **not a fresh interface** but:

```
ModuleIO  ≙  { drive: MotorIO (velocity tier), steer: MotorIO (position tier), azimuth: AbsoluteEncoder }
```

where `MotorIO`, `Command`, and `MotorState` are the motor spec's PODs. The flat five-method
`ModuleIO` above is the *convenience facade*; the *canonical* model is two `MotorIO` ports. This
matters because it means the swerve spec inherits the motor spec's nullable-payload, capability-tier,
and ROS-translation machinery for free — a steer motor is "a `MotorIO` whose `Command` is a position
oneof," nothing new to design.

### 3.2 The one leak to legislate against

AdvantageKit's template has exactly one vendor type above L1: `Module.java` reuses
`com.ctre.phoenix6.swerve.SwerveModuleConstants` as a constants bag, because that is what the Tuner X
generator emits. This spec **disallows that** above L1 — constants cross the seam as our own neutral
record (`ModuleConstants{ driveGearRatio, steerGearRatio, wheelRadiusMeters, locationMeters,
encoderOffsetRot, slipCurrentAmps, ... }`), populated *from* `TunerConstants` by the L1 adapter, not
referenced by type at L2. This is the swerve form of doc 07's rule: **generate the constants, own the
architecture** — ingest the generator's numbers, never its types.

### 3.3 Seam granularity: cut below the motors, or below the whole drivetrain

There are **two altitudes** at which teams cut L1, and the right one depends on what sits below it.
Reading the corpus settles this empirically — both are in live use, by elite teams:

- **Per-module** — `ModuleIO` + `GyroIO` (the AdvantageKit template, §3 above). You cut below each
  *motor*; the subsystem owns kinematics + odometry. Correct when you **build from motors** — the
  vendor abstraction stops at one drive + one steer + one encoder, four times over.
- **Per-drivetrain** — a single `DriveIO`/`SwerveIO` that wraps an *entire vendor swerve* (CTRE's
  `CommandSwerveDrivetrain`). Correct when you **wrap a vendor's swerve**, because CTRE already
  abstracts the four modules internally — re-cutting per-module below it would be redundant. This is
  the **254 (`DriveIO` + `DriveIOHardware`/`DriveIOSim`) and 2910 (`SwerveIO` + `SwerveIOCTRE`/
  `SwerveIOSim`)** pattern: their `CommandSwerveDrivetrain` is demoted to a plain device (it does
  **not** `implements Subsystem`), and a hand-owned `DriveSubsystem` sits on top of the IO seam.

The coarse seam's contract is tiny and falls straight out of §5 and §6.1 — **`SwerveRequest` in,
`SwerveDriveState` out**:

```java
interface DriveIO {                 // the per-drivetrain seam (wraps CommandSwerveDrivetrain)
  void updateInputs(DriveIOInputs inputs);   // inputs ≙ the SwerveDriveState fields (§6.1)
  void setControl(SwerveRequest request);    // intent in  (§5)
  void addVisionMeasurement(Pose2d pose, double tSec, Matrix<N3,N1> stdDevs);
  void resetPose(Pose2d pose);
}
```

Both are the *same seam* (data-struct read side, intent write side, vendor types below only) cut at
different heights. **Rule of thumb:** own the motors → per-module `ModuleIO`; inherit a vendor swerve
→ per-drivetrain `DriveIO`. The two unavoidable leaks that *force* the wrap when you inherit CTRE's
drivetrain — the class **is** a `SwerveDrivetrain<TalonFX,…>` and `getModule(i)`/`getPigeon2()` hand
back raw vendor handles — are exactly why 254/2910 demote it below the line rather than subclass it.

---

## 4. L0 — the math currency (fix the units, inherit the types)

L0 is WPILib and is not ours to redesign; the spec's job is to *pin the contract* so every layer
speaks it. Verified against the WPILib 2026.2.2 javadoc:

- **`ChassisSpeeds{ vxMetersPerSecond, vyMetersPerSecond, omegaRadiansPerSecond }`** — the robot
  velocity currency. `fromFieldRelativeSpeeds(vx, vy, ω, Rotation2d robotAngle)` and the static
  **`discretize(speeds, dtSeconds)`** (second-order translate-while-rotating skew correction). Forward
  is +x, left is +y, CCW is +ω — REP-103, same frame as the motor spec.
- **`SwerveModuleState{ double speedMetersPerSecond; Rotation2d angle }`** — desired/measured per
  module. As of WPILib 2025, `optimize(Rotation2d)` and `cosineScale(Rotation2d)` are **instance**
  methods that mutate in place (the old static `optimize` is deprecated). L2 calls these.
- **`SwerveModulePosition{ double distanceMeters; Rotation2d angle }`** — the odometry accumulator.
- **`SwerveDriveKinematics(Translation2d... locations)`** — `toSwerveModuleStates(ChassisSpeeds)`,
  `toChassisSpeeds(SwerveModuleState...)`, and the in-place `desaturateWheelSpeeds(...)`.
- **`SwerveDrivePoseEstimator`** — `update(...)`, `addVisionMeasurement(Pose2d, timestampSeconds[,
  Matrix<N3,N1> stdDevs])`; std-dev vectors are ordered **[x_m, y_m, θ_rad]**.

**Rule:** L2 and above traffic *only* in these types plus our neutral constants/records. A
`SwerveModuleState` is the contract between L2 (which produces it) and L1 (which actuates it); a
`SwerveModulePosition[]` + gyro `Rotation2d` is the contract between L1 (which samples it) and L3
(which fuses it).

---

## 5. L4 — the control vocabulary (the second missing piece)

AdvantageKit stops at `runVelocity(ChassisSpeeds)`. CTRE's `SwerveRequest` is the better idea and
the one genuinely worth lifting: **control is an intent object you hand the drivetrain each loop**,
not a method you call. This spec adopts it, recast off CTRE types — and, consistent with the motor
spec's philosophy, modeled as **a tagged-union data object** (so requests are loggable, replayable,
and ROS-translatable like everything else), not a class hierarchy with hidden vendor state.

The CTRE seam, for reference:

```java
interface SwerveRequest { StatusCode apply(SwerveControlParameters params, SwerveModule<?,?,?>... modules); }
```

The neutral form — a `oneof` of intents plus shared modifiers. **The arms are not speculative:** the
annotations are corpus reference counts (683 repos), so this union is the measured ~90% of real CTRE
`SwerveRequest` usage, not a wish-list.

```
SwerveRequest = oneof {
    FieldCentric    { double vx, vy, omega }              // field frame, REP-103          [used 324×]
    FacingAngle     { double vx, vy; Rotation2d heading } // field translate, θ-PID heading [used 115×]
    ApplyChassisSpeeds { ChassisSpeeds speeds; bool fieldRelative }  // path-follower entry  [used 127× as ApplyRobot/FieldSpeeds]
    RobotCentric    { double vx, vy, omega }              // robot frame                    [used  80×]
    PointWheelsAt   { Rotation2d angle }                  //                                [used  74×]
    Brake           { }                                   // X-lock the wheels              [used 119×]
    Idle            { }                                   //                                [used  48×]
    Characterize    { CharMode mode; double value }       // plant-response test (see naming note) [SysId* used ~310×]
}
modifiers (apply to the translating variants):
    DriveRequestType  drive   = OPEN_LOOP_VOLTAGE | VELOCITY  // ← maps straight to ModuleIO.setDriveOpenLoop vs setDriveVelocity   [withDriveRequestType 337×]
    double            translationDeadband, rotationDeadband   // [148× / 126×]
    Perspective       forward = OPERATOR | BLUE_ALLIANCE       // CTRE's ForwardPerspectiveValue  [58×]
    Translation2d     centerOfRotation                        // [20×]
    bool              desaturateWheelSpeeds
    double[]          wheelForceFeedforwardsX, wheelForceFeedforwardsY  // ← the L3 setpoint generator's per-module forces (§6.2)  [44× / 40×]
```

The usage data drives two decisions. We **drop** `RobotCentricFacingAngle` (2 uses corpus-wide — noise)
and we **keep** `wheelForceFeedforwardsX/Y` as a first-class modifier: at 44/40 live uses it is the
*observed* path by which the L3 setpoint generator's per-module forces reach the wheels — the
L3→L1 feedforward channel §6.2 predicts, confirmed in the wild.

`apply(...)` runs the same pipeline every system implements: resolve the frame (`fromFieldRelative`
when needed) → `discretize` → `kinematics.toSwerveModuleStates` → `desaturateWheelSpeeds` →
per-module `optimize` → push a `SwerveModuleState` through L1. `DriveRequestType` is the whole
open-vs-closed-loop switch and it lands directly on the two `ModuleIO` drive verbs — no extra
machinery. Custom behaviors (e.g. a "drive to note" auto-aim) are just new union arms, exactly as
CTRE lets you write new `SwerveRequest` classes.

### 5.1 Naming: `Characterize` / plant-response, **not** `SysId`

CTRE's three characterization requests (`SysIdSwerveTranslation/Rotation/SteerGains`, ~310 corpus
uses combined) are the #2 most-referenced request family — so the neutral union must carry the
capability. But it must **not** carry CTRE's name for it. `SysId` ("System Identification") is a
control-theory import that **collides head-on with software's prior claims on both words**: *system*
reads as the machine/OS/infrastructure, *identification* reads as identity/auth, and the abbreviation
`sysId` is indistinguishable from a system identifier (a UUID, a PID, a tenant key) — `getSysId()` in
any other codebase returns a `String` handle, not a feedforward routine. It fails the motor spec's
core test (§ "Why these names"): **a name must survive a change of reader**, and "System
Identification" arrives in a software reader's head meaning something else entirely.

So this spec names the arm **`Characterize`** (with a `CharMode = { DRIVE_TRANSLATION, ROTATION,
STEER }`) — or `PlantResponse` if naming the observable is preferred. The rationale, for the record:

- **`plant`** is the one control-theory term software never spent — it imports with zero collision.
- **`response`** is already native characterization vocabulary (step/impulse/frequency *response*) and
  does not actively mislead a software reader the way *identification* does.
- It **names the observable** (how the drivetrain responds to a known input) rather than the *inverse
  problem* (solving for parameters). For an education program, naming the thing a student can see beats
  naming the estimation theory they don't have yet.
- **`characterization` is the term the FRC community already de-facto adopted** ("characterize the
  drive," "characterization gains") — `SysId` is the vestigial import the surrounding vocabulary already
  routed around. We follow the community's correction.

This is the general policy for the whole interface: **import a control term only if the destination
domain hasn't already spent the word.** `plant`, `chassis speeds`, `kinematics`, `pose` import
cleanly; `system identification`, `state` (vs. application state), and `observer` (vs. the Observer
pattern) do not — rename or qualify them at the seam.

---

## 6. L3 — drive coordination, and the optional setpoint generator

### 6.1 Odometry & state

L3 owns kinematics, the pose estimator, and the **high-frequency odometry thread** that drains the
`odometry*` arrays out of the L1 inputs structs. Here the systems differ in *fidelity*, and the spec
takes a position:

- **CTRE and AdvantageKit both run a true signal-synchronized thread** — 250 Hz on CAN FD
  (CANivore), 100 Hz on the roboRIO — that samples drive/steer/gyro status signals together and
  timestamps them. AdvantageKit's `PhoenixOdometryThread` registers each signal, `waitForAll(...)`s
  on CAN FD, and stamps samples with FPGA-aligned time (`monotonic − mean CAN latency`).
- **YAGSL runs a plain WPILib `Notifier`** at 50 Hz (real) / 250 Hz (sim) that is **not** aligned to
  CAN signal timestamps.

**The spec requires the signal-synced model**, because timestamped high-rate samples are what make
vision fusion (`addVisionMeasurement` with per-sample latency) and replay correct. The thread is a
property of the L1 adapter (it knows the vendor's signal API); it publishes into the inputs struct,
so L3 stays vendor-neutral.

State out is a single immutable snapshot, modeled field-for-field on CTRE's `SwerveDriveState` and
published via a registered callback that runs on the odometry thread — so telemetry/logging sees every
high-rate sample, not just the 50 Hz main-loop view. The field set (with corpus access counts across
683 repos, which double as a relevance ranking):

| Field | Type | accesses | role |
|---|---|---|---|
| `Pose` | `Pose2d` | **682** | the fused robot pose — *the* output everything consumes |
| `ModuleStates` | `SwerveModuleState[]` | 322 | measured per-module speed+angle |
| `Speeds` | `ChassisSpeeds` | 243 | measured robot velocity |
| `ModuleTargets` | `SwerveModuleState[]` | 154 | commanded per-module (for error/telemetry) |
| `OdometryPeriod` | `double` | 101 | health of the odom loop |
| `ModulePositions` | `SwerveModulePosition[]` | 55 | odometry accumulators |
| `RawHeading` | `Rotation2d` | 17 | gyro yaw before fusion |
| `SuccessfulDaqs` / `FailedDaqs` | `int` | 17 / 19 | thread sample health |
| `Timestamp` | `double` | ~0 | sample time |

Two things this confirms. **First, `Pose` is read 682× — far more than any actuator field on any
subsystem in the corpus** — which is the empirical proof that the drivetrain is the robot's
*world-model anchor*: it is simultaneously an actuator and the primary sensor, and what it senses
(where am I?) is the most-consumed value on the robot. The state snapshot, not the motion command, is
the drivetrain's most important output. **Second, CTRE already ships this as a flat, PascalCase,
public-field POD** — i.e. it independently arrived at exactly the *inputs-struct-as-data* idea this
spec champions at L1, just without the `@AutoLog`/replay seam wrapped around it. Modeling our
`DriveIOInputs` on these fields is therefore not invention; it is adopting the consensus the whole
field has already converged on.

### 6.2 The setpoint generator (optional, but the elite L3 addition)

A **`SwerveSetpointGenerator`** is a *dynamic-feasibility filter* that sits above the modules: given
the previous setpoint and a desired `ChassisSpeeds`, it returns a `SwerveModuleState[]` that is
actually reachable within one loop without slipping a wheel or outrunning a steer motor. It is pure
WPILib-and-`DCMotor` math — **no vendor types** — which is exactly why it belongs at L3, above the
seam: swapping CTRE↔REV or running in sim changes nothing about it.

The lineage matters, because the name hides two different physical models:

| Version | Limits model | `SwerveSetpoint` carries | Limit record |
|---|---|---|---|
| **254 (2022)** — original | **acceleration-limited** (kinematic) | `chassisSpeeds`, `moduleStates` | `KinematicLimits{maxDriveVelocity, maxDriveAcceleration, maxSteeringVelocity}` |
| **6328 (2024)** — port ("Inspired by 254") | **acceleration-limited** (kinematic) | `chassisSpeeds`, `moduleStates` | `ModuleLimits(maxDriveVelocity, maxDriveAcceleration, maxSteeringVelocity)` |
| **PathPlannerLib** (mjansen4857) — evolution | **torque/current + friction** (dynamic) | + `DriveFeedforwards` (per-module forces) | `RobotConfig`/`ModuleConfig` (`DCMotor`, `wheelCOF`, `driveCurrentLimit`, mass, MOI) |

```java
// shape (PathPlannerLib): returns a new feasible setpoint each loop
SwerveSetpoint generateSetpoint(SwerveSetpoint prev, ChassisSpeeds desiredRobotRelative, double dt[, double busVoltage]);
record SwerveSetpoint(ChassisSpeeds robotRelativeSpeeds, SwerveModuleState[] moduleStates, DriveFeedforwards feedforwards);
record DriveFeedforwards(double[] accelerationsMPSSq, double[] linearForcesNewtons,
                         double[] torqueCurrentsAmps, double[] robotRelativeForcesXNewtons, double[] robotRelativeForcesYNewtons);
```

It works by **binary-searching an interpolant `s∈[0,1]`** from `prev` toward `desired`, backing off
until every module satisfies: (a) max steer-rate `dt·maxSteerVel`; (b) max drive velocity, *scaled by
bus voltage* `maxVel·min(1, V/12)` then desaturated; (c) traction — the modern model bounds wheel
torque by what the motor can produce (`DCMotor.getCurrent`, clamped to `driveCurrentLimit`) capped at
the friction ceiling `μ·N`; (d) a centripetal/heading-change cap so cornering force stays under
friction. The 254/6328 ports approximate (c)/(d) with a single hand-tuned `maxDriveAcceleration`;
PathPlannerLib's advance is making that budget *physics-derived* and speed/voltage-dependent.

**Spec position:** the setpoint generator is **optional** (a strong team's upgrade, not a baseline
requirement), it lives at L3, and its `DriveFeedforwards.torqueCurrentsAmps` flows down as the
arbitrary-feedforward field of the L1 drive `MotorIO.Command` — closing the loop with the motor spec
again. If present, prefer PathPlannerLib's torque model over a hand-tuned acceleration limit.

---

## 7. Simulation

L1's `…IOSim` is the swerve form of the motor spec's sim story: the same inputs struct, populated by
a physics model instead of a vendor. Two fidelity tiers, both proven in the field:

- **Functional sim** (CTRE's `updateSimState(dt, batteryVolts)`): "perfect" kinematics, no scrub/slip,
  driven faster than the main loop (a 4 ms `Notifier`). Enough to develop logic and autos.
- **Physical sim** (maple-sim, which YAGSL vendors directly): models scrub, slip, and field
  collisions. The natural backing for the L3 setpoint generator's traction model — see
  [`../alternatives/02-physical-plant-simulation.md`](../alternatives/02-physical-plant-simulation.md).

Because the seam is the inputs struct, the *same* L2/L3/L4 code runs over either sim or real with no
changes — the D3/D4 payoff of cutting the seam at L1.

---

## 8. ROS harmonization (the same trick as the motor spec)

The whole point of a neutral design is that it crosses to ROS in both directions. The mapping is
clean because L0/L4 are already frame-honest:

| This spec | ROS 2 |
|---|---|
| `SwerveRequest.ApplyChassisSpeeds` / `FieldCentric` | `geometry_msgs/Twist` (cmd_vel) |
| `SwerveDriveState{Pose, Speeds}` | `nav_msgs/Odometry` |
| per-`ModuleIO` `MotorState` | `sensor_msgs/JointState` (name, position, velocity, effort) |
| `addVisionMeasurement(Pose2d, t, stdDevs)` | a pose source fused in `robot_localization` (EKF) |

A swerve drive *is* a `Twist`-in / `Odometry`-out component with four `JointState` pairs underneath —
which is exactly `ros2_control`'s diff/swerve controller shape. The L1 seam is the FRC analogue of
`ros2_control`'s hardware-interface; naming the contract this way (and reusing the motor spec's
`Command`/`MotorState` PODs) is what makes the bridge a translation table rather than a rewrite. See
[`../corpus-analysis/06-lessons-from-broader-robotics.md`](../archived/corpus-analysis/06-lessons-from-broader-robotics.md) §0.

---

## 9. Capability tiers (don't force one shape on every team)

Like the motor spec's capability spectrum, a swerve interface should degrade gracefully, not demand
the elite shape from a rookie:

- **Tier 0 — drive only.** L0+L1+L2+L4-`RobotCentric`/`FieldCentric`. Open-loop drive, closed-loop
  steer, WPILib odometry. This is a complete, testable, vendor-swappable drivetrain.
- **Tier 1 — fused localization.** + signal-synced odometry thread + `addVisionMeasurement`. The
  corpus baseline for a competitive team (AprilTag pose fusion).
- **Tier 2 — feasibility-planned.** + L3 `SwerveSetpointGenerator` (torque model) + `DriveFeedforwards`
  into the L1 drive command. The elite addition.

A team climbs tiers without re-cutting the seam — every tier is the same L1.

---

## 10. Summary of decisions

1. **One architecture, two choices.** The field's four swerve systems differ only on seam placement
   and control vocabulary; everything else is shared WPILib math.
2. **Cut the seam at L1 as an inputs struct** (AdvantageKit's `ModuleIO`/`GyroIO`). One cut = replay
   + sim-mock + vendor-swap. Vendor types appear *only* here.
3. **L1 is two `MotorIO`s + an encoder**, composing the [portable motor interface](portable-motor-interface.md) —
   not a new contract.
4. **Seam granularity follows what's below it** (§3.3): own the motors → per-module `ModuleIO`;
   inherit a vendor swerve → per-drivetrain `DriveIO` (`SwerveRequest` in / `SwerveDriveState` out),
   the 254/2910 pattern. Same seam, two altitudes.
5. **Constants cross the seam as our neutral record, never the vendor type** — ingest `TunerConstants`
   numbers, own the architecture (doc 07).
6. **Control is intent objects** (CTRE's `SwerveRequest`), modeled as a tagged union whose arms are the
   corpus-measured ~90% of real usage; `DriveRequestType` and `wheelForceFeedforwardsX/Y` land straight
   on the L1 drive verbs.
7. **Name for the destination domain, not control theory's** (§5.1): the characterization arm is
   `Characterize`/`PlantResponse`, **not** `SysId` — import a control term only if software hasn't
   already spent the word.
8. **Odometry must be signal-synced** (250/100 Hz timestamped), not a bare `Notifier` — it's what
   makes vision fusion and replay correct. `Pose` is the most-consumed value on the robot (682×):
   the drivetrain's state snapshot, not its motion command, is its primary output.
9. **The setpoint generator is an optional L3 filter**, pure math above the seam; prefer
   PathPlannerLib's torque/friction model; its force feedforwards flow into the L1 drive command.
10. **Tiered capability** — drive-only → fused localization → feasibility-planned, all over the same L1.

The one-line version: **AdvantageKit's seam + CTRE's vocabulary, on WPILib's math, with the
254→PathPlannerLib setpoint generator as the optional top — named for software, not for control theory.**

---

## Pointers (sources)

All claims below are source-verified (official docs, GitHub source read raw, or 2026.2.2 javadoc).

**CTRE Phoenix 6 Swerve API**
- Overview / builder / requests / simulation / usage:
  https://pro.docs.ctr-electronics.com/en/latest/docs/api-reference/mechanisms/swerve/swerve-overview.html
  (+ `swerve-builder-api`, `swerve-requests`, `swerve-simulation`, `using-swerve-api`).
- `SwerveDrivetrain<DriveMotor,SteerMotor,Encoder>`, `SwerveRequest.apply(SwerveControlParameters,
  SwerveModule<?,?,?>...)`, `SwerveDriveState`, `registerTelemetry`, 250/100 Hz odom thread,
  `updateSimState`, `FeedbackSource` Fused/Remote/Sync CANcoder: CTRE Java API
  https://api.ctr-electronics.com/phoenix6/stable/java/

**AdvantageKit swerve template (6328 / Littleton Robotics)** — read raw from GitHub `main`
- `Mechanical-Advantage/AdvantageKit`, `template_projects/sources/talonfx_swerve/.../subsystems/drive/`:
  `ModuleIO.java`, `GyroIO.java`, `Module.java`, `Drive.java`, `PhoenixOdometryThread.java`,
  `ModuleIOTalonFX.java`. Docs: https://docs.advantagekit.org/getting-started/template-projects/talonfx-swerve-template/

**WPILib L0 math** — verbatim from the 2026.2.2 Java javadoc
- `SwerveDriveKinematics`, `SwerveModuleState` (instance `optimize`/`cosineScale`, added 2025),
  `SwerveModulePosition`, `ChassisSpeeds` (`discretize`, `fromFieldRelativeSpeeds`),
  `SwerveDrivePoseEstimator` (`addVisionMeasurement`, `[x,y,θ]` std-devs):
  https://github.wpilib.org/allwpilib/docs/release/java/edu/wpi/first/math/kinematics/ and `/estimator/`.

**YAGSL** — read raw from `Yet-Another-Software-Suite/YAGSL`, `yagsl/java/swervelib/`
- `SwerveDrive.java`, `SwerveModule.java`, `motors/SwerveMotor.java` (+ `TalonFXSwerve`, `SparkMaxSwerve`,
  `ThriftyNovaSwerve`), `encoders/SwerveAbsoluteEncoder.java`, `imu/SwerveIMU.java`,
  `parser/SwerveParser.java`, `parser/json/DeviceJson.java`. Javadoc: https://broncbotz.org/YAGSL-Lib/docs/

**SwerveSetpointGenerator lineage**
- 254: https://github.com/Team254/FRC-2022-Public `.../lib/swerve/SwerveSetpointGenerator.java`
- 6328: https://github.com/Mechanical-Advantage/RobotCode2024Public `.../util/swerve/SwerveSetpointGenerator.java` + `ModuleLimits.java`
- PathPlannerLib: https://pathplanner.dev/pplib-swerve-setpoint-generator.html and
  `com.pathplanner.lib.util.swerve.{SwerveSetpoint,SwerveSetpointGenerator}`, `DriveFeedforwards`,
  `config.{RobotConfig,ModuleConfig}` (javadoc + source `mjansen4857/pathplanner`).

## See also (internal)

- [`../corpus-analysis/08-drivetrain-as-architecture.md`](../corpus-analysis/08-drivetrain-as-architecture.md) — the
  **empirical evidence** behind this spec: what 55 teams actually built, the architecture spectrum, the
  254/2910 package layout, and the corpus usage counts that validate §3.3, §5, §5.1, and §6.1.
- [`portable-motor-interface.md`](portable-motor-interface.md) — the `MotorIO` / `Command` / `MotorState`
  spec that L1 composes (drive motor + steer motor are two instances of it).
- [`../corpus-analysis/07-code-generators.md`](../corpus-analysis/07-code-generators.md) — the generator
  landscape; this spec is the concrete form of its "generate the constants, own the architecture" thesis.
- [`../corpus-analysis/03-io-layer-strategy-pattern.md`](../archived/corpus-analysis/03-io-layer-strategy-pattern.md) — why the L1 seam is ports-and-adapters.
- [`../build-spec/subsystems/06-swerve-drivetrain.md`](../build-spec/subsystems/06-swerve-drivetrain.md) — the
  build-out: the `ModuleIO`+`GyroIO` quartet a team actually writes.
- [`../alternatives/02-physical-plant-simulation.md`](../alternatives/02-physical-plant-simulation.md) — the
  L1 `…IOSim` / maple-sim fidelity dial.
- [`../corpus-analysis/06-lessons-from-broader-robotics.md`](../archived/corpus-analysis/06-lessons-from-broader-robotics.md) — the
  `ros2_control` hardware-interface analogy behind §8.

## Open questions for a deeper build-out

1. **Should L1 be the flat five-method facade or the two-`MotorIO` canonical form in the actual
   `scaffold-robot` output?** The facade is what every shipping template uses; the composed form is
   cleaner but heavier. Decide which one `add-subsystem`/`scaffold-robot` emits by default.
2. **Whether to ship a `TunerConstants → ModuleConstants` adapter** as a first-class tool (the §3.2
   move), so CTRE-hardware teams get the generator's numbers without the generator's types — the most
   concrete unbuilt artifact this research surfaced.
