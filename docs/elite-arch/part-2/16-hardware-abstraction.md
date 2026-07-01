---
title: 16. Hardware abstraction and the IO line
weight: 16
---

*Part I argued that a subsystem should depend on a contract, not on a motor. This chapter shows the mechanics: the IO layer is the Strategy pattern, "IO layer" and "hardware abstraction" name two different axes, and a single diagnostic — which side of the line the control loop is on — classifies any interface you find. Code is quoted to study the technique, not to copy.*

Part I, [chapter 5](../part-1/03-the-io-seam.md), motivated the IO seam and then deferred the implementation. This is that deferred deep dive. The case for the seam is made; here we open the files and show how the boundary is actually built, what every implementation in the corpus shares, and the choices that distinguish one team's IO layer from another's.

The IO seam appears in some form in 24 of the corpus teams — the single most widely shared architectural idea in serious FRC code, and the default rather than the exception among the strong programs. That convergence is the subject of the rest of this chapter: not whether to draw the line, but where it sits and what crosses it.

## The pattern has an older name

"IO layer" is FRC's house name. The pattern is Strategy.

Strategy, in the Gang of Four sense, defines a family of interchangeable implementations behind one interface and lets the caller select which one is in force — and lets that implementation vary independently of both the interface and the code that uses it. That is an IO layer exactly. `ElevatorIO` is the strategy interface; `RealElevator`, `SimElevator`, and `NoElevator` are interchangeable strategies; the subsystem holds a reference to one without knowing which.

The reason to reach for Strategy is that the implementation can change over time without any change to the interface or to the code that depends on it. A team writes the subsystem's logic once against `ElevatorIO`, then swaps the strategy underneath: real hardware during a match, a physics model on a laptop, a log-replay stub after the match, a different motor vendor next season. None of those swaps touches the interface, and none touches the subsystem. Teach it as Strategy first and "IO layer" second — the FRC name describes where the pattern sits, the GoF name describes what it is.

Two neighboring patterns are worth naming so they stay distinct:

- **Factory Method** is the selection step. SciBorgs' `Elevator.create()` and `Elevator.none()` are factory methods that choose which strategy to instantiate. The factory picks the strategy; the strategy does the work.
- **Null Object** is the do-nothing strategy. `NoElevator` is a full member of the strategy family whose methods are deliberately empty, so a subsystem with disconnected hardware runs as a safe no-op instead of crashing. It is a strategy, not an absence of one.

### Strategy vs. Bridge

A true hardware abstraction layer — "any motor accepts a voltage, regardless of vendor" — is structurally similar to the IO layer but is better described as **Bridge**. Bridge splits an abstraction (motor) from its implementation (TalonFX driver) so the two evolve separately: a design-time structural concern.

Strategy and Bridge look almost identical in code. GoF distinguishes them by intent:

| | Strategy | Bridge |
|---|---|---|
| What it swaps | Behavior, at runtime | Implementation, decided once |
| When the choice happens | Every deploy (real vs. sim vs. replay) | At design time (device independence) |
| The IO layer | Leans this way | Less so |

The IO layer leans Strategy because the swap is a runtime choice made on every deploy. The distinction matters for the section after next, where the line between the two blurs in real code.

## The two axes that get tangled

There is a persistent ambiguity in FRC about whether the IO layer *is* a hardware abstraction layer. Resolving it changes how you read every interface in the corpus.

**"IO layer" names a location. "Hardware abstraction" names a property.**

- The IO layer is *where* the boundary sits — one interface per subsystem, at the line between the subsystem's logic and its devices.
- Hardware abstraction is a *property* an interface may or may not have — independence from the specific device.

A given interface can sit at the IO-layer location while having very little true hardware abstraction, or a lot. They are not the same axis, which is why they feel tangled. The next sections take them apart with a single diagnostic.

## What every implementation shares

Strip away the per-team decoration and every IO layer in the corpus has the same four parts.

**1. An interface that names the hardware boundary.** One interface per subsystem (`ElevatorIO`, `GyroIO`, `ModuleIO`), declaring only the operations that cross the hardware line: a way to read the device's current state and a way to command outputs to it. No control logic, no game logic — just the contract. This is dependency inversion: the subsystem depends on an abstraction, not on a `TalonFX`.

**2. Output methods — commands going to hardware.** Methods that actuate the device. At the subsystem level these are commands like `setPosition(double inches)`; at the raw device level they are primitives like `runVolts(double)`. Which of these an interface exposes is not cosmetic — it tells you where the control loop lives, the subject of the next section.

**3. An inputs channel — state coming back from hardware.** Every implementation reports position, velocity, applied voltage, current, temperature, and a connected flag back up to the logic. This is the one place the two dominant styles truly diverge (see Variation 1): some teams pass a mutable inputs object the implementation fills in; others expose plain getters. Both answer "what is the hardware doing right now?"

**4. Interchangeable implementations, selected at construction.** At minimum a real one (talks to motors) and a sim one (talks to a WPILib physics model). The subsystem is handed one in its constructor and never learns which. Selection happens in exactly one place — a constructor call, a `create()` factory, or a switch on robot identity — so the entire behavior of "run on a real robot" versus "run on a laptop" turns on a single line.

6328's drivetrain shows the selection in its barest form — the same `Drive` object built three ways depending on what hardware is present:

```java
// 6328 — RobotContainer.java, implementation selection (abridged)
switch (Constants.getRobot()) {
  case COMPBOT ->                              // real competition robot
    drive = new Drive(new GyroIOPigeon2(),
      new ModuleIOComp(0), new ModuleIOComp(1), /* ... */);
  case SIMBOT ->                               // laptop simulation
    drive = new Drive(new GyroIO() {},         // anonymous no-op gyro
      new ModuleIOSim(), new ModuleIOSim(), /* ... */);
  default ->                                   // replay: feed everything from logs
    drive = new Drive(new GyroIO() {},
      new ModuleIO() {}, new ModuleIO() {}, /* ... */);
}
```

That `new GyroIO() {}` — an empty inline implementation — is worth noticing. When every interface method has a default empty body, the no-op implementation costs zero extra files. It is the replay/absent case for free.

## The line that matters: where the control loop lives

The control loop is the code that turns "go to height H" into the moment-by-moment voltages that get there — a PID plus a feedforward. Where that loop sits is the diagnostic that classifies any IO interface. One question cuts cleanly: **which side of the interface is the control loop on?**

### Loop above the line — the interface is a device pipe

If the subsystem holds the PID and feedforward and computes a voltage every cycle, the only thing left to send across the interface is that voltage. The interface ends up exposing `setVoltage(double)` — a raw actuator primitive. SciBorgs do this: their `Elevator` subsystem owns a `ProfiledPIDController` and an `ElevatorFeedforward` as fields, computes the output, and pushes volts down through the IO.

```java
// 1155 SciBorgs — the loop sits in the subsystem, so the IO takes volts

// in Elevator.java (the SUBSYSTEM, above the interface):
private final ProfiledPIDController pid = new ProfiledPIDController(kP, kI, kD, /* ... */);
private final ElevatorFeedforward   ff  = new ElevatorFeedforward(kS, kG, kV, kA);

// interface (below): a dumb pipe to the motor
public interface ElevatorIO extends AutoCloseable {
  void   setVoltage(double voltage);   // raw actuator command
  double position();                   // meters
  double velocity();                   // meters/sec
  void   resetPosition();
}
```

An `ElevatorIO` with a `setVoltage` method reads at the wrong level for an elevator — and that instinct is the correct diagnostic. "Set voltage" is a motor verb, not an elevator verb. Its presence is the tell that the elevator's intelligence lives *above* this interface, and the interface is functioning as a hardware abstraction layer — a thin device pipe — with the subsystem as the smart layer on top.

One impurity is worth noting: SciBorgs' `position()` returns meters, an elevator unit, so the gear-ratio conversion has leaked below the line. A perfectly pure device pipe would return motor rotations and convert above. Real code is rarely that pure.

### Loop below the line — the interface is a subsystem-intent contract

If instead each implementation carries its own controller, the interface can speak in the subsystem's own terms — `setPosition(inches)` — and the implementations are responsible for running the loop that gets there. PhantomCatz do this. Their interface commands a position *and* exposes the gains, because the controller lives in the implementation (here, CTRE's on-motor MotionMagic firmware):

```java
// 2706 PhantomCatz — gains pushed BELOW the line; the loop runs in the implementation
default void setPosition(double inches) {}                      // intent
default void setGainsSlot0(double kP, double kI, double kD,
    double kS, double kV, double kA, double kG) {}             // the loop's gains...
default void setMotionMagicParameters(double cruiseVelocity,    // ...live below
    double acceleration, double jerk) {}
```

Here the interface reads at the right level for an elevator, and the implementations are full hardware bundles, each owning the control math. This is the "fat IO" or true subsystem-intent style. Its cost is that the loop is reimplemented (or reconfigured) per strategy — the real one tunes firmware MotionMagic, the sim one needs its own controller to honor `setPosition`.

The full PhantomCatz interface is the same one quoted in Part I: the output verb is `setPosition`, the readback is `positionInch`, and the elevator never traffics in volts at the subsystem level.

```java
// 2706 PhantomCatz — CatzElevator/ElevatorIO.java (abridged to the essential surface)
public interface ElevatorIO {
  @AutoLog
  class ElevatorIOInputs {
    public double  positionInch        = 0.0;   // read: height
    public double  velocityInchPerSec  = 0.0;   // read: speed
    public boolean isLeaderMotorConnected = false;
  }

  default void updateInputs(ElevatorIOInputs inputs) {}
  default void setPosition(double inches) {}      // command: go to a height
  default void setBrakeMode(boolean enabled) {}
  default void stop() {}
}
```

### The rule

Both styles are legitimate Strategy implementations sitting at the IO-layer location. They differ only on loop placement, and that placement is what makes one interface look like a HAL and the other like a subsystem contract.

| | Loop ABOVE the line | Loop BELOW the line |
|---|---|---|
| Interface command | `setVoltage(volts)` | `setPosition(inches)` |
| What it reads as | A device pipe (HAL-like) | A subsystem-intent contract |
| Where PID/FF lives | In the subsystem, written once | In each implementation |
| Implementations are | Trivial (forward the volts) | Full bundles (each runs a loop) |
| Corpus example | SciBorgs 1155 | PhantomCatz 2706 (CTRE MotionMagic) |

So: a pure IO layer is Strategy applied at subsystem granularity, and whether it *also* looks like a hardware abstraction layer depends entirely on whether you left the control loop above it. See `setVoltage` on something named for a mechanism — the loop is above, the interface is a HAL. See `setPosition` — the loop is below, the interface is a subsystem contract. Same location, same pattern, different placement of the brains. The detailed control-path treatment is in [chapter 15](15-control-path.md).

## Selecting the strategy

Selection lives in one place. PhantomCatz switch on robot mode, with an anonymous no-op for replay:

```java
// 2706 PhantomCatz — strategy selection
elevatorIO = switch (Constants.getRobotMode()) {
  case REAL    -> new ElevatorIOReal();   // CTRE MotionMagic to a position
  case SIM     -> new ElevatorIOSim();    // physics model to a position
  case REPLAY  -> new ElevatorIO() {};    // no-op: logs drive the inputs
};
```

SciBorgs do the same selection as factory methods, with an explicit null-object strategy for the disabled-hardware case:

```java
// 1155 SciBorgs — Elevator.java, factory selection + null object
public static Elevator create() {
  return new Elevator(Robot.isReal() ? new RealElevator() : new SimElevator());
}

public static Elevator none() {
  return new Elevator(new NoElevator());   // Null Object: a do-nothing strategy
}
```

One interface, interchangeable strategies, selected in one place, swappable over time without touching the interface or the subsystem.

## Four variations

Teams differ on four axes. None is right or wrong; each is a trade between boilerplate, logging power, and language ergonomics.

### Variation 1 — Inputs struct vs. direct getters (the logging fork)

The deepest fork, and it traces directly to a logging decision.

**The getter style (SciBorgs).** The interface exposes `position()` and `velocity()` as plain methods. Simple, readable, and the logic just calls them. The cost: nothing about the hardware state is automatically logged — you log what you choose to, separately.

**The inputs-struct style (6328 / AdvantageKit).** The interface has no read methods at all. Instead it has one method, `updateInputs(inputs)`, that fills a mutable data object. That object is annotated `@AutoLog`, and AdvantageKit serializes every field to the match log every cycle. Here is 6328's gyro — exactly one method, and the "read" half of the interface is the struct it populates:

```java
// 6328 — GyroIO.java (complete, header trimmed)
public interface GyroIO {
  @AutoLog
  class GyroIOInputs {
    public GyroIOData data = new GyroIOData(false, Rotation2d.kZero, 0, /* ... */);
    public double[]    odometryYawTimestamps = new double[] {};
    public Rotation2d[] odometryYawPositions = new Rotation2d[] {};
  }
  record GyroIOData(boolean connected, Rotation2d yawPosition,
      double yawVelocityRadPerSec, Rotation2d pitchPosition, /* ... */) {}

  default void updateInputs(GyroIOInputs inputs) {}   // the only method
}
```

The struct style is what makes whole-match log replay possible. Because every value crossing the hardware boundary lands in a logged struct, AdvantageKit can later feed a recorded log back through the real code and reproduce exactly what the robot decided. The getter style cannot do this — it has no single chokepoint to record. That replay guarantee is also why 6328's entire robot program must be single-threaded and deterministic: an architectural invariant dictating a coding rule.

The trade: the struct style is more boilerplate (a data class plus an inputs wrapper per subsystem) bought in exchange for free, complete, replayable telemetry. The getter style is less code and is fine until you want to debug a match you can no longer reproduce.

### Variation 2 — Per-subsystem interface vs. one generic base

6328 writes a fresh `XxxIO` interface for every mechanism. 254 noticed that most position-controlled mechanisms (elevator, arm, wrist, pivot) need the same handful of motor operations, and collapsed them into a single parameterized base class:

```java
// 254 — the generic servo subsystem (signature)
class ServoMotorSubsystem<
      T extends MotorInputsAutoLogged,
      U extends MotorIO>
    extends SubsystemBase { /* ... */ }
```

A concrete mechanism becomes a thin subclass plus a config object holding gains, gear ratios, and limits. There is one `MotorIO` interface and one `TalonFXIO` / `SimTalonFXIO` pair shared across every mechanism. The trade: maximum reuse and almost no per-mechanism code, paid for with heavy generics and a steeper on-ramp for a new student. 6328's per-subsystem interfaces are more verbose but each one is independently readable. The archetype split that makes the generic base possible is the subject of [chapter 18](18-subsystem-archetypes.md).

### Variation 3 — The null object: named class vs. anonymous

Every mature IO layer has a third implementation beyond real and sim: the do-nothing one, for running with a mechanism unplugged or replaying from logs. Two ways to express it.

- **Named class** (SciBorgs `NoElevator`, PhantomCatz `ElevatorIONull`). Explicit, greppable, self-documenting — there is a file you can point at. The null-object pattern made visible.
- **Anonymous inline** (`new GyroIO() {}`, 6328). Costs zero files because the interface's methods all have empty default bodies, so an empty implementation is automatically a safe no-op. 6328 uses this 30+ times across the codebase for replay and sim-stub cases.

The anonymous form only works with the struct style, where methods can default to empty. The getter style returns values, so its no-op must return something (`return 0;`) — which is why SciBorgs writes `NoElevator` out as a real class. The two forks are not independent: the logging choice (Variation 1) constrains the null-object choice (Variation 3).

### Variation 4 — The language carries part of the pattern

In Kotlin (3636, 4099) the architecture is identical to 6328's, but the language enforces for free what Java teams hand-roll. The same `FunnelIO` interface, a real implementation, and a sim implementation — but the singleton, the unit types, and the inputs class are language features, not boilerplate:

```java
// 3636 — FunnelIO.kt (abridged; active fields shown, commented telemetry omitted)
@Logged
open class FunnelInputs { /* logged fields */ }

interface FunnelIO {
    fun setSpeed(percent: Double)
    fun setVoltage(voltage: Voltage)        // Voltage is a *type*, not a double
    fun updateInputs(inputs: FunnelInputs)
}

class FunnelIOReal : FunnelIO {
    private var rampMotor = TalonFX(CTREDeviceId.FunnelMotor).apply { /* ... */ }
    override fun setVoltage(voltage: Voltage) {
        assert(voltage.inVolts() in -12.0..12.0)
        rampMotor.setVoltage(voltage.inVolts())
    }
    override fun updateInputs(inputs: FunnelInputs) { /* ... */ }
}

class FunnelIOSim : FunnelIO {
    private var simMotor = FlywheelSim(system, motor, 0.0)
    override fun setSpeed(percent: Double) { simMotor.inputVoltage = percent * 12 }
    override fun updateInputs(inputs: FunnelInputs) { simMotor.update(Robot.period) }
}
```

The `Voltage` parameter type is the lesson: in Kotlin a height and a voltage are different types, so handing a motor a distance where it wants a voltage is a compile error rather than a runtime mystery. Putting the same elevator IO in Java and Kotlin side by side makes visible which lines are the design and which are merely Java ceremony.

## Naming the implementations

The corpus names implementations by device, not by the abstract word "Real":

- The sim impl is reliably `XxxIOSim` (or `SimXxx`).
- The hardware impl is named **by device** — `XxxIOTalonFX`, `XxxIOSparkMax`, `XxxIOKrakenX60`, `GyroIOPigeon2`, `VisionIOLimelight` — **not `XxxIOReal`**. Only ~5 teams use `Real`. Naming the device documents the vendor at the seam.
- The `XxxIOInputs` struct always co-exists with the interface; the null-object / replay variants are real but rare (~1 team ships a dedicated replay impl).

The four files that constitute a subsystem (the "quartet") are:

```
xxx/
  XxxIO.java            // the contract: what the subsystem needs from hardware
  XxxIO<device>.java    // the hardware impl — the ONLY file that imports a vendor SDK
  XxxIOSim.java         // the simulation impl — wraps a WPILib sim model; WPILib only
  Xxx.java              // the subsystem — holds ONE XxxIO, owns control logic, exposes Commands
```

The motor-interface layer that sits underneath these — `MotorIO`, `TalonFXIO`, and friends — is the subject of [chapter 17](17-motor-interfaces.md).

## Vendor confinement and leak detection

The IO line is only worth drawing if vendor types stay below it. The rule:

> A `TalonFX`, a `PhotonCamera`, a `SparkMax` appears **only** inside a `XxxIO<device>` or `XxxIOSim` file — never in the subsystem, a command, or the `Superstructure`. The moment `com.ctre` / `com.revrobotics` / `org.photonvision` appears above the line, a tool swap becomes a refactor and the subsystem stops being portable.

This is the most-violated rule in the corpus: **22 of 24** IO-layer teams leak a vendor type above the line at least once. Clean confinement is a distinguishing marker, not a baseline. Enforce it mechanically with a checkstyle/spotless import rule rather than by review alone.

### How to detect a leak

The detection is a directed import search. For each subsystem package, grep the files *above* the IO line (`Xxx.java`, commands, `Superstructure`, `RobotState`) for the three vendor roots:

```
com.ctre
com.revrobotics
org.photonvision
```

Any match above the line is a finding. The agent-facing review workflow in the code-review principles makes this step 2 of a deterministic pass:

1. Map touched seams (IO / state / coordination).
2. **Check vendor confinement** — search changed files for vendor imports above IO implementations.
3. Check interface shape — does the contract still support REAL + SIM without vendor leakage?
4. Check dependency direction — no upward dependency from subsystem to coordinator/state.
5. Check test path — can the code still be instantiated in sim-backed tests?
6. Check sim path — no SIM-only behavior fork.
7. Check logging path — inputs and key decisions remain observable.
8. Classify findings by severity.

Steps 2 and 3 are the two red flags specific to the IO line:

- A subsystem imports `com.ctre`, `com.revrobotics`, or `org.photonvision` directly.
- An interface exposes vendor-specific handles or configuration objects, or mirrors the vendor API surface without subsystem intent.

The evidence of correctness is symmetric: vendor imports exist *only* in `XxxIO<device>` and `XxxIOSim`, the subsystem constructor accepts an interface (`XxxIO`) rather than a vendor object, and the interface can be implemented by both a hardware class and a physics-sim class.

### Severity

The code-review principles assign severity by the invariant a change breaks, not by whether the robot currently runs:

| Severity | Meaning | Applied to the IO line |
|---|---|---|
| S0 Blocker | Breaks an architectural invariant or makes safe operation unverifiable | A subsystem that cannot execute with `XxxIOSim` at all; new mechanism code skipping the IO seam by design |
| S1 High | Preserves runtime behavior today but creates a near-term test/sim/replay dead end | A vendor type leaked above the line; an interface that a sim class cannot implement |
| S2 Medium | Local design smell that increases coupling or hides intent | An interface method that mirrors a vendor call without subsystem intent |
| S3 Low | Readability or consistency issue | Naming the hardware impl `XxxIOReal` instead of by device |

Two framings from the principles govern how a reviewer treats these. First: **review what is used, not what is present** — a vendordep in the build file is not adoption, and an `XxxIO` interface that no implementation actually swaps is not a seam. Confirm by opening the files. Second: **treat architecture regressions as functional regressions** — a leaked vendor type is a finding even when the robot behaves correctly on the field. "Works on robot" is not a justification for bypassing the abstraction, and "will refactor later" for a vendor leak is architectural debt that must carry a dated remediation plan.

The non-negotiable anti-patterns that auto-fail a review, restricted to the IO line, are: vendor types imported above IO implementations; subsystem logic that cannot execute with `XxxIOSim`; and new mechanism code skipping the IO seam by design.

## Why confinement pays

The three rules below are the same property seen three ways — you can test in isolation and lift the subsystem out as a library *because* the vendor and the siblings are kept out:

1. **Mock below, test above.** Because the sim impl is just another `XxxIO`, you can construct the *real* subsystem against *fake* hardware and unit-test it with zero hardware and zero other subsystems — `new Elevator(new SimElevator())`, command a setpoint, step the sim, assert it arrived.
2. **Rip it out as a library.** The subsystem package imports WPILib plus its own contract and no sibling subsystem. If a sibling import sneaks in, the seam has leaked.
3. **Never import a vendor type above the IO line.** The rule of this chapter, restated as an ethic.

These are the IO layer's deferred dividends — simulation, unit testing, and replay all fall out of the one interface. They are the subject of the cross-cutting-practices chapters; the seam built here is what makes them mechanically possible.

---

Next: [chapter 17 — motor interfaces](17-motor-interfaces.md), the layer beneath the subsystem IO where `MotorIO` and its device implementations live.
