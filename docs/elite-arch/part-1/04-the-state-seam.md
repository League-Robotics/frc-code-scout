---
title: 4. The state seam — RobotState
weight: 4
---
The second seam is a single object that owns the robot's best belief about the world — where it is on
the field, and later its game-piece and mechanism state. Sensors *write* to it; decisions, pathing,
and autonomous *read* from it. One fused estimate that everything shares, rather than each subsystem
keeping its own guess.

## Sensors in, belief out

`RobotState` has no hardware and no control loop. Its "IO" is purely informational: observations in,
a fused pose out.

```d2
direction: right
DR: Drive subsystem
VIS: Vision subsystem
RS: "RobotState
pose estimator + time buffer"
CONS: Auto / Path / Aim / Superstructure
DR -> RS: odometry (fast)
VIS -> RS: vision obs (delayed)
RS -> CONS: getPose()
RS -> VIS: sampleAt(t)
```

Two streams arrive at different rates and latencies. **Odometry** is fast and continuous but drifts.
**Vision** is accurate but sparse and *delayed* — an AprilTag frame is timestamped in the past.
`RobotState` reconciles them with a time-interpolating buffer: it keeps a couple of seconds of
timestamped odometry poses, so when a delayed vision measurement arrives it can rewind to where the
robot *was* at that timestamp, blend the correction in by its trust weight, and replay odometry
forward to now. The mechanics of that blend are [Part II ch. 20](../part-2/20-the-world-model.md); what
matters here is that the reconciliation happens in one place.

## Why centralizing it is the architectural move

Pose estimation itself is not the elite signal — it is the floor. WPILib's
`SwerveDrivePoseEstimator` already does odometry-plus-vision fusion, and `addVisionMeasurement` appears
in 50 of 55 corpus teams. The common shape is a pose estimator owned *privately by the drivetrain*,
with vision reaching into the drive subsystem to correct it.

The architectural move is pulling that estimate out of the drivetrain into its own object, so vision,
pathfinding, and autonomous all read one consistent world model instead of reaching into the drive
class. That is the difference the rubric marks between D7 level 2 (a pose estimate exists) and level 4
(a world model is the architecture):

| Level | Shape | Who |
|---|---|---|
| L2 | a `SwerveDrivePoseEstimator` owned privately by Drive; `addVisionMeasurement` called from vision | most teams |
| L3 | + std-dev / ambiguity **rejection** before fusing | 3061, 254 |
| L4 | a dedicated `RobotState` owning the estimator + time buffer, decoupled from Drive; a world model of pose + game-piece + mechanism state | 6328, 254 |

The levels are cumulative, not a partition — a team at L4 also does the L3 rejection, which is why
254 appears in both rows.

At L4 the object stops being "pose" and becomes the robot's belief about everything — 6328's
`RobotState` also carries game-piece observations, robot velocity, and even mechanism extension, so
"where am I and what's the situation" lives in one inspectable, logged place.

## The cleanest class on the robot

Because `RobotState` takes plain data — a `Pose2d`, a `SwerveModulePosition[]`, a timestamp — and
returns a fused estimate, it is pure `edu.wpi.first.math` geometry with no vendor type and no IO
implementation anywhere in it. Grep its imports and you will not find a `TalonFX` or a `PhotonCamera`.
If one appears, the seam has leaked — a subsystem handed it a device handle instead of an observation.

That purity has a consequence the corpus repeatedly fails to collect: `RobotState` is the **most
unit-testable class on the robot** and almost the **least tested.** There is nothing to mock — feed it
a second of straight-line odometry, assert the pose integrated to one meter; feed it a tight vision
observation, assert the estimate pulled toward it. No HAL, no robot, no other subsystem. It is the
highest-leverage test most teams are not writing, and it falls straight out of building the seam at
all.

The state seam and the IO seam together give the robot a body and a sense of place. The third seam
decides what to do with them: [the coordination seam](05-the-coordination-seam.md).
