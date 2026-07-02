---
title: 15. The control path, end to end
weight: 15
---

*This is the deep dive Part I deferred and the map for everything that follows in Part II. A button press or an autonomous routine becomes a robot-wide goal, becomes per-subsystem setpoints, becomes an IO call, becomes a motor voltage — and measured state flows back up the same structure to a single world model. Trace that path once and the rest of Part II is detail.*

Part I argued for the shape of the architecture: three seams ([the architecture in five views](../part-1/02-five-views.md)) built foundation-first in a fixed order ([the foundation-first appendix](../appendices/how-we-developed-this/05-foundation-first.md)). It did not show how data actually moves through that shape during a 20 ms cycle. That is this chapter. We trace one full control path — from a teleop binding or an auto routine all the way down to a motor voltage, and the measured state all the way back up — and then walk several concrete scenarios that are each a specialization of the same loop.

The examples are abridged from the build spec; the point is the data flow, not a drop-in implementation.

Treat this chapter as the orienting map for Part II. Each later chapter zooms in on one stop along the path traced here: [hardware abstraction at the IO line](16-hardware-abstraction.md), the [motor interfaces](17-motor-interfaces.md) below it, the [subsystem archetypes](18-subsystem-archetypes.md) that sit on it and [the drivetrain](19-the-drivetrain-subsystem.md), [the world model](20-the-world-model.md) the path reads from and [the vision systems](21-vision-systems.md) that feed it, and the coordination layer that turns intent into setpoints ([state machines and the superstructure](22-coordination-state-machines.md), [state graphs and behavior trees](23-coordination-graphs-trees.md)).

---

## 15.1 The layered overview

Everything in the control path lives inside a small core: the IO seam, the state seam, and the coordination seam, plus a logging facade. Each advanced capability — vision fusion, pathfinding, replay, unit tests, a state graph — attaches to one of these seams as an addition, not a rewrite.

```d2
direction: down

FOUND: "FOUNDATION — the core control path" {
  OI: "Driver / Operator bindings
(RobotContainer)"
  SUP: "Superstructure coordinator
(goal in, setpoints out, guarded transitions)"
  SUBS: "Subsystems (logic only)" {
    DR: Drive
    EL: Elevator
    AR: Arm
    MAN: Manipulator
  }
  RS: "RobotState
(pose estimator + world model)"
  IOSEAM: "IO seam — one interface per subsystem" {
    IOI: "XxxIO interface + XxxIOInputs struct"
    REAL: "XxxIOReal (hardware)"
    SIM: "XxxIOSim (stub now, physics later)"
  }
  LOG: "Logging facade
(AdvantageKit or DogLog — swappable)"
}

FOUND.OI -> FOUND.SUP
FOUND.SUP -> FOUND.SUBS
FOUND.SUBS -> FOUND.IOSEAM.IOI
FOUND.IOSEAM.IOI -> FOUND.IOSEAM.REAL
FOUND.IOSEAM.IOI -> FOUND.IOSEAM.SIM
FOUND.SUBS -> FOUND.RS
FOUND.RS -> FOUND.SUP
FOUND.SUBS -> FOUND.LOG: "publish Inputs" { style.stroke-dash: 3 }
FOUND.RS -> FOUND.LOG: "publish pose" { style.stroke-dash: 3 }

ADD: "ADD-ONS — attach to seams later" {
  VIS: "Vision (VisionIO) → RobotState"
  PP: "PathPlanner / Choreo autos"
  PF: "On-the-fly pathfinding"
  REPLAY: "Log replay (AdvantageKit)"
  TESTS: "Unit tests vs XxxIOSim"
  GRAPH: "State-graph / motion planner"
}

ADD.VIS -> FOUND.RS: "writes vision measurements" { style.stroke-dash: 3 }
ADD.PP -> FOUND.SUP: "requests Superstructure goals" { style.stroke-dash: 3 }
ADD.PF -> FOUND.RS: "consumes RobotState pose" { style.stroke-dash: 3 }
ADD.REPLAY -> FOUND.IOSEAM.IOI: "feeds logged Inputs" { style.stroke-dash: 3 }
ADD.TESTS -> FOUND.IOSEAM.SIM: "construct subsystem w/ Sim" { style.stroke-dash: 3 }
ADD.GRAPH -> FOUND.SUP: "replaces transition fn" { style.stroke-dash: 3 }
```

Read the solid arrows top to bottom and that is the command path: bindings call the Superstructure, the Superstructure sets goals on subsystems, subsystems call their IO, IO drives hardware. Read the arrows that feed `RobotState` and the logging facade and that is the data path coming back up. The dotted add-ons all hang off one of the three seams; none of them reach into a subsystem to do their job.

The signature of the foundation, on disk, is a four-file quartet per mechanism — `XxxIO`, `XxxIOInputs`, an `XxxIO<impl>`, and `XxxIOSim`. If a new team member can find those four files for any mechanism, the architecture is intact. (Naming note from the corpus: the hardware impl is named by device — `ElevatorIOTalonFX`, `GyroIOPigeon2`, `VisionIOLimelight` — not literally `IOReal`. [Chapter 16](16-hardware-abstraction.md) covers that line in depth.)

---

## 15.2 Run mode: REAL, SIM, REPLAY, and the single selection point

The same code runs in three modes. The only thing that changes between them is which IO implementation is constructed, and that choice happens in exactly one place — the robot constructor, keyed off the run mode.

```d2
direction: right
START: "Robot constructor"
MODE: "Run mode?" { shape: diamond }
R: "new ElevatorIOReal()
new VisionIOPhoton()"
S: "new ElevatorIOSim()
new VisionIOSim()"
Z: "new ElevatorIO() {}
(no-op; inputs come from log)"
BUILD: "construct subsystems"
START -> MODE
MODE -> R: REAL
MODE -> S: SIM
MODE -> Z: REPLAY
R -> BUILD
S -> BUILD
Z -> BUILD
```

Three things follow from this one selection point.

- **REAL** constructs hardware implementations. `updateInputs` reads real sensors; `setVoltage`/`setSetpoint` commands real motors.
- **SIM** constructs simulation implementations. The same subsystem logic runs against a physics model instead of hardware; nothing above the IO line knows the difference.
- **REPLAY** constructs an empty no-op implementation — `new ElevatorIO() {}` — that does nothing and reads nothing. In replay the inputs struct is overwritten from a recorded log before the subsystem ever sees it, so the no-op has nothing to do. You write this empty body on day one. It costs nothing and it is the entire reason replay later requires zero new subsystem code.

Because the rest of the codebase only ever holds an `XxxIO` reference, the subsystems, commands, and Superstructure are written once and run unmodified in all three modes. The fork is one `switch`, not a parallel code path. That single selection point is what makes scenario §15.6.D (replay) free later in this chapter.

---

## 15.3 The 20 ms runtime loop: read → log → decide → actuate

This is the heartbeat. Every scenario later in the chapter is a specialization of it. The `CommandScheduler` runs each subsystem's `periodic()` every cycle, and within a cycle the order is fixed.

```d2
shape: sequence_diagram
Sched: CommandScheduler
Sub: Subsystem
IO: XxxIO impl
HW: Hardware / Sim
Log: Logging facade
RS: RobotState
Sup: Superstructure

Sched -> Sub: periodic()
Sub -> IO: updateInputs(inputs)
IO -> HW: read sensors
HW -> IO: raw values
IO -> Sub: inputs filled
Sub -> Log: publish Xxx/Inputs
Sub."in REPLAY, log OVERWRITES inputs here"
Sub -> RS: contribute odometry / mechanism state
Sched -> Sup: (command) requested goal
Sup -> RS: read pose / state
Sup -> Sub: setGoal(...) → setpoint
Sub -> IO: setVoltage / setSetpoint
IO -> HW: actuate
```

The invariant is **read → log → decide → actuate**, in that order, every cycle.

1. **Read.** `updateInputs(inputs)` fills a mutable `XxxIOInputs` struct with everything coming back from the device — position, velocity, applied volts, current, temperature. One call, one struct, all the hardware readings in one place.
2. **Log.** The filled struct is published immediately, before any decision uses it. Logging right after reading is what makes the log a faithful record of exactly what the code saw — which is the precondition for deterministic replay. In REPLAY mode this is also the moment the recorded log overwrites the struct, so downstream code runs against the historical inputs.
3. **Decide.** Subsystems contribute their state to `RobotState` (drive contributes odometry); the Superstructure reads pose and state and turns the active goal into per-subsystem setpoints.
4. **Actuate.** Each subsystem pushes its setpoint down to its IO via `setVoltage` or `setSetpoint`, and the IO commands hardware.

The struct at the center of step 1 is the artifact both logging stacks consume:

```java
class XxxIOInputs {
    double positionMeters;
    double velocityMps;
    double appliedVolts;
    double currentAmps;
    double tempC;
}
```

Building the inputs-struct style (the interface fills this object each cycle via `updateInputs`) rather than plain getters is the one decision that keeps logging and replay available later. It is a few lines of boilerplate per subsystem — annotate the struct `@AutoLog` for AdvantageKit, or hand-log its fields for DogLog — and it is why the log/replay choice can be deferred. [Chapter 17](17-motor-interfaces.md) goes further into what the IO contract carries beyond `updateInputs`/`setVoltage` (brake mode, current limits, characterization).

### Where the loop lives: above or below the line

A second per-subsystem decision shapes the actuate step: the PID and feedforward can sit above the IO interface (the interface takes `setVoltage(volts)` and the subsystem owns one controller that Sim and Real share) or below it (the interface takes `setSetpoint(inches)` and each implementation runs its own loop, typically on-motor firmware). Keep the loop above the line for anything you simulate; push it below only to deliberately exploit firmware control such as Phoenix 6 MotionMagic — [chapter 16](16-hardware-abstraction.md) gives the full side-by-side comparison, and [chapter 18](18-subsystem-archetypes.md) maps which archetypes lean which way.

---

## 15.4 The state seam the path reads from

The decide step above reads pose from `RobotState`, a single object that owns the robot's best estimate of the world behind a pose estimator. Subsystems feed it odometry; later, vision feeds it corrections; decisions and pathing read from it.

```java
public class RobotState {
    private final SwerveDrivePoseEstimator estimator;     // foundation
    // later: TimeInterpolatableBuffer<Pose2d> history;   // world-model seam
    public void addOdometry(SwerveModulePosition[] p, Rotation2d g, double t) {...}
    public void addVisionMeasurement(Pose2d p, double t, Matrix<N3,N1> stdDevs) {...}
    public Pose2d getPose() {...}
}
```

On day one only `addOdometry` and `getPose` are exercised. `addVisionMeasurement` exists but is uncalled — it is the vision seam, pre-cut. Centralizing the estimate here, rather than letting the drive subsystem privately own it, is what lets vision, pathfinding, and auto all share one consistent world model. [Chapters 20](20-the-world-model.md) [and 21](21-vision-systems.md) develop this seam in full.

## 15.5 The coordination seam the path passes through

The decide step's "turn a goal into setpoints" happens in the `Superstructure`. It takes one robot-wide goal and fans it out to subsystems through a single transition function that may reject or reorder a transition for safety.

```java
public class Superstructure extends SubsystemBase {   // SubsystemBase: schedulable, owns run/runOnce
    public enum Goal { STOW, INTAKE, SCORE_L4, CLIMB }
    public Command requestGoal(Goal g) { return applyGoal(g); }
    private Command applyGoal(Goal g) {       // <-- the seam. interlocks live here.
        return switch (g) {
            case SCORE_L4 -> Commands.sequence(       // sequenced, each step guarded —
                arm.setGoalCommand(CLEAR),            // three plain setGoal() calls would
                Commands.waitUntil(arm::atGoal),      // all land in the same cycle and
                elevator.setGoalCommand(L4),          // the last would overwrite the first
                Commands.waitUntil(elevator::atGoal),
                arm.setGoalCommand(SCORE));
            // ...
        };
    }
}
```

(`CLEAR`, `L4`, `SCORE` — like `setModuleStates` in the scenarios below — are schematic names, not a real API.)

The seam is that **all transitions pass through one function**. The foundation version is a `switch` over a goal enum; later its body can be replaced with a guarded transition table, a motion planner, or a graph search without changing a single caller. The two coordination chapters cover that progression: [chapter 22](22-coordination-state-machines.md) for the state-machine form, [chapter 23](23-coordination-graphs-trees.md) for graphs and trees.

---

## 15.6 Scenarios — walking the data flow

The loop above is the general case. Here are concrete control paths through it.

### 15.6.A Vision → pose → path: how the robot makes a path from what it sees

*Goal: see the field, decide where to score, drive there.* This flow touches all three seams in sequence: **VisionIO → RobotState → Superstructure → pathfinder → DriveIO.**

```d2
shape: sequence_diagram
Cam: "Coprocessor (PhotonVision/Limelight)"
VIO: VisionIO impl
RS: RobotState
Sup: Superstructure
PF: "Pathfinder (PathPlanner/Choreo)"
Drive: Drive subsystem
DIO: DriveIO

Cam -> VIO: AprilTag observation (pose + tags + latency)
VIO -> RS: addVisionMeasurement(pose, t, stdDevs)
RS."fuse with odometry (reject if stdDev/ambiguity high)"
Sup -> RS: getPose() (where am I?)
Sup -> Sup: pick target = nearest legal scoring pose
Sup -> PF: generate path(currentPose → targetPose)
PF -> Drive: trajectory / chassis speeds
"until at target": {
  Drive -> RS: getPose() (closed-loop on fused pose)
  Drive -> DIO: setModuleStates(...)
}
Drive -> Sup: at target
Sup -> Sup: applyGoal(SCORE_L4)
```

The camera writes a measurement to `RobotState`; everything downstream reads pose from the one fused estimate. **Vision never talks to drive.** Swapping PhotonVision for Limelight is a new `VisionIO` impl. Swapping PathPlanner for Choreo, or adding on-the-fly pathfinding, changes only the pathfinder participant. The seams localize every change. This is the same `getPose()` from §15.4 and the same `applyGoal` from §15.5 — the scenario just chains them.

### 15.6.B The interlock: refusing an illegal physical state

*Constraint: the manipulator/scoop must not be open while the elevator is raised (they collide).* This lives in exactly one place — the Superstructure's guarded transition — never scattered across subsystems.

```d2
direction: down
REQ: "requestGoal(SCORE_L4)"
GUARD: "Guard: is scoop open AND elevator low?" { shape: diamond }
RAISE: "elevator.setGoal(L4)"
SEQ: "sequence the safe order"
S1: "1. manipulator.setGoal(CLOSED)"
S2: "2. waitUntil(manipulator.isClosed)"
S3: "3. elevator.setGoal(L4)"
S4: "4. manipulator.setGoal(SCORE)"
DONE: "goal active"
REQ -> GUARD
GUARD -> RAISE: safe to raise
GUARD -> SEQ: unsafe
SEQ -> S1
S1 -> S2
S2 -> S3
S3 -> S4
RAISE -> DONE
S4 -> DONE
```

In the foundation, `applyGoal` hand-sequences the safe order with `Commands.sequence(...)` and `waitUntil(...)`, where each subsystem exposes a cheap predicate (`isClosed()`, `isStowed()`) read from its inputs struct. Later, a declarative transition table or a motion planner that knows mechanism geometry can compute the safe interpolation automatically — and because every transition already routes through `applyGoal`, you replace the body, not the callers.

The subsystems stay dumb: they execute setpoints and report state. The knowledge that two states are mutually exclusive lives in the coordinator, the only object that sees all mechanisms at once. [Chapter 22](22-coordination-state-machines.md) develops the guard from a `switch` into a real transition function.

### 15.6.C Operator intent vs execution

*An operator presses "score L4."* This shows why intent is separated from execution.

```d2
shape: sequence_diagram
Op: Operator
RC: RobotContainer
Sup: Superstructure
El: Elevator
Man: Manipulator
Op -> RC: button L4
RC -> Sup: requestGoal(SCORE_L4)
Sup -> Sup: applyGoal — runs interlock (§15.6.B)
Sup -> El: setGoal(L4)
Sup -> Man: setGoal(SCORE) (after guard clears)
Man."each subsystem closes its own loop to its setpoint via its IO"
```

The operator expresses *intent* (a goal). The Superstructure owns *execution* (the legal, sequenced setpoints). The operator binding never commands a motor, so re-tuning the scoring sequence is a one-place change — and the same `SCORE_L4` goal is reusable as an autonomous action (it is the final `applyGoal(SCORE_L4)` step in scenario 15.6.A). One goal, two callers, identical execution.

### 15.6.D Replay a match to find the bug

*The robot mis-scored in qualifier 42; reproduce it at your desk.* This scenario requires zero code written for the purpose. It is the dividend of the inputs-struct IO seam (§15.3) plus the REPLAY run mode (§15.2).

```d2
shape: sequence_diagram
Log: Match WPILOG
Robot: Your code (unchanged)
IO: XxxIO (REPLAY no-op)
AS: AdvantageScope
Log -> Robot: launch in REPLAY mode, feed log
"every logged cycle": {
  Log -> IO: overwrite Inputs with logged values
  Robot -> Robot: run real decision code on logged inputs
  Robot -> AS: emit NEW computed outputs alongside originals
}
Robot."step through, add fields, see exactly what the superstructure decided and why"
```

Recall the loop's order: read → log → decide → actuate. Replay intercepts at the log step. Instead of reading hardware, the recorded log overwrites the inputs struct, and then the actual decision code runs against the actual sensor inputs from the match, deterministically. You can add new logged fields to inspect decisions that were not logged live — see exactly what the Superstructure decided and why. The only prerequisites are that the foundation logged the inputs struct and wired a REPLAY mode, both of which §15.2 and §15.3 already did. Nothing in the subsystems changes; the no-op IO simply has nothing to do because the inputs arrive from the log.

This is why teams that build the seam and never collect replay are leaving the dividend on the table. The afternoon of work that fills `XxxIOSim` for simulation also unlocks unit tests (point a test at the sim) and replay (flip the mode). The foundation already paid for all three.

---

## 15.7 The path, in one breath

A binding or auto routine requests a `Goal`. The Superstructure's `applyGoal` reads `RobotState`, runs any interlock, and sets per-subsystem setpoints. Each subsystem, every 20 ms, reads its IO inputs, logs them, decides against the active setpoint, and actuates through its IO down to a motor voltage. Measured state flows back up: IO inputs into the subsystem, odometry and corrections into `RobotState`, pose back into the Superstructure for the next decision. Vision feeds the state seam without touching drive; replay feeds the IO seam without touching subsystems; coordination changes the Superstructure body without touching callers.

Everything in Part II is a closer look at one stop on that path. The next chapter starts at the bottom — the IO line itself, and what it means to keep vendor types below it: [chapter 16, hardware abstraction and the IO line](16-hardware-abstraction.md).
