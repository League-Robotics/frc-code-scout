---
title: 27. The portable swerve interface — the mid-level block
weight: 27
---
A drive subsystem is the first interesting block above the leaf: a `Block` whose children are four
module blocks, each two motor blocks. Its `Command_in` is a control-intent union, its `State` is the
fused drive state, and its `Command_out` is four module setpoints. Working it out shows
seam-granularity for what it is — *the altitude at which you draw a block boundary* — and reuses the
[motor interface](26-portable-motor-interface.md) wholesale. Part II built the swerve subsystem from
the corpus ([ch. 19](../part-2/19-the-drivetrain-subsystem.md)); this chapter gives it the portable
contract.

## They already agree

Put the field's four reference swerve systems side by side — CTRE Phoenix 6, Team 6328's AdvantageKit
template, YAGSL, and WPILib's math — and the apparent diversity collapses. Every one computes module
setpoints with the **same WPILib types** (`SwerveDriveKinematics`, `SwerveModuleState`, `ChassisSpeeds`,
`SwerveDrivePoseEstimator`). That is the shared substrate. They differ on exactly **two** decisions:
*where the hardware seam goes* and *whether there is a control-intent vocabulary.* So the design space
is not four architectures; it is one architecture with two open choices — and the field has already
produced the best answer to each. The right swerve is **"AdvantageKit's seam + CTRE's vocabulary, on
WPILib's math."**

## Five layers, one seam

```d2
direction: up
L0: "L0 — math substrate: WPILib SwerveModuleState / Position · ChassisSpeeds · Kinematics · PoseEstimator"
L1: "L1 — hardware seam: ModuleIO + GyroIO, inputs struct  ◄ THE seam — vendor types ONLY here"
L2: "L2 — module logic: optimize() · open/closed-loop selection · drive feedforward  (no vendor types)"
L3: "L3 — drive coordination: kinematics · pose estimator · signal-synced odometry thread · (optional) setpoint generator"
L4: "L4 — control vocabulary: SwerveRequest union (FieldCentric · FacingAngle · Brake · …)"
L0 -> L1 -> L2 -> L3 -> L4
L1.style.fill: "#1f3a5a"
L1.style.font-color: "#ffffff"
```

Two load-bearing rules, inherited from the rubric. **Vendor SDK types appear only at L1** — everything
L2 and above is WPILib-and-our-own-types only (the D1 rule applied to swerve). And **the seam is a data
struct, not a method bag** — L1's read side is a serializable inputs struct, which makes it
simultaneously the replay seam, the sim-mock seam, and the vendor-swap seam: one cut buys all three.

## L1 is just two motor blocks and an encoder

The seam to adopt is AdvantageKit's `ModuleIO`/`GyroIO` — minimal and field-proven: a per-module read
struct plus four write verbs (drive open-loop, drive velocity, steer open-loop, steer position), and a
gyro read struct. But the clean formulation is not a fresh interface. Those four verbs are exactly **two
motors' worth of the motor spec** plus an absolute encoder:

```
ModuleIO  ≙  { drive: Motor (velocity tier), steer: Motor (position tier), azimuth: AbsoluteEncoder }
```

So the swerve block inherits the motor block's nullable payloads, capability tiers, and ROS translation
for free — a steer motor is "a `Motor` whose `Command` is a position `oneof`," nothing new to design.
The flat five-method `ModuleIO` is a convenience facade over that canonical pair.

The one leak to legislate against: AdvantageKit's template reuses CTRE's `SwerveModuleConstants` as a
constants bag above the seam, because that is what the Tuner X generator emits. We disallow that —
constants cross as our own neutral record (`ModuleConstants{ driveGearRatio, wheelRadiusMeters,
locationMeters, encoderOffsetRot, … }`), populated *from* `TunerConstants` by the L1 adapter, never
referenced by type above it. This is the swerve form of *generate the constants, own the architecture.*

## Two altitudes for the seam

Where you cut L1 depends on what sits below it, and the corpus shows both in live elite use:

- **Per-module** — `ModuleIO` + `GyroIO`, the subsystem owning kinematics and odometry. Correct when
  you **build from motors**: the vendor abstraction stops at one drive + one steer + one encoder, four
  times over.
- **Per-drivetrain** — a single `DriveIO` wrapping an *entire vendor swerve* (CTRE's
  `CommandSwerveDrivetrain`), with the contract **`SwerveRequest` in, `SwerveDriveState` out.** Correct
  when you **inherit a vendor's swerve**, because CTRE already abstracts the four modules internally.
  This is the 254/2910 pattern: `CommandSwerveDrivetrain` is demoted to a plain device (it does *not*
  `implements Subsystem`) and a hand-owned `DriveSubsystem` sits on the seam.

Both are the same seam — data-struct read side, intent write side, vendor below only — cut at different
heights. **Rule of thumb: own the motors → per-module; inherit a vendor swerve → per-drivetrain.**

## L4: control is an intent object

AdvantageKit stops at `runVelocity(ChassisSpeeds)`; CTRE's `SwerveRequest` is the better idea worth
lifting — control is an intent object you hand the drivetrain each loop, not a method you call —
recast off vendor types as a tagged union, so requests are loggable and replayable like everything
else. The arms are not speculative; the counts are corpus reference frequencies across 683 repos (the
full cloned corpus — see [Appendix A](../appendices/how-we-developed-this/)), so
the union is the measured ~90% of real usage:

```
SwerveRequest = oneof {
    FieldCentric    { vx, vy, omega }                  // field frame, REP-103       [324×]
    FacingAngle     { vx, vy; Rotation2d heading }     // translate + θ-PID heading   [115×]
    ApplyChassisSpeeds { ChassisSpeeds; bool fieldRel} // path-follower entry         [127×]
    RobotCentric    { vx, vy, omega }                  //                              [80×]
    Brake { }                                          // X-lock the wheels            [119×]
    PointWheelsAt { Rotation2d angle }                 //                              [74×]
    Characterize { CharMode mode; double value }       // plant-response test          [~310×]
}
modifiers: DriveRequestType drive = OPEN_LOOP | VELOCITY  // lands on the two ModuleIO drive verbs
           wheelForceFeedforwardsX/Y                      // the L3 setpoint generator's per-module forces
```

(One vintage note: Phoenix 6's 2025 release split `ApplyChassisSpeeds` into `ApplyRobotSpeeds` and
`ApplyFieldSpeeds`; the counts above use the older class name because most of the corpus predates the
split.)

`DriveRequestType` *is* the whole open-vs-closed-loop switch, and it maps straight onto the two
`ModuleIO` drive verbs — no extra machinery. One naming decision is deliberate: the characterization
arm is **`Characterize`**, not CTRE's `SysId`. "System identification" collides head-on with software's
prior claims on both words — `getSysId()` in any other codebase returns a string handle, not a
feedforward routine — so it fails [ch. 26](26-portable-motor-interface.md)'s
survive-a-change-of-reader rule. The general
policy: *import a control term only if the destination domain hasn't already spent the word.* `plant`,
`chassis speeds`, `kinematics`, `pose` import cleanly; `system identification` and bare `observer` do
not.

## L3: state out, and the optional planner

State out is one immutable snapshot, modeled field-for-field on CTRE's `SwerveDriveState` — which is
itself a flat public-field POD, meaning CTRE independently arrived at the inputs-struct-as-data idea,
just without the replay seam around it. The field that matters: **`Pose` is read 682 times across the
corpus, more than any actuator field on any subsystem** — the empirical proof that the drivetrain is
the world-model anchor ([ch. 6](../part-1/06-the-drivetrain.md)). Its state snapshot, not its motion
command, is its primary output.

Odometry **must be signal-synced** — a 250 Hz (CAN FD) / 100 Hz (RIO) thread that samples drive,
steer, and gyro signals together and timestamps them — because timestamped high-rate samples are what
make vision fusion and replay correct; a bare 50 Hz `Notifier` (YAGSL) is not enough. The thread is a
property of the L1 adapter (it knows the vendor's signal API) and publishes into the inputs struct, so
L3 stays vendor-neutral. Above the modules sits the optional **`SwerveSetpointGenerator`**, a
dynamic-feasibility filter (pure WPILib-and-`DCMotor` math, no vendor types) that backs a desired
`ChassisSpeeds` off to one actually reachable this loop without slipping a wheel; prefer
PathPlannerLib's torque/friction model, and let its per-module force feedforwards flow down as the
arbitrary-feedforward field of the L1 drive command — closing the loop with the motor spec again.

A team climbs capability tiers — drive-only → fused localization → feasibility-planned — over the
*same L1*, never re-cutting the seam. And the whole stack crosses to ROS cleanly: a swerve drive is a
`Twist`-in / `Odometry`-out component with four `JointState` pairs underneath — the shape a
`ros2_control` swerve controller takes (cf. `diff_drive_controller`; swerve controllers exist as
third-party packages) ([ch. 31](31-ros-bridge-portability.md)). With the leaf and
mid-level blocks in hand, the next chapter recovers the two higher seams as blocks:
[`RobotState` and `Superstructure`](28-robotstate-superstructure-blocks.md).
