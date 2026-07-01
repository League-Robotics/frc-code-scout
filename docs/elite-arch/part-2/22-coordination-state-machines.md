---
title: 22. Coordination I — state machines and the superstructure
weight: 22
---

*Part I's chapter on [the coordination seam](../part-1/05-the-coordination-seam.md) named six paradigms and deferred their construction. This chapter builds the common ones: the superstructure as the single object that turns one robot-wide goal into a coordinated set of guarded subsystem setpoints, and the two finite-state-machine shapes the corpus uses to do it. The far end of the spectrum — transitions as data, searched as a graph or walked as a behavior tree — is the [next chapter](23-coordination-graphs-trees.md).*

Code is quoted to study the technique, not to copy. Build the contract for your robot.

This chapter is the deep dive [chapter 7](../part-1/05-the-coordination-seam.md) pointed to. Part I argued why a coordination seam exists and where it sits relative to the [control path](15-control-path.md), the [subsystem archetypes](18-subsystem-archetypes.md), and the [world model](20-the-world-model.md). It will not re-argue that here. What follows is the engineering: the I/O boundary the seam presents, the three implementations the corpus actually ships, the maturity ladder they fall on, where kinematic interlocks live, and how you test the safe ordering without a robot.

---

## 1. The seam, stated as a boundary

The superstructure turns one robot-wide goal into a coordinated set of subsystem setpoints, through a single transition function that is allowed to reorder or reject a transition for safety. A button asks for `SCORE_L4`; the superstructure decides the legal sequence — clear the frame, raise the elevator, then score — that realizes it. It is the one object that sees every mechanism at once, so the knowledge that "the arm must clear before the elevator rises" lives in exactly one place instead of scattered across subsystems.

Like [RobotState](20-the-world-model.md), the superstructure is a "subsystem" with no hardware. Its I/O is goals in, subsystem setpoints out:

```
Operator/Auto → requestGoal(Goal) → [ one guarded transition function ] → subsystem.setState(...) ×N
                                          reads RobotState for safety/sequencing
```

The split is intent vs execution: a caller expresses *what it wants* (a goal) and walks away; the superstructure owns *how each mechanism gets there* (the legal, sequenced setpoints). Callers cannot drive a mechanism into an illegal configuration because only the transition function writes setpoints. There is no control loop here — each subsystem still closes its own loop behind its [IO line](16-hardware-abstraction.md) and its [motor interface](17-motor-interfaces.md). The superstructure only decides which setpoint each subsystem should have right now.

```d2
direction: right
start: "" { shape: circle }
STOW
INTAKE
SCORE_L4: "SCORE_L4
(guarded: arm clears frame
before elevator raises)"
start -> STOW
STOW -> INTAKE: request INTAKE
INTAKE -> STOW: has piece
STOW -> SCORE_L4: request SCORE_L4
SCORE_L4 -> STOW: scored
```

### 1.1 The contract

| Method | Direction | Why |
|---|---|---|
| `requestGoal(Goal)` / `setStateCommand(State)` | in | a caller asks for one robot-wide state; returns a `Command` |
| the transition function (`applyGoal` / `updateSubsystemStates` / `continueTransition`) | internal | the seam — fans the goal out to subsystem setpoints, with guards |
| `getState()` / `atGoal()` | out | what the robot is doing now (read by auto, LEDs, RobotState) |

What it omits is as load-bearing as what it has. No `TalonFX`, no `*IO` interface, no `XxxIOSim` / `XxxIOReal`. It holds the *subsystems* — their public `setState` / `setGoal` API — not their hardware. No motor math, no vendor SDK. Pure command and decision logic. A vendor type appearing here means a subsystem has leaked its hardware upward, and the corpus exemplars in this chapter are clean: 3128 and 3476 import zero vendor types.

---

## 2. How wide a paradigm this is

This is the richest point of architectural divergence in FRC, and the survey of 37 teams quantifies it. A class named `Superstructure` appears in 22 teams; a generic `*StateMachine` in 12. Across all three sweeps the survey identified six coordination paradigms, with an orthogonal centralized-vs-distributed axis layered on top:

| Paradigm | Exemplars | Best at |
|---|---|---|
| Command composition | 254, 1155, 3061, 190 | resource arbitration; composing reusable command objects |
| Wanted/current FSM (distributed) | 2910, 33, 4099, 4504 | localizing each mechanism's intent-vs-execution split |
| Centralized `RobotManager` FSM | 581, 3128 | reasoning about whole-robot states in one place |
| State graph (search over states) | 6328, 254 | complex transition logic; pathfinding through legal states |
| Behavior tree | 3015 | deeply nested, reactive decision logic borrowed from game AI |
| Message passing (inter-process) | 971 | process isolation; language-agnostic contracts |

The first three rows, plus the boundary of the fourth, are this chapter. The state graph and behavior tree are [chapter 23](23-coordination-graphs-trees.md). The survey's framing matters for how you read the rest: these are not competitors to choose among once. They are rungs and forks. A program grows from command composition, to a distributed or centralized FSM, to a state graph or behavior tree when transitions outgrow a switch statement.

---

## 3. Centralized FSM — one goal fans out to dumb subsystems

The first shape the corpus uses is a single object holding the whole robot's state machine, driving subsystems that deliberately expose only state setters. The survey calls this the 581/3128 pattern: "a single `RobotManager` holds the entire robot's state machine and drives a set of deliberately 'dumb' subsystems that only expose setters. Mechanism behavior lives in one place; subsystems own no decision logic." It is a genuine architectural fork from the distributed FSM — the centralized version "makes whole-robot states trivial to reason about but concentrates all complexity in one file."

The goal is an enum where each robot state bundles a target state for every subsystem. 3128's `RobotManager` extends an FSM base and fans one `RobotStates` value out:

```java
// 3128 Aluminum Narwhals — subsystems/Robot/RobotManager.java
public class RobotManager extends FSMSubsystemBase<RobotStates> {
  private static Elevator elevator; private static Manipulator manipulator;
  private static Intake intake;     private static Climber climber;  private static Swerve swerve;

  // THE SEAM: one robot goal -> a sequenced, guarded fan-out to each subsystem
  public Command updateSubsystemStates(RobotStates nextState) {
    return sequence(
      elevator.setStateCommand(nextState.getElevatorState())
              .unless(() -> nextState.getElevatorState() == ElevatorStates.UNDEFINED),
      manipulator.setStateCommand(nextState.getManipulatorState()).unless(/* ... */),
      intake.setStateCommand(nextState.getIntakeState()).unless(/* ... */),
      climber.setStateCommand(nextState.getClimberState()).unless(/* ... */),
      waitUntil(() -> climber.winch.atSetpoint())                    // ◀ a guarded transition
              .unless(() -> nextState.getClimberState() == ClimberStates.UNDEFINED));
  }
}
```

Every transition routes through `updateSubsystemStates`. Three details carry the technique:

- **One enum per subsystem, bundled by the robot state.** `nextState.getElevatorState()`, `getManipulatorState()`, and so on each return that subsystem's target. The robot-wide goal is a tuple of per-subsystem goals, and the fan-out is mechanical: read the target for each subsystem, command it.
- **`UNDEFINED` means "leave this one alone."** The `.unless(...)` guards skip any subsystem whose bundled target is `UNDEFINED`, so a robot state can move some mechanisms and leave the rest untouched. This is how one transition function serves many goals without a combinatorial mess of full-robot poses.
- **The `waitUntil(...)` is the interlock seam.** Sequencing the climber winch to reach its setpoint before the transition completes is the guarded transition: the safe order is expressed here, once, and the subsystems stay dumb.

The imports are exactly what the contract predicts — WPILib commands, the team's own subsystems and `common` FSM library, and not one vendor type. The decision logic and the hardware never meet.

One caveat the corpus build-spec flags: 3128 reaches its subsystems through static fields rather than constructor injection. That works on the robot but makes the seam harder to test in isolation, because a test cannot hand it sim-backed subsystems. Section 6 returns to why injection matters for the interlock test.

---

## 4. Superstructure-as-`SubsystemBase` — the transition runs over time

The second shape makes the superstructure a real `SubsystemBase` that holds the mechanisms plus a state machine, accepts a target state, and advances the transition each cycle in `periodic()`. This is the 3476 style, and the survey places 3476 with 254 and 6328 at the level that "separates intent from execution and handles kinematic safety," distinct from the centralized-FSM fork:

```java
// 3476 Code Orange — superstructure/Superstructure.java
public class Superstructure extends SubsystemBase {
  private Elevator elevator; private EndEffector endEffector;
  private SuperstructureStateMachine stateMachine;

  @Override public void periodic() {
    stateMachine.continueTransition();                        // advance the guarded transition
    RobotState.setSuperstructureState(getCurrentState());     // publish intent to the world model
    Logger.recordOutput("Superstructure/TargetState", stateMachine.getTargetState());
  }
  public Command setStateCommand(SuperstructureState state, String name) {
    return new InstantCommand(() -> stateMachine.setTargetState(state)).withName(name);
  }
}
```

The difference from the centralized FSM is the time axis. A goal request here is just "set the target state" — an `InstantCommand` that flips one field and returns. The work happens in `continueTransition()`, called every cycle, walking the legal path toward the target one step at a time. Where 3128's `sequence(...)` builds the whole ordered transition as a command up front, 3476's `continueTransition()` is a tick function: each `periodic()` it looks at where the robot is, where it should be, and takes the next safe step.

Two things this buys, both visible in the four lines of `periodic()`:

- **Intent is published to the world model.** `RobotState.setSuperstructureState(getCurrentState())` writes what the superstructure is doing into [RobotState](20-the-world-model.md), so auto routines, LEDs, and dashboards read the robot's coordination state from one place rather than poking the superstructure directly. The seam announces its execution; the rest of the robot subscribes.
- **The target is logged separately from the current.** `Logger.recordOutput("Superstructure/TargetState", ...)` records intent next to execution, which is exactly what you want when a transition stalls and you are trying to see whether the goal was wrong or the path to it was blocked.

The survey also notes 3476's refinement: they "expose superstructure states as autonomous actions (`SetSuperstructureState`, `WaitForSuperstructureState`)," which marries 254's action-based autonomous to the request-based superstructure. The auto routine asks for a state and waits for it; it never sequences the mechanisms itself.

Because 3476 takes its subsystems by constructor, a test can build the whole superstructure on sim-backed mechanisms — the property 3128's static fields give up.

---

## 5. The wanted/current two-enum pattern

Underneath both shapes is a single idea, stated most plainly by 2910: hold two states per mechanism, the one requested and the one actually in effect, with a transition function as the only thing allowed to move between them. The survey calls 2910 "the reference implementation of the wanted/current state-machine pattern," and notes the reversal worth marking — 2910 is the team most cited for running finite-state machines instead of the command scheduler, but their 2025 code is a hybrid. Subsystems do extend `SubsystemBase` and use an IO layer (`ShoulderIO` / `ShoulderIOTalonFX`); behavior is driven by explicit state machines rather than scheduled commands. "FSM vs command-based" is a false binary; the strongest version uses command-based for resource arbitration and an FSM for decision logic.

The pattern, stated precisely, is two enums and one function:

```java
// 2910 — every subsystem and the superstructure follow this shape
enum WantedState  { IDLE, HOME, INTAKE, SCORE_L4, ... }   // requested
enum SystemState  { IDLING, HOMING_WRIST, ... }           // actual

private SystemState handleStateTransitions() {
    switch (wantedState) {
        case HOME: ... return SystemState.HOMING_SHOULDER;
        ...
    }
}

// each periodic(): currentState = handleStateTransitions(); applyStates();
```

A caller sets `wantedState` and walks away. It never knows what sequence of physical steps the subsystem must run to honor the request, and it cannot put the mechanism into an illegal configuration because only `handleStateTransitions()` writes `SystemState`. The superstructure does the same at the next level up — its wanted state is a robot-wide goal, its current state is what it has actually achieved, and the same transition function mediates between them.

This is the in-process equivalent of 971's `Goal` / `Status` message split, achieved with two enums inside one process. The distributed form (2910, 33, 4099, 4504) localizes each mechanism's intent-vs-execution split — one wanted/current machine per subsystem, plus one on top. The centralized form (581, 3128) collapses the per-subsystem machines into a single `RobotManager`. Same intent-vs-execution principle; opposite choices about where the machines live.

Two notes on where this pattern shows up in other languages, both from the survey: 4504's Python MagicBot provides the wanted/current machinery as a framework feature — "a dumb `launcher.py` (just hardware and setters) and a `launcherController.py` subclassing MagicBot's `StateMachine` with `@state`-decorated methods and `next_state()` transitions" — the same pattern with the switch statements provided by the framework. And 4099 reaches it in Kotlin as a "request-based superstructure," reinforcing that the design is language-independent.

---

## 6. The D2 ladder

These implementations are not interchangeable; they are rungs on the rubric's coordination dimension. Reading the corpus build-spec and survey together, the coordination axis (rubric D2) has four levels:

| Level | Shape | Team |
|---|---|---|
| 1 | command composition — sequential/parallel groups; no coordinator | most teams |
| 2 | wanted/current FSM, distributed (one per subsystem + a top one) | 2910, 4099 |
| 2 | centralized `RobotManager` — one FSM, dumb subsystems | 581, 3128 |
| 3 | `Superstructure` coordinator that separates intent from execution + handles kinematic safety | 254, 3476, 6328 |
| 4 | state graph — transitions are data; pathfind through legal states (JGraphT / A*) | 6328, 254 |

The progression is a sequence of refactors a team performs when the previous rung breaks down, each motivated by a problem just felt:

- **Level 1 → 2.** Command composition works until two callers want conflicting things or a caller can sequence mechanisms into an illegal pose. The fix is an FSM: callers request intent, a transition function owns execution. The wanted/current two-enum machine of §5 is the right *first* state machine — it teaches the core idea without graph-search machinery.
- **Level 2 → 3.** Distributed or centralized FSMs handle each mechanism, but kinematic safety — two mechanisms that share space and can collide — needs an object that sees both. A `Superstructure` coordinator separates "which pose we want" from "the safe path to get there," and owns the interlocks.
- **Level 3 → 4.** When transitions get complex enough that the legal sequence between two states is itself a search problem, the transition logic becomes data: a graph of states with commands on the edges, walked by a path search. That is the optimization for when a switch statement stops scaling — and the subject of the [next chapter](23-coordination-graphs-trees.md).

The two level-2 rows are the centralized/distributed fork, not a quality difference. Both are intent-vs-execution machines; they differ in where the machines live.

---

## 7. Where the interlocks live, and how you test them

The defining job of a level-3 superstructure is kinematic safety: ensuring two mechanisms that can collide never do. The architectural rule is that this knowledge lives in the *one* transition function, as guards and sequencing — not scattered across subsystems. 3128's `waitUntil(() -> climber.winch.atSetpoint())` is one such guard. The general form is "the arm must clear the frame before the elevator rises," expressed as ordering inside the seam.

(Some teams pull the geometry out further still — 1678's dedicated `MotionPlanner` owns collision-free arm/elevator motion as its own layer, with a tellingly-named `UnsafePivotAndElevatorSynchronousToPositionMotionMagic` command coordinating the two axes so they arrive together. That separation of "where we want to be" from "what path through space is safe" is [chapter 23](23-coordination-graphs-trees.md) territory; here the interlock lives directly in the transition function.)

Interlocks are exactly what you want to test, and the superstructure is the one place they live, so it is the one place to test them. Because the subsystems below it run on their `*IOSim` implementations, you construct the whole thing in sim, request a dangerous goal, and assert the *order*:

```java
// construct subsystems on Sim, build the superstructure, request a dangerous goal:
var sup = new Superstructure(Elevator.create(), Arm.create() /* both Sim in a test */);
run(sup.requestGoal(SCORE_L4));
fastForward();
// assert the guard held: the arm cleared the frame BEFORE the elevator passed the danger zone
assertTrue(armClearedBeforeElevatorRose);   // the interlock, verified without a robot
```

This is the test that catches the failure mode that breaks robots — two mechanisms colliding — and it costs nothing once the subsystems have sim implementations. It also explains why §3 flagged 3128's static fields and §4 noted 3476's constructor injection: the test above only works if you can hand the superstructure sim-backed subsystems. A superstructure that reaches its mechanisms through `getInstance()` cannot be constructed against sim in a test. Take subsystems by constructor (3476, and 5190 below) rather than `getInstance()` (3128), and the interlock test is available; skip injection, and it is not.

The survey backs the payoff: SciBorgs (1155) run 14 JUnit suites that build sim-backed subsystems and run real commands to completion, and Ranger Robotics (3015) ship 37 test files. The interlock test is one instance of the IO layer's deferred dividend — verification on CI before the code reaches a robot.

---

## 8. The anti-pattern: a level-1 class wearing a level-3 name

A class named `Superstructure` is not a coordinator if it just holds references and exposes manual jogs. The build-spec calls this "level-1 wearing a level-3 name," and 5190 is the example of what not to ship:

```java
// 5190 Green Hope Falcons — Superstructure.java (what NOT to ship)
public class Superstructure {
  public final Pivot pivot_;  public final EndEffector end_effector_;
  public Command jogPivot(double percent) { /* StartEndCommand setPercent */ }   // no goal, no transition
}
```

There is no goal enum, no transition function, no interlock — it is a bag of subsystems with jog buttons. The name promises a coordination seam; the body delivers a holder. This matters for scoring: D2 is scored on what the class *does*, not what it is *named*. Before crediting a superstructure with level-3 coordination, confirm three things by opening the file:

- **An actual goal-request API** — a goal/state enum and a `requestGoal` / `setStateCommand` method, not just per-subsystem jog buttons.
- **A single transition function** that all transitions route through, fanning the goal out to subsystem setpoints.
- **Kinematic interlocks living here**, as guards or sequencing, not pushed down into subsystems.

5190 has the public-field holder and the jog, and none of the three. It is a level-1 command-composition setup with a level-3 name — exactly the case the rubric tells you to catch by reading the code rather than grepping for the class name.

---

## 9. Vendor and IO discipline at the seam

The coordination seam is, like RobotState, naturally vendor-free, and a leak here is a loud signal that a subsystem's abstraction is broken. The rule:

> The superstructure imports subsystems, not their hardware. No `com.ctre` / `com.revrobotics` / `org.photonvision`, no `ElevatorIOTalonFX`, no `ElevatorIO`. If a vendor type or an IO impl appears here, a subsystem has leaked its hardware upward — the fix is to expose a `setGoal(...)` / `setState(...)` on the subsystem and call that.

The corpus exemplars above are clean: 3128 and 3476 import zero vendor types. The superstructure depends only on WPILib commands, the subsystems' public API, and [RobotState](20-the-world-model.md). Its one coupling is to the mechanisms it coordinates — which is correct; that is its whole job. The discipline is identical to the one drawn at the [IO line](16-hardware-abstraction.md) and the [motor interface](17-motor-interfaces.md): a vendor type belongs below the IO line, and the coordination seam sits well above it. The seam imports the *public state API* of each subsystem — `setState`, `setGoal`, `getState` — and never an IO implementation.

### Checklist — is your coordination seam intact?

- [ ] A goal/state enum and a `requestGoal` / `setStateCommand` API — not just per-subsystem jog buttons.
- [ ] **One** transition function fans the goal out to subsystem setpoints; all transitions route through it.
- [ ] Kinematic interlocks (mechanism-collision safety) live **here**, as guards/sequencing — not in subsystems.
- [ ] It holds subsystems (their `setState` API), **no `*IO` impl and no vendor type**.
- [ ] Subsystems are injected by constructor so a test can pass sim-backed ones.
- [ ] A test requests a dangerous goal and asserts the safe ordering held (the interlock).
- [ ] Intent is logged and written to [RobotState](20-the-world-model.md) so auto, LEDs, and dashboards can read it.

---

## 10. Where this sits

The three implementations here — centralized FSM (§3), superstructure-as-`SubsystemBase` (§4), and the wanted/current two-enum machine (§5) — are the common rungs of the D2 ladder, levels 2 and 3. They share one principle: one robot-wide goal in, guarded subsystem setpoints out, through a single transition function, with intent separated from execution. They differ in where the machines live (centralized vs distributed) and whether the transition is built up front as a command or advanced each cycle as a tick function.

The far end of the ladder — level 4, where transitions become data and the legal path between two states is found by search — is a different enough technique to warrant its own chapter. The state graph (6328's JGraphT, 254's A\*) and the behavior tree (3015's leaf/decorator/blackboard runtime) are coordination for when a switch statement stops scaling.

Continue to the next chapter: [23. Coordination II — state graphs and behavior trees](23-coordination-graphs-trees.md).
