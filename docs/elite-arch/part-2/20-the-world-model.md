---
title: 20. The world model
weight: 20
---

*Part I argued for centralizing the robot's pose estimate into one shared object; it deferred the mechanics. This chapter shows them: RobotState as a subsystem with no hardware, the two input streams it reconciles, the time-interpolating buffer that rewinds and replays them, and the unit test that makes it the easiest class on the robot to verify.*

[Part I chapter 4](../part-1/04-the-state-seam.md) made the case for the state seam: one fused estimate that vision, pathing, and auto all share, instead of each subsystem keeping its own guess. That chapter stopped at the boundary. This one crosses it — how observations come in, how a delayed vision frame gets reconciled against fast odometry, and what the class is and is not allowed to import.

## A subsystem with no hardware

Every other subsystem in this half of the book owns a mechanism: a drivetrain ([19](19-the-drivetrain-subsystem.md)), an elevator or arm ([18](18-subsystem-archetypes.md)), a camera ([21](21-vision-systems.md)). Each has an IO layer ([16](16-hardware-abstraction.md)) hiding a vendor device behind an interface ([17](17-motor-interfaces.md)), and each runs a control loop ([15](15-control-path.md)) that turns a setpoint into motor output.

RobotState has none of that. Its IO is *observations in, belief out*. Sensors write to it — the drivetrain feeds wheel odometry, vision feeds AprilTag corrections — and decisions, pathing, and auto read from it. No motor ever moves. It is the purest example of the architecture's ethic: zero vendor types, zero IO implementations, just math. That same purity makes it the single most testable class on the robot.

It owns the robot's best belief about the world — where it is on the field (pose), and, at the top of the ladder, its game-piece and mechanism state too. Centralizing that belief is what makes vision, pathfinding, and auto agree on "where are we." It is the difference between a pose estimate merely *existing* and a world model *being* the architecture.

## The I/O boundary — two streams, no control loop

Two streams come in, at different rates and latencies:

```
Drive  → addOdometryObservation(wheelPositions, gyro, t) ┐
Vision → addVisionObservation(pose, t, stdDevs)          ├→ RobotState → getPose() / sampleAt(t)
                                                          ┘   (everyone reads)
```

**Odometry** is fast and continuous but drifts — integrate wheel motion long enough and the estimate wanders. **Vision** is accurate but sparse and *delayed*: a camera frame is timestamped in the past, because capture, exposure, and pose solving all take time. By the moment a vision pose lands, the robot has already moved.

RobotState reconciles the two with a **time-interpolating buffer**. It keeps roughly two seconds of timestamped odometry poses. When a delayed vision measurement arrives, it rewinds to where the robot *was* at that observation's timestamp, blends the correction in by a Kalman gain, and replays odometry forward to now. The "IO" here is purely informational — observations in, a fused `Pose2d` out.

```d2
direction: right
DR: "Drive subsystem"
VIS: "Vision subsystem"
RS: "RobotState
pose estimator + time buffer"
AUTO: "Auto / Path / Aim / Superstructure"
DR -> RS: "odometry (fast)"
VIS -> RS: "vision obs (delayed)"
RS -> AUTO: "getPose()"
RS -> VIS: "sampleAt(t)"
```

The diagram has an arrow most readers skip: `sampleAt(t)` runs *back* toward Vision. Vision asks RobotState what the pose was at a past instant so it can latency-correct its own measurement before handing it back. The buffer is shared infrastructure, not a one-way sink.

## The contract

### The API

| Method | Direction | Why |
|---|---|---|
| `addOdometryObservation(obs)` | in (write) | integrate wheel motion + gyro into the estimate, buffer it |
| `addVisionObservation(obs)` | in (write) | blend a timestamped AprilTag pose by its std-dev weight |
| `getPose()` / `getEstimatedPose()` | out (read) | the fused belief — what auto and aiming use |
| `sampleAt(timestamp)` | out (read) | the pose at a past instant (for latency-correcting a measurement) |
| `resetPose(pose)` | in | seed the estimate (auto start, operator reset) |

Five methods. Two write, two read, one seeds. Everything a consumer needs and nothing it does not.

### What the contract omits

There is no `TalonFX`, no `PhotonCamera`. There is no IO interface and — this is the part teams get wrong — **no `Drive` or `Vision` object reference**. RobotState does not hold the subsystems that feed it; it holds only the *observations* they hand over: a `Pose2d`, a `SwerveModulePosition[]`, a timestamp, a std-dev vector. It carries no commands and no game logic. It is pure `edu.wpi.first.math` geometry.

The test for whether your contract is clean is mechanical: grep the imports. If you find a vendor package or a subsystem class, the seam has leaked.

## Real implementation — 6328's RobotState

6328 Mechanical Advantage hand-rolls its estimator rather than using WPILib's built-in one. The reason is the buffer: hand-rolling buys ownership of the replay logic, and ownership is what lets the rest of the world model grow off the same object. The file is `RobotCode2025Public/.../RobotState.java`.

### The observations in

```java
public void addOdometryObservation(OdometryObservation obs) {
  Twist2d twist = kinematics.toTwist2d(lastWheelPositions, obs.wheelPositions());
  lastWheelPositions = obs.wheelPositions();
  odometryPose = odometryPose.exp(twist);
  obs.gyroAngle().ifPresent(g -> odometryPose =
      new Pose2d(odometryPose.getTranslation(), g.plus(gyroOffset)));   // gyro overrides integrated heading
  poseBuffer.addSample(obs.timestamp(), odometryPose);                  // ◀ the 2-second time buffer
  estimatedPose = estimatedPose.exp(lastOdometryPose.log(odometryPose));
  lastOdometryPose = odometryPose;                                      // remember for the next delta
}
```

Read it top to bottom. Wheel positions become a `Twist2d` (a small motion delta) through the kinematics. That twist is composed onto `odometryPose` with `.exp()`. If a gyro angle is present it overrides the integrated heading — wheels are good at distance, a gyro is better at heading. The new odometry pose is stamped into `poseBuffer` with its timestamp; that single line is the two-second history the vision blend depends on. Finally the fused `estimatedPose` advances by the same delta the raw odometry just took.

Note what is being kept separate. `odometryPose` is the pure dead-reckoning track. `estimatedPose` is the fused belief. The buffer holds the odometry track so the estimate can be rewound and recomputed when a correction arrives.

### The vision blend — latency-corrected, std-dev weighted

```java
public void addVisionObservation(VisionObservation obs) {
  // skip if older than the buffer; else get the odometry pose AT the observation's timestamp
  var sample = poseBuffer.getSample(obs.timestamp());
  if (sample.isEmpty()) return;
  // the rewind: odometry accumulated since the sample, and the estimate as it stood back then
  Transform2d sampleToOdometryTransform = new Transform2d(sample.get(), odometryPose);
  Pose2d estimateAtTime = estimatedPose.plus(new Transform2d(odometryPose, sample.get()));
  // build a 3x3 Kalman gain by comparing obs.stdDevs() against the estimator's fixed odometry
  // std-devs, blend vision into the rewound estimate, then replay odometry forward to now:
  Matrix<N3,N3> visionK = /* from obs.stdDevs() vs. odometry std-devs */;
  Transform2d correction = new Transform2d(estimateAtTime, obs.visionPose());
  // scaledByK is pseudocode — scale the correction's (x, y, θ) by the gain's diagonal
  estimatedPose = estimateAtTime.plus(scaledByK(correction, visionK)).plus(sampleToOdometryTransform);
}
public record VisionObservation(Pose2d visionPose, double timestamp, Matrix<N3,N1> stdDevs) {}
```

The first two lines are the latency correction. `poseBuffer.getSample(obs.timestamp())` retrieves where the robot was at the moment the frame was captured — not now. If the observation is older than the buffer holds, the method returns rather than guessing.

The blend is three operations. `visionK` is a 3×3 Kalman gain built by comparing the observation's std-devs against the estimator's fixed odometry std-devs — trust is relative, not absolute: a measurement tighter than the odometry pulls the estimate hard toward the vision pose, a looser one barely nudges it. `correction` is the transform from the rewound estimate to the vision pose. The estimate gets the correction scaled by the gain, *then* `sampleToOdometryTransform` replays the odometry that accumulated between the observation's timestamp and now. The result is a pose that incorporated the past measurement but is current.

That `record VisionObservation` is the whole input type — a pose, a timestamp, a std-dev matrix. No camera, no pipeline, no vendor handle. Vision computes those three values and hands them over.

The estimator core is roughly 80 lines of `edu.wpi.first.math` — `Twist2d`, `Transform2d`, `Matrix`, `TimeInterpolatableBuffer` — though the full `RobotState` is larger, because it also carries the game-piece and mechanism state described next. Grep the imports and you will not find one vendor type. The state seam is math, not hardware.

### The world model grows off it

6328's `RobotState` does not stop at pose. It also carries `@AutoLogOutput` game-piece observations (coral and algae for the 2025 game), robot velocity, and mechanism state like `elevatorExtensionPercent` and `intakeDeployPercent`. The robot's belief about *everything* lives in one inspectable, logged place. That is the D7 L4 world model: not just where the robot is, but a shared, logged model of the whole situation.

## Who owns the estimator — the D7 climb

The state seam sits on the rubric's D7 ladder; [chapter 21](21-vision-systems.md) has the full 0–4 table. What matters for this chapter is *ownership*. At D7 L2 the estimator is WPILib's `SwerveDrivePoseEstimator` — a RobotState-lite with `addVisionMeasurement`, the time buffer, and the Kalman fusion already built in — owned *privately by Drive*, so vision and auto have to reach into the drivetrain to read or correct the pose. At D7 L4 the estimator is *extracted* into a dedicated `RobotState`, decoupled from Drive: vision and auto talk to the world model, not the drivetrain, and the model has room to grow into game-piece and mechanism state. (L3, between them, is the trust gate — rejection and weighting before fusing — also chapter 21's territory.)

The architectural move is the *extraction*: making one object the place pose lives. Hand-rolling the estimator (6328) is the upgrade that follows — it buys ownership of the replay buffer and the blend. Whether `RobotState` is a singleton (6328's `getInstance()`) or constructor-injected is a style choice — injected is friendlier to tests, as the next section shows.

Across the corpus, a `RobotState` class — a named, dedicated world-model object rather than an estimator buried in Drive — appears in 26 of the 55 repos in the season index.

## The easiest test on the robot, and the least written

### Nothing to mock

Every other subsystem test needs a mock IO below the line so the control loop has something to drive in simulation. RobotState has no IO and no loop. It takes plain data. So the test is trivial:

```java
// the test RobotState makes possible (and most teams never write):
// helpers (abridged): odom(t) builds an OdometryObservation at time t for a straight
// 1 m/s +X drive; tightStdDevs = VecBuilder.fill(0.05, 0.05, 0.05) — a high-trust measurement
var state = new RobotState(kinematics);
state.resetPose(Pose2d.kZero);
// feed a straight 1 m/s drive for 1 s as odometry samples...
for (double t = 0; t < 1.0; t += 0.02) state.addOdometryObservation(odom(t));
assertEquals(1.0, state.getPose().getX(), 0.02);                 // odometry integrates
state.addVisionObservation(new VisionObservation(new Pose2d(0.9,0,kZero), 0.98, tightStdDevs));
assertTrue(state.getPose().getX() < 1.0);                        // vision pulled it back
```

Two assertions cover the contract. The first feeds a straight one-meter drive as odometry samples and checks that the estimate integrated to roughly one meter — dead reckoning works. The second feeds a single tight vision observation reading 0.9 m at timestamp 0.98 and checks that the fused pose moved *back* toward it — the blend works. No HAL, no robot, no other subsystem. Feed observations, assert the belief.

This is the finding worth dwelling on: RobotState is the most unit-testable class on the robot — pure functions of input, nothing to mock, no hardware to stand up — and almost nobody tests it. It is the highest-value test a team is not writing.

Constructor injection helps here. `new RobotState(kinematics)` is a one-liner because the kinematics is passed in; a singleton that reaches into `Drive` for its kinematics cannot be built this cleanly in a test.

### Already a library

RobotState imports `edu.wpi.first.math.*` and nothing else load-bearing. It is *already* a standalone, reusable estimator — you could lift it into another project unchanged. The thing that would break that property is importing a subsystem object or a vendor type. If either appears, the seam has leaked.

### Vendor discipline — trivially clean, and that is the point

> A correct `RobotState` cannot leak a vendor type **because it never touches hardware.** If you see `com.ctre` or `org.photonvision` in your RobotState, something is wrong — a subsystem is handing it a device handle instead of an observation. The fix is at the caller: subsystems compute `Pose2d` / observations and pass *those*.

Most chapters in this book frame vendor discipline as work — building IO interfaces, hiding device types behind them. RobotState is the one place where the discipline costs nothing, because the class has no hardware to hide. That makes it a clean signal: a vendor import in RobotState is not a style nit, it is proof a subsystem is leaking device handles across a boundary that should only ever carry data.

## Checklist — is your state seam intact?

- [ ] One `RobotState` owns the pose estimate; Drive does **not** privately own the estimator.
- [ ] It takes `addOdometryObservation` + `addVisionObservation(pose, t, stdDevs)` and exposes `getPose()` / `sampleAt(t)`.
- [ ] A `TimeInterpolatableBuffer` reconciles delayed vision against past odometry.
- [ ] Its imports are WPILib math/geometry (plus logging) only — **no vendor, no IO impl, no subsystem object**.
- [ ] Vision feeds it (and only it); auto and aim read pose *from* it, never from Drive.
- [ ] A unit test feeds odometry plus a vision observation and asserts the fused pose — the easy test almost no one writes.

---

The world model is where every other subsystem's output converges and where the next layer's input begins. The stream that corrects it — sparse, delayed, and the hardest to trust — gets its own chapter next: [21. Vision systems](21-vision-systems.md).
