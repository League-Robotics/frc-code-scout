---
title: 21. Vision systems
weight: 21
---

*Vision is the subsystem that breaks the mold: no motor, no setpoint, no control loop. The IO is a pure sensor that produces observations, and the subsystem's only job is to hand them to the world model. This chapter follows the whole path — coprocessor to observation to `VisionIO` interface to `RobotState.addVisionMeasurement` — and shows where the trust gate sits, what the system produces, and who reads each output.*

[Chapter 4, the state seam](../part-1/04-the-state-seam.md), named vision as the input that fuses into `RobotState` and pointed here for the rest. This is that deep dive. Vision feeds the world model of [chapter 20](20-the-world-model.md): everything downstream — auto, pathing, aiming — reads the *fused* pose from `RobotState` and never talks to the camera. Part I argued why localization matters; this chapter shows the vision system end to end.

## What the subsystem is for

A vision subsystem turns what the cameras see — AprilTags on a known field — into a correction to the robot's belief about where it is. It actuates nothing. It reads camera frames, computes a field-relative pose estimate with a timestamp and a confidence, and hands that to `RobotState`, which fuses it with wheel odometry. This is why vision is a subsystem at all: it owns the camera hardware behind an IO seam so the rest of the robot stays vendor-agnostic.

That seam matters more for vision than for any other mechanism, because the vendor choice is a live, mid-season decision. PhotonVision and Limelight are competing coprocessor stacks, and teams switch between them when one performs better at an event. A clean `VisionIO` makes that switch a one-file change. A team that calls `LimelightHelpers.getBotPose()` directly inside its drivetrain has welded itself to Limelight — the exact leak the seam exists to prevent.

`addVisionMeasurement` is called in **50 of 55** corpus teams. A note on the name before it recurs: WPILib's estimator calls this method `addVisionMeasurement`, while 6328's hand-rolled `RobotState` calls its equivalent `addVisionObservation` — the same seam under two names, and the corpus grep marker is `addVisionMeasurement`. Pose estimation is assumed; it is the floor, not the ceiling. The differences that separate teams are *where* pose estimation runs and *how* bad observations are rejected before they corrupt the estimate.

## The pipeline, end to end

There is no control loop. The data moves one direction, from camera to world model:

```
Camera → VisionIO.updateInputs(observations) → Vision subsystem (filter by ambiguity / std-dev)
       → RobotState.addVisionObservation(pose, timestamp, stdDevs) → pose estimator fuses with odometry
```

The governing rule: **vision never talks to drive.** It writes a measurement to `RobotState`; drive, auto, and aiming all read pose *from* `RobotState`. Swapping PhotonVision for Limelight is a new `VisionIO` implementation and touches nothing else.

```d2
direction: right
CAM: "Camera (PhotonVision / Limelight)"
VIO: "VisionIO impl
(vendor confined HERE)"
VSUB: "Vision subsystem
(reject high-ambiguity)"
RS: "RobotState
(pose estimator)"
DRIVE: "Drive / Auto / Aim (read only)"
CAM -> VIO
VIO -> VSUB: "PoseObservation(pose, t, stdDevs)"
VSUB -> RS: "addVisionObservation"
RS -> DRIVE: "getPose()"
```

Each stage has a job. The camera and coprocessor detect tags and, in most stacks, compute a candidate pose. The `VisionIO` implementation receives that result and packages it as an observation — pose, timestamp, and the evidence needed to weight it. The subsystem applies the trust gate, rejecting or downweighting weak frames. `RobotState` blends the surviving observations into the pose estimator. The rest of the robot reads only the fused result.

### Where the pose is computed

Two architectures split the corpus by where the estimation work lands:

- **Estimate on the RIO.** 3061 Huskie Robotics runs a `PhotonPoseEstimator` inside the IO implementation and emits a `Pose2d` observation. Everything stays in robot code; nothing extra runs off-board. Simpler, but the RIO does the math.
- **Estimate on a coprocessor.** 6328 Mechanical Advantage's "Northstar" computes the pose off-RIO; the IO just receives frames or poses over NetworkTables. Limelight MegaTag is the same shape — the coprocessor produces the pose, the IO reads it. Less RIO load, more infrastructure to maintain.

Both feed the same `addVisionObservation` call. The difference is which side of the NetworkTables boundary the `PhotonPoseEstimator` work happens on, and that difference is hidden behind the IO interface.

## The `VisionIO` seam

Vision is the archetype where the IO contract is most clearly *sensor-only*. The interface produces observations and accepts camera configuration. It exposes nothing that moves the robot.

| Method | Crosses as | Why |
|---|---|---|
| `updateInputs(inputs)` | input only | fills the observation struct (poses, timestamps, tags seen, fps) |
| `setPipeline(int)` / `setRecording(bool)` | config | camera configuration — not robot actuation |

There is no `setVoltage`, no `setSetpoint`. The absence *is* the archetype. A `VisionIO` that exposed an actuation method would be a category error — vision being asked to drive something.

### The observation carries evidence, not an answer

The inputs do not hand down a single trusted pose. They hand down the *evidence* so the subsystem can decide how much to trust it: a per-frame timestamp, the estimated pose or poses, which tags were used, and the ambiguity and average tag distance that downstream code turns into a standard-deviation weight. 6328 logs raw frames; 3061 logs computed `PoseObservation`s already carrying `averageAmbiguity` and `averageTagDistance` so the subsystem can reject or downweight bad frames.

Here is the input struct from 6328 — note that what crosses the seam is observations, never commands:

```java
public interface VisionIO {
  @AutoLog class AprilTagVisionIOInputs {
    public double[] timestamps = new double[] {};
    // one row per frame, packed flat for NT/log transport: pose count, error, then the
    // candidate pose(s) as translation + quaternion, then the tag IDs used — decoded on the RIO
    public double[][] frames = new double[][] {};   // observations, not commands
    public long fps = 0;
  }
  // VisionIOInputs / ObjDetectVisionIOInputs are sibling structs of the same shape
  // (abridged — full file: RobotCode2025Public/.../vision/VisionIO.java)
  default void updateInputs(VisionIOInputs inputs, AprilTagVisionIOInputs aprilTagInputs,
                            ObjDetectVisionIOInputs objDetectInputs) {}
  default void setRecording(boolean active) {}      // config, not actuation
}
```

The struct omits any `PhotonCamera` or `LimelightHelpers` type, any drivetrain reference, and any game logic. It is timestamps, poses, and tag evidence.

### The Photon implementation confines the vendor

The vendor SDK lives in exactly one file. This is the 3061 RIO-side implementation:

```java
import org.photonvision.PhotonCamera;            // ◀ the ONLY place a vendor vision type appears
import org.photonvision.PhotonPoseEstimator;

public class VisionIOPhotonVision implements VisionIO {
  protected final PhotonCamera camera;
  protected final PhotonPoseEstimator photonEstimator =   // strategy fixed at construction
      new PhotonPoseEstimator(fieldLayout, PoseStrategy.MULTI_TAG_PNP_ON_COPROCESSOR, robotToCamera);

  @Override public void updateInputs(/* ... */) {
    for (PhotonPipelineResult result : camera.getAllUnreadResults()) {
      Optional<EstimatedRobotPose> visionEstimate = photonEstimator.update(result);
      // ...compute averageAmbiguity, averageTagDistance per observation,
      //    push PoseObservation(pose, timestamp, stdDevs) into the inputs...
    }
  }
}
```

`org.photonvision` appears here and nowhere else. A `VisionIOLimelight` is a sibling file implementing the same contract with `LimelightHelpers` and MegaTag2 — 254 and many others run this variant. When a team swaps Photon for Limelight, they write the sibling and change which IO they construct. The subsystem, `RobotState`, and the whole robot stay the same.

> **MegaTag2 is not a symmetric swap.** It must be seeded with the robot's gyro heading every cycle (`LimelightHelpers.SetRobotOrientation(...)`), and because its solve is rotation-constrained by that seed, teams typically fuse only x/y and inflate the θ std-dev. The IO contract holds; the sibling file carries this extra choreography.

The discipline, stated as a rule: banned above the IO line are `org.photonvision.*` and `LimelightHelpers`. They live only in `VisionIOPhotonVision` / `VisionIOLimelight`. Allowed above the line are WPILib geometry types (`Pose2d`, `Transform3d`) and your own observation record.

### A sim variant for a sensor

A sensor has no physics plant, so "sim" does not mean modeling dynamics. It means producing fake observations. A `VisionIOSim` either renders tags from a simulated field pose with PhotonLib's `PhotonCameraSim`, or it replays logged frames. Either way it implements `VisionIO` and pushes observations into the same input struct, so the subsystem above it cannot tell sim from hardware — the same sim-parity property the rest of Part II relies on.

This is why a logged match is so useful for vision: a recorded match *is* a stream of real observations. Replayed through the same code under AdvantageKit, it reproduces every fusion decision the robot made, which makes vision logic testable off-robot with no camera and no field.

## The consumer — `RobotState.addVisionMeasurement`

The subsystem's one downstream coupling is to the state seam. The Vision subsystem calls the vision-measurement method — `addVisionObservation` in 6328's hand-rolled form, shown here; `RobotState` blends the measurement into its pose estimator, weighted by the standard deviations the observation carried:

```java
public void addVisionObservation(VisionObservation observation) { /* fuse into pose estimator */ }
public record VisionObservation(Pose2d visionPose, double timestamp, Matrix<N3, N1> stdDevs) {}
```

This is the seam from [chapter 4](../part-1/04-the-state-seam.md) and the world model of [chapter 20](20-the-world-model.md). Vision attaches here, and *only* here. The coupling is intended — feeding `RobotState` is vision's whole purpose — but it should be a method on a small interface rather than a reference to the concrete `RobotState`, so the `vision/` package lifts out as a library. The package may import WPILib and, in the IO implementation, the vendor SDK; it must not import `Drive` or any other subsystem.

At D7 L2–L3, `RobotState` typically wraps WPILib's `SwerveDrivePoseEstimator`; at L4 some teams hand-roll the equivalent ([chapter 20](20-the-world-model.md)). Either way, the `stdDevs` matrix sets, per measurement, how much the estimator should trust this vision pose against the wheel odometry it already has. A measurement with small std-devs pulls the estimate toward the vision pose; one with large std-devs barely moves it. The trust gate, then, is mostly a matter of choosing those std-devs well — or refusing to fuse at all.

> **Timestamp epoch — the most common silent failure.** The measurement timestamp must be on the same clock as the estimator. NetworkTables time, FPGA time, and CTRE's time-synced clock are different epochs; CTRE's swerve API provides `Utils.fpgaToCurrentTime(...)` for exactly this conversion. Fuse with the wrong epoch and every measurement rewinds to the wrong moment — the pose quietly degrades with no error anywhere.

## The trust gate — std-dev and ambiguity gating

This is the rung that separates a team that merely calls `addVisionMeasurement` from one that does localization well. AprilTag pose estimates are not uniformly reliable. A tag seen edge-on, far away, or alone produces an ambiguous pose — the solver cannot tell which of two orientations is correct. Ambiguity is a *single-tag* concept: with one tag the PnP solver faces two mirror solutions, while a multi-tag solve has no pose ambiguity at all — which is why multi-tag observations earn trust. Fusing a bad frame blindly jumps the robot's belief and breaks aiming and auto. The gate weights or rejects each observation *before* it reaches the estimator.

The discriminating markers, from the rubric, are `setVisionMeasurementStdDevs` (dynamic per-measurement std-dev tuning) and a `VisionIO` interface with a sim variant (vision decoupled from `Drive`). The inputs carry `averageAmbiguity` and `averageTagDistance` precisely so this gate has something to act on. A typical policy: reject observations above an ambiguity threshold outright; for the rest, scale the std-devs up with tag distance so far tags count for less; trust multi-tag solutions more than single-tag ones. A concrete anchor for that policy is a formula of the shape `stdDev = base * avgTagDistance² / tagCount` — trust falls with the square of distance and rises with the number of tags. 3061 and 254 both weight and reject by ambiguity and tag distance before fusing.

## The D7 rubric ladder

Dimension D7 of the [rubric](../appendices/how-we-developed-this/02-the-rubric.md) measures what the robot believes about where it is and how that belief is maintained. The vision system maps onto its levels directly:

| Level | Anchor | What it looks like in the vision system |
|---|---|---|
| 0 | None | No vision; odometry unused in decisions |
| 1 | Targeting only | Limelight `tx`/`ty` servoing on a target; no pose estimation |
| 2 | Pose estimation | AprilTag pose feeding `addVisionMeasurement` — the near-universal floor (50/55) |
| 3 | Fused, filtered | std-dev tuning, multi-camera fusion, rejection logic; vision behind an IO interface with a sim variant |
| 4 | World model as architecture | a dedicated `RobotState` owning pose + game-piece state with time-interpolated buffers; localization decoupled from control |

The level is not set by whether `addVisionMeasurement` is called — it nearly always is. It is set by the *filtering* (the trust gate of the previous section) and the *architecture* (the IO seam and the central world model). Both must be read in the code to score, because `addVisionMeasurement`'s presence is the L2 floor and says nothing about L3. The corpus prevalence backs this: `addVisionMeasurement` in 50 teams, but a `*PoseEstimator` in 36 and a `*RobotState` class in only 26 — pose estimation is far more common than a centralized world model, so the L2-vs-L4 split is real.

## FRC localization is a known-map problem

Why AprilTag fusion rather than SLAM? The field geometry ships as CAD months before the season, so the robot does not need to build a map of an unknown environment — it needs to find itself on a map it already has, which is exactly what fiducial pose fusion does. SLAM solves a harder problem the field does not pose; the fuller argument is in the [Lessons from Outside appendix](../appendices/lessons-from-outside/01-lessons-from-outside.md).

## The rungs past AprilTag fusion

Two techniques layer on top of the AprilTag floor for teams that have reached it.

**Neural game-piece detection.** Beyond pose, teams run an on-coprocessor object detector — a neural model on a Limelight or PhotonVision pipeline — that reports the bearing, and sometimes the range, to game pieces. A "drive-to-piece" auto or teleop-assist routine then turns to and intakes the best available target. The detector is mainstream: **31 teams** carry one (including 254, 971, 1678, 2056, 2637). The detector itself is the easy half; the differentiating part is the architecture on top — closed-loop drive-to-piece with rejection of bad detections and a graceful fallback when nothing is seen. Architecturally this is the same shape as AprilTag vision: a sensor that produces an observation (here a bearing instead of a pose) crossing the same kind of IO seam.

**QuestNav.** A Meta Quest headset is a cheap, very good inside-out 6-DOF tracker — it has to be, to render VR without nausea. QuestNav mounts one on the robot and streams its pose over NetworkTables, where it is fused with AprilTag vision as a high-rate, low-drift odometry source. It is the newest item here — **1 team** in the corpus (7028's 2026 season code, using the `gg.questnav` library) — and emerging across FRC for 2026. The point for this chapter: the Quest does not need a new architecture. It is one more observation feeding the same `RobotState` pose estimator, behind the same kind of IO seam.

## What the vision system produces, and who consumes it

The whole system, read by output, comes down to four things crossing into the rest of the robot — and each has a specific consumer:

| Output | Carried as | Consumed by |
|---|---|---|
| Field-relative pose estimate | `Pose2d` + timestamp | `RobotState`'s pose estimator (the fusion) |
| Standard deviations | `Matrix<N3, N1>` | the fusion's per-measurement trust weighting |
| Latency timestamp | `double` seconds | the time-interpolated buffer, so the measurement applies at the moment it was captured, not when it arrived |
| Target bearing (neural detector) | angle, optional range | the aim — drive-to-piece auto and teleop-assist |

The pose estimate and its std-devs and timestamp go to the fusion in `RobotState`. The fused pose then reaches the aim and the auto, but indirectly: they call `RobotState.getPose()`, never the camera. The neural detector's bearing is the one output that drives an aiming behavior directly. Nothing in this list is an actuation command — the vision system observes and reports, and the consumers decide what to do.

## Checklist

- [ ] A `VisionIO` whose methods are `updateInputs(...)` plus camera config — no actuation method.
- [ ] Observations carry timestamp, pose, and ambiguity/tag-distance, so they can be weighted.
- [ ] The implementation (`VisionIOPhotonVision` / `VisionIOLimelight`) is the only file importing `org.photonvision` / `LimelightHelpers`.
- [ ] Vision feeds `RobotState`'s vision-measurement method (`addVisionMeasurement`, or a hand-rolled `addVisionObservation`) and never references the drivetrain.
- [ ] High-ambiguity or far-tag observations are rejected or downweighted before fusing (the D7 L3 gate).
- [ ] A test publishes a known observation and asserts the fused pose responds, and that a bad frame is rejected.

---

The vision system produces a belief and the trust to attach to it; the [world model](20-the-world-model.md) holds that belief over time, and the coordinator decides what to do with it. The other archetypes that feed the same seams are in [chapter 18](18-subsystem-archetypes.md); the drivetrain that reads the fused pose is in [chapter 19](19-the-drivetrain-subsystem.md). For how the actuating subsystems get their commands, see [the control path](15-control-path.md), [hardware abstraction](16-hardware-abstraction.md), and [motor interfaces](17-motor-interfaces.md).

NEXT: [22. Coordination — state machines](22-coordination-state-machines.md), where the executive layer turns the world model into intent. Graphs and trees follow in [chapter 23](23-coordination-graphs-trees.md).
