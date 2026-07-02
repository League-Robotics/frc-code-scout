The IO Layer in FRC

**The IO Layer in FRC**

**Hardware abstraction as the one near-universal pattern in serious robot code**

*Why the IO layer is the Strategy pattern, what every implementation shares, where it blurs into a hardware abstraction layer, and the real code that implements it — read from source (6328, SciBorgs, PhantomCatz, 3636, 254, 2056), cloned June 2026.*

**Contents**

# Which teams use it

Of the 37 teams in the FRC corpus, the IO layer is the single most widely shared architectural idea — present in some form in roughly two-thirds of the Java and Kotlin codebases, and the default rather than the exception among the strong ones. The teams below are the ones whose source makes the pattern legible, grouped by what each one is the clearest example of.

| **Team** | **Language** | **What their IO layer demonstrates** |
| --- | --- | --- |
| 6328 Mechanical Advantage | Java | The canonical form. Defined the pattern via AdvantageKit: an interface per subsystem, a logged inputs struct, and real / sim / replay implementations. |
| 254 | Java | The same idea generalized into one parameterized base class (ServoMotorSubsystem) shared across every position-controlled mechanism. |
| 3636 / 4099 | Kotlin | The identical pattern in Kotlin, where the language enforces unit-safety and singletons that Java teams hand-roll. |
| 1155 SciBorgs | Java | The cleanest naming (Real / Sim / No), an explicit null object, and the payoff: subsystems unit-tested in sim on CI. |
| 2706 PhantomCatz | Java | A regional team that independently reinvented the whole 6328 toolkit — the convergence evidence — plus an explicit IONull. |
| 4481 / 2767 / 5026 / 9015 / 1257 / 1741 | Java | Regional AdvantageKit builds carrying the IO layer as a matter of course; 4481 alone has 32 IO files including replay variants. |
| 2056 OP Robotics / 1538 The Holy Cows | C++ | The C++ story — but with an important caveat about what counts as an IO layer (see the C++ note below). |
| 971 Spartan Robotics | C++/Rust | The pattern's logical extreme: hardware decoupling pushed all the way to a separate process behind a message contract. |

# The problem it solves

WPILib hands every team a subsystem class that owns its motors directly — the drivetrain subsystem holds TalonFX objects, calls .setVoltage() on them, and reads .getPosition() back. That works, and it is where every team starts. The coupling it leaves is the problem: the subsystem's logic is welded to specific hardware. You cannot run that subsystem without the physical robot plugged in, you cannot swap a motor controller without editing the logic, and you cannot replay a match through the code because the sensor reads come straight off the CAN bus.

The IO layer breaks that weld with one move: **insert an interface between the subsystem****'****s logic and its physical devices.** The subsystem talks to the interface; concrete implementations talk to hardware, to a physics simulation, or to nothing at all. The logic no longer knows or cares which.

# What it really is: Strategy

“IO layer” is FRC's house name for it, but the pattern has an older and more precise name. The IO layer **is the Strategy pattern.** Strategy, in the Gang of Four sense, defines a family of interchangeable implementations behind one interface and lets the caller select which implementation is in force — and, critically, lets that implementation vary independently of the interface and of the code that uses it. That is exactly what an IO layer does: ElevatorIO is the strategy interface; RealElevator, SimElevator, and NoElevator are interchangeable strategies; and the subsystem holds a reference to one of them without knowing which.

The point of Strategy — the reason to reach for it — is that **the implementation can change over time without any change to the interface or to the code that depends on it.** A team writes the subsystem's logic once against ElevatorIO, then swaps the strategy underneath: real hardware during a match, a physics model on a laptop, a log-replay stub after the match, a different motor vendor next season. None of those swaps touches the interface, and none touches the subsystem. That independence is the whole value, and it is why a curriculum should teach this as Strategy first and “IO layer” second — the FRC name describes where the pattern sits; the GoF name describes what it is.

Two related GoF patterns sit nearby and are worth naming so students can tell them apart:

- **Factory Method** is the selection step. SciBorgs' Elevator.create() and Elevator.none() are factory methods that choose which strategy to instantiate. The factory picks the strategy; the strategy does the work.

- **Null Object** is the do-nothing strategy. NoElevator is a full member of the strategy family whose methods are deliberately empty, so a subsystem with disconnected hardware runs as a safe no-op instead of crashing. It is a strategy, not an absence of one.

A note on the related-but-different case. A true **hardware abstraction layer** — “any motor accepts a voltage, regardless of vendor” — is structurally similar but is better described as **Bridge**: it splits an abstraction (motor) from its implementation (TalonFX driver) so the two evolve separately, a design-time structural concern. Strategy and Bridge look almost identical in code; GoF distinguishes them by intent. Strategy swaps behavior at runtime (real-vs-sim, flipped every deploy); Bridge lets structure evolve independently (device independence, decided once). The IO layer leans Strategy because the swap is a runtime choice you make on every deploy. The distinction matters for the next section, where the line between the two blurs in real code.

# The common structure — what every implementation shares

Strip away the per-team decoration and every IO layer in the corpus has the same four parts.

### 1. An interface that names the hardware boundary

One interface per subsystem (ElevatorIO, GyroIO, ModuleIO), declaring only the operations that cross the hardware line: a way to read the device's current state, and a way to command outputs to it. No control logic, no game logic — just the contract. This is plain dependency inversion: the subsystem depends on an abstraction, not on a TalonFX.

### 2. Output methods — commands going to hardware

Methods that actuate the device: at the subsystem level these are commands like setPosition(double inches) or runToHeight(Distance); at the raw device level they are primitives like runVolts(double) or setBrakeMode(boolean). Which of these a given interface exposes is not cosmetic — it tells you where the control loop lives, and that is the whole subject of the section after next. For now: these are how the subsystem's logic actuates the device, identical in signature across every implementation, differing only in body.

### 3. An inputs channel — state coming back from hardware

Every implementation needs to report position, velocity, applied voltage, current, temperature, and a connected flag back up to the logic. This is the one place the two dominant styles genuinely diverge (see variations below): some teams pass a mutable inputs object the implementation fills in; others expose plain getter methods. Both answer the same question — “what is the hardware doing right now?”

### 4. Interchangeable implementations, selected at construction

At minimum a real one (talks to motors) and a sim one (talks to a WPILib physics model). The subsystem is handed one of them in its constructor and never learns which. Selection happens in exactly one place — a constructor call, a create() factory, or a switch on robot identity — so the entire behavior of “run on a real robot” versus “run on a laptop” turns on a single line.

6328's own drivetrain shows the selection in its barest form — the same Drive object built three different ways depending on what hardware is present:

*6328 — RobotContainer.java, implementation selection (abridged)*

switch (Constants.getRobot()) {

  case COMPBOT ->                              // real competition robot

    drive = new Drive(new GyroIOPigeon2(),

      new ModuleIOComp(0), new ModuleIOComp(1), ...);

  case SIMBOT ->                               // laptop simulation

    drive = new Drive(new GyroIO() {},         // anonymous no-op gyro

      new ModuleIOSim(), new ModuleIOSim(), ...);

  default ->                                   // replay: feed everything from logs

    drive = new Drive(new GyroIO() {},

      new ModuleIO() {}, new ModuleIO() {}, ...);

}

That new GyroIO() {} — an empty inline implementation — is worth noticing: when every interface method has a default empty body, the no-op implementation costs zero extra files. It is the replay/absent case for free.

# The sparest real implementation

An elevator's job, stated in its own terms, is “go to a height.” So the interface that reads most honestly is one whose command is a position and whose readback is a position. PhantomCatz's elevator interface does exactly that — the output verb is setPosition, the readback is positionInch, and the elevator never traffics in volts at the subsystem level:

*2706 PhantomCatz — CatzElevator/ElevatorIO.java (abridged to the essential surface)*

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

setPosition(inches) is the right level of abstraction for an elevator: the caller asks for a height and the implementation is responsible for getting there. The strategy interface reads like the thing it models. Each implementation is then swapped underneath without the subsystem changing — the same Strategy move as everywhere else:

*Selecting the strategy (PhantomCatz pattern)*

elevatorIO = switch (Constants.getRobotMode()) {

  case REAL    -> new ElevatorIOReal();   // CTRE MotionMagic to a position

  case SIM     -> new ElevatorIOSim();    // physics model to a position

  case REPLAY  -> new ElevatorIO() {};    // no-op: logs drive the inputs

};

And SciBorgs show the same selection done as factory methods, with an explicit null-object strategy for the disabled-hardware case:

*1155 SciBorgs — Elevator.java, factory selection + null object*

public static Elevator create() {

  return new Elevator(Robot.isReal() ? new RealElevator() : new SimElevator());

}

public static Elevator none() {

  return new Elevator(new NoElevator());   // Null Object: a do-nothing strategy

}

That is the whole pattern: one interface, interchangeable strategies, selected in one place, swappable over time without touching the interface or the subsystem.

# The line that actually matters: where the control loop lives

There is a real and persistent ambiguity in FRC about whether the IO layer is a hardware abstraction layer or something else, and it is worth resolving directly because it changes how you read every interface in the corpus.

**“IO layer” names a location; “hardware abstraction” names a property.** The IO layer is *where* the boundary sits — one interface per subsystem, at the line between the subsystem's logic and its devices. Hardware abstraction is a *property* an interface may or may not have — independence from the specific device. A given interface can sit at the IO-layer location while having very little true hardware abstraction, or a lot. They are not the same axis, which is why they feel tangled.

The diagnostic that cuts cleanly is a single question: **which side of the interface is the control loop on?** The control loop is the code that turns “go to height H” into the moment-by-moment voltages that get there — a PID plus a feedforward. Where that loop sits determines what kind of interface you are looking at.

### Loop above the line — the interface is a device pipe

If the subsystem holds the PID and feedforward and computes a voltage every cycle, then the only thing left to send across the interface is that voltage. The interface ends up exposing setVoltage(double) — a raw actuator primitive. This is what SciBorgs do: their Elevator subsystem owns a ProfiledPIDController and an ElevatorFeedforward as fields, computes the output, and pushes volts down through the IO:

*1155 SciBorgs — the loop sits in the subsystem, so the IO takes volts*

// in Elevator.java (the SUBSYSTEM, above the interface):

private final ProfiledPIDController pid = new ProfiledPIDController(kP, kI, kD, ...);

private final ElevatorFeedforward   ff  = new ElevatorFeedforward(kS, kG, kV, kA);

 

// interface (below): a dumb pipe to the motor

public interface ElevatorIO extends AutoCloseable {

  void   setVoltage(double voltage);   // raw actuator command

  double position();                   // meters

  double velocity();                   // meters/sec

  void   resetPosition();

}

This is why an ElevatorIO can end up with a setVoltage method that reads at the wrong level for an elevator — and your instinct that it is the wrong level is the correct diagnostic. “Set voltage” is a motor verb, not an elevator verb. Its presence is the tell that the elevator's intelligence lives *above* this interface, and the interface is functioning as a hardware abstraction layer — a thin device pipe — with the subsystem as the smart layer on top. (The one impurity worth noting: SciBorgs' position() returns meters, an elevator unit, so the gear-ratio conversion has leaked below the line. A perfectly pure device pipe would return motor rotations and convert above. Real code is rarely that pure.)

### Loop below the line — the interface is a subsystem-intent contract

If instead each implementation carries its own controller, the interface can speak in the subsystem's own terms — setPosition(inches) — and the implementations are responsible for running the loop that gets there. PhantomCatz do this: their interface not only commands a position but exposes the gains, because the controller lives in the implementation (here, CTRE's on-motor MotionMagic firmware):

*2706 PhantomCatz — gains pushed BELOW the line; the loop runs in the implementation*

default void setPosition(double inches) {}                      // intent

default void setGainsSlot0(double kP, double kI, double kD,

    double kS, double kV, double kA, double kG) {}              // the loop's gains...

default void setMotionMagicParameters(double cruiseVelocity,    // ...live below

    double acceleration, double jerk) {}

Here the interface reads at the right level for an elevator, and the implementations are full hardware bundles, each owning the control math. This is the “fat IO” or true subsystem-intent style. Its cost is that the loop is reimplemented (or reconfigured) per strategy — the real one tunes firmware MotionMagic, the sim one needs its own controller to honor setPosition.

### The rule

Both styles are legitimate Strategy implementations sitting at the IO-layer location. They differ only on loop placement, and that placement is what makes one interface look like a HAL and the other like a subsystem contract:

|  | **Loop ABOVE the line** | **Loop BELOW the line** |
| --- | --- | --- |
| Interface command | setVoltage(volts) | setPosition(inches) |
| What it reads as | A device pipe (HAL-like) | A subsystem-intent contract |
| Where PID/FF lives | In the subsystem, written once | In each implementation |
| Implementations are | Trivial (forward the volts) | Full bundles (each runs a loop) |
| Corpus example | SciBorgs 1155 | PhantomCatz 2706 (CTRE MotionMagic) |

So: a pure IO layer is the Strategy pattern applied at subsystem granularity, and whether it also looks like a hardware abstraction layer depends entirely on whether you left the control loop above it. If you see setVoltage on something named for a mechanism, the loop is above and the interface is a HAL. If you see setPosition, the loop is below and the interface is a subsystem contract. Same location, same pattern, different placement of the brains.

# Variations

Teams differ on four axes. None of these is right or wrong; each is a trade between boilerplate, logging power, and language ergonomics.

## Variation 1 — Inputs struct vs. direct getters

This is the deepest fork, and it traces directly to a logging decision.

**The getter style (SciBorgs).** The interface exposes position() and velocity() as plain methods. Simple, readable, and the logic just calls them. The cost: nothing about the hardware state is automatically logged — you log what you choose to, separately.

**The inputs-struct style (6328 / AdvantageKit).** The interface has no read methods at all. Instead it has one method, updateInputs(inputs), that fills a mutable data object. That object is annotated @AutoLog, and AdvantageKit serializes every field to the match log every cycle. Here is 6328's gyro — note there is exactly one method, and the “read” half of the interface is the struct it populates:

*6328 — GyroIO.java (complete, header trimmed)*

public interface GyroIO {

  @AutoLog

  class GyroIOInputs {

    public GyroIOData data = new GyroIOData(false, Rotation2d.kZero, 0, ...);

    public double[]    odometryYawTimestamps = new double[] {};

    public Rotation2d[] odometryYawPositions = new Rotation2d[] {};

  }

  record GyroIOData(boolean connected, Rotation2d yawPosition,

      double yawVelocityRadPerSec, Rotation2d pitchPosition, ...) {}

 

  default void updateInputs(GyroIOInputs inputs) {}   // the only method

}

**Why the struct style exists:** it is what makes whole-match log replay possible. Because every value crossing the hardware boundary lands in a logged struct, AdvantageKit can later feed a recorded log back through the real code and reproduce exactly what the robot decided. The getter style cannot do this — it has no single chokepoint to record. That replay guarantee is also why 6328's entire robot program must be single-threaded and deterministic: an architectural invariant dictating a coding rule.

**The trade:** the struct style is more boilerplate (a data class plus an inputs wrapper per subsystem) bought in exchange for free, complete, replayable telemetry. The getter style is less code and is fine until you want to debug a match you can no longer reproduce.

## Variation 2 — Hand-rolled per subsystem vs. one generic base

6328 writes a fresh XxxIO interface for every mechanism. 254 noticed that most position-controlled mechanisms (elevator, arm, wrist, pivot) need the same handful of motor operations, and collapsed them into a single parameterized base class:

*254 — the generic servo subsystem (signature)*

class ServoMotorSubsystem<

      T extends MotorInputsAutoLogged,

      U extends MotorIO>

    extends SubsystemBase { ... }

A concrete mechanism becomes a thin subclass plus a config object holding gains, gear ratios, and limits. There is one MotorIO interface and one TalonFXIO / SimTalonFXIO pair shared across every mechanism. **The trade:** maximum reuse and almost no per-mechanism code, paid for with heavy generics and a steeper on-ramp for a new student. 6328's per-subsystem interfaces are more verbose but each one is independently readable.

## Variation 3 — The null/no-op implementation: named class vs. anonymous

Every mature IO layer has a third implementation beyond real and sim: the do-nothing one, for running with a mechanism unplugged or replaying from logs. Teams express it two ways.

- **Named class (SciBorgs `NoElevator`, PhantomCatz `ElevatorIONull`).** Explicit, greppable, and self-documenting — there is a file you can point at. The null-object pattern made visible.

- **Anonymous inline (`new GyroIO() {}`, 6328).** Costs zero files because the interface's methods all have empty default bodies, so an empty implementation is automatically a safe no-op. 6328 uses this 30+ times across the codebase for exactly the replay and sim-stub cases.

The anonymous form only works with the struct style, where methods can default to empty. The getter style returns values, so its no-op must return something (return 0;) — which is why SciBorgs writes NoElevator out as a real class.

## Variation 4 — The language carries part of the pattern

In Kotlin (3636, 4099) the architecture is identical to 6328's, but the language enforces for free what Java teams hand-roll. The same FunnelIO interface, a real implementation, and a sim implementation — but the singleton, the unit types, and the inputs class are language features, not boilerplate:

*3636 — FunnelIO.kt (abridged; active fields shown, commented telemetry omitted)*

@Logged

open class FunnelInputs { /* logged fields */ }

 

interface FunnelIO {

    fun setSpeed(percent: Double)

    fun setVoltage(voltage: Voltage)        // Voltage is a *type*, not a double

    fun updateInputs(inputs: FunnelInputs)

}

 

class FunnelIOReal : FunnelIO {

    private var rampMotor = TalonFX(CTREDeviceId.FunnelMotor).apply { ... }

    override fun setVoltage(voltage: Voltage) {

        assert(voltage.inVolts() in -12.0..12.0)

        rampMotor.setVoltage(voltage.inVolts())

    }

    override fun updateInputs(inputs: FunnelInputs) { ... }

}

 

class FunnelIOSim : FunnelIO {

    private var simMotor = FlywheelSim(system, motor, 0.0)

    override fun setSpeed(percent: Double) { simMotor.inputVoltage = percent * 12 }

    override fun updateInputs(inputs: FunnelInputs) { simMotor.update(Robot.period) }

}

The Voltage parameter type is the lesson: in Kotlin a height and a voltage are different types, so handing a motor a distance where it wants a voltage is a compile error rather than a runtime mystery. The same elevator IO in Java and Kotlin side by side makes visible which lines are the design and which are merely Java ceremony.

## Variation 5 — C++, and an honest caveat

The consolidated survey lists 2056 (OP Robotics) as a C++ example of the IO layer. Reading the source closely, that needs qualifying. 2056 has an IO/ directory — OPRGyro, OPRSensors, OPRCameras — but these are concrete singleton hardware wrappers, not an abstract interface with swappable implementations:

*2056 — OPRGyro.h (abridged)*

class OPRGyro {

  public:

    static OPRGyro* GetInstance();      // singleton, not an interface

    OPRGyro(void);                      // constructs a real Pigeon2

    units::degree_t GetAngle();

    units::degree_t GetPitch();

    double GetAngleRate();

};

There is no OPRGyroSim, no interface OPRGyro could implement, and nothing to swap at construction. This is **directory-level organization** (“the hardware-touching code lives here”), which is useful, but it is not the dependency-inversion the IO layer is about. The honest reading: 2056 demonstrates tidy hardware encapsulation, not a true IO layer.

**Where C++ genuinely does the pattern:** two places, by different routes. The Holy Cows (1538) keep an explicit single-process IO with C++ unit tests — the direct analog of the Java form. And 971 push decoupling past the class boundary entirely: each subsystem is a separate OS process, and the “interface” is a typed FlatBuffers message contract (Goal / Position / Output / Status) passed over channels. 971's version is the same idea — isolate the logic from the hardware behind a contract — taken to the point where the contract is a versioned schema and the implementations are processes. It buys process isolation and testability by replaying message streams, at the cost of infrastructure most teams cannot maintain.

# Why the pattern won

Three payoffs fall out of that one interface, and they explain why a powerhouse signature became a regional default:

- **Simulation is free.** Swap the real implementation for the sim one — one line at construction — and the entire subsystem runs on a laptop with no robot. For a team with ten programmers and one robot on the cart, this is the whole game.

- **Unit testing becomes possible** — the IO layer's deferred dividend. Because a subsystem can be built with a sim implementation, you can drive it to completion in a test harness on CI and assert on the result. SciBorgs ship 14 JUnit suites doing exactly this; Ranger Robotics 37 test files. Almost no other FRC teams test robot code at all, and the IO layer is what makes it mechanically possible.

- **Hardware swaps and replay stay local.** Changing a motor controller, supporting a practice robot with different electronics, or replaying a recorded match all touch one IO file (or, for AdvantageKit, none — the log feeds the existing code). The logic above the line never moves.

# The one-line summary

The IO layer is the Strategy pattern applied at the per-subsystem hardware boundary: one interface, a family of interchangeable implementations (real / sim / null), selected in one place, swappable over time without touching the interface or the subsystem. Teams vary it on four axes — inputs-struct vs. getters (the logging fork), per-subsystem vs. one generic base (the reuse fork), named vs. anonymous null object, and how much the language does for you — and on one deeper axis, where the control loop lives, which decides whether the interface reads as a hardware abstraction layer (setVoltage, loop above) or a subsystem-intent contract (setPosition, loop below). The spine is identical across Java, Kotlin, and (properly done) C++ — the strongest evidence in the project that the principle is real and the syntax is incidental.

Page
