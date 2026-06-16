# Anatomy of a Subsystem — the shared template

This is the preamble for the per-subsystem deep-dives. It defines, **once**, the structure every
subsystem shares, the three rules that make a subsystem worth building, and the map of which
mechanism belongs to which document. Each subsystem doc instantiates this template for one
control archetype; read this first, then the doc for your mechanism.

This sits one level below [`../elite-architecture.md`](../elite-architecture.md), which builds the
whole-robot foundation (the IO / `RobotState` / `Superstructure` seams). Here we zoom into a
single subsystem and show how to build it so it can be **tested in isolation and lifted out as a
library**.

---

## The series

Subsystems are usually named after the game mechanism (elevator, arm, intake, shooter…), but they
**collapse to a handful of control archetypes** — the archetype, not the game name, determines the
IO contract, the simulation model, and the test. So the series is organized by archetype, each doc
led by its most recognizable mechanism, with the siblings covered as variants.

| Doc | Archetype | Mechanisms | Sim model | Contract shape |
|---|---|---|---|---|
| [`01-linear-position`](01-linear-position.md) | linear position | **Elevator**, Climber | `ElevatorSim` | position in, volts out |
| [`02-rotational-position`](02-rotational-position.md) | rotational position | **Arm**, Pivot, Wrist, Turret | `SingleJointedArmSim` | angle in, volts out |
| [`03-velocity`](03-velocity.md) | velocity | **Shooter**, Flywheel | `FlywheelSim` | speed in, volts out |
| [`04-roller-gamepiece`](04-roller-gamepiece.md) | roller + sensor | **Intake**, Indexer, Feeder, Manipulator | `DCMotorSim` + beam-break | run / stop + "have piece?" |
| [`05-vision-sensor`](05-vision-sensor.md) | sensor-only | **Vision** | replayed/sim observations | observations out, **no actuation** |
| [`06-swerve-drivetrain`](06-swerve-drivetrain.md) | swerve (special) | **Drivetrain** = Module + Gyro | `SwerveModuleSim` / maple-sim | two interfaces, kinematics |

If your mechanism isn't listed by name, find its archetype: anything that goes to a height is
`01`; anything that goes to an angle is `02`; anything that spins to a speed is `03`; anything that
moves game pieces past a sensor is `04`.

**The other two seams.** `elite-architecture.md` defines three seams; the docs above are all
instances of the **IO seam**. The other two get their own chapters — they are "subsystems" with no
hardware (their IO is information, not motors), and the purest examples of the ethic below (zero
vendor types, zero IO impls, hence the most testable):

| Doc | Seam | Its IO is | Rubric |
|---|---|---|---|
| [`07-robotstate`](07-robotstate.md) | state | observations in (odometry, vision) → fused pose out | D7 |
| [`08-superstructure`](08-superstructure.md) | coordination | goals in → guarded subsystem setpoints out | D2 |

**See also — the cross-cutting practices** (one level up, in `build-spec/`). These are the IO seam's
deferred dividends; every subsystem doc's §6 points into them:
[`../testing.md`](../testing.md) (the IO sim *is* the mock) · [`../simulation.md`](../simulation.md)
(what backs an `XxxIOSim`) · [`../logging.md`](../logging.md) (the inputs struct is the log).

## The four files that are a subsystem

Every subsystem in this series is the same four-part shape (the "quartet"), defined in
`elite-architecture.md` §2.2 and shown concretely throughout `01-linear-position`:

```
xxx/
  XxxIO.java            // the contract: what the subsystem needs from hardware (volts out, readings in)
  XxxIO<device>.java    // the hardware impl — the ONLY file that imports a vendor SDK (TalonFX, SparkMax)
  XxxIOSim.java         // the simulation impl — wraps a WPILib sim model; imports WPILib only
  Xxx.java              // the subsystem — holds ONE XxxIO, owns the control logic, exposes Commands
```

Two recurring companions: an **`XxxIOInputs` struct** (the readings, often `@AutoLog`-annotated so
AdvantageKit logs and replays them), and a **no-op / null** impl (`NoXxx` / `XxxIONull`) so the
robot runs with the mechanism disabled.

### Naming, as the corpus actually does it
- The sim impl is reliably **`XxxIOSim`** (or `SimXxx`).
- The hardware impl is named **by device** — `XxxIOTalonFX`, `XxxIOSparkMax`, `XxxIOKrakenX60`,
  `GyroIOPigeon2`, `VisionIOLimelight` — **not `XxxIOReal`** (only ~5 of 55 teams use `Real`). Naming
  the device documents the vendor at the seam.
- The `XxxIOInputs` struct always co-exists with the interface; the null-object/replay variants are
  real but rare (~1 team ships a replay impl).

## The three rules (the ethic — stated here once)

A subsystem is "done right" when all three hold. Every per-subsystem doc closes (§6) by applying
these to its archetype.

1. **Mock below, test above.** Because the sim impl is just another `XxxIO`, you can construct the
   *real* subsystem against *fake* hardware and unit-test it with **zero hardware and zero other
   subsystems** — `new Elevator(new SimElevator())`, command a setpoint, step the sim, assert it
   arrived. This is the IO layer's whole payoff (rubric D4) and the rarest marker in the corpus.

2. **Rip it out as a library.** The subsystem's package must import **WPILib + its own contract**
   and **no sibling subsystem** — no `Drive` inside `Arm`, no `Superstructure` inside `Elevator`.
   The test: could `xxx/` be a Gradle module another robot depends on? If a sibling-subsystem import
   sneaks in, the answer is no and the seam has leaked.

3. **Never import a vendor type above the IO line.** A `TalonFX`, a `PhotonCamera`, a `SparkMax`
   appears **only** inside a `XxxIO<device>` or `XxxIOSim` file — never in the subsystem, a command,
   or the `Superstructure`. The moment `com.ctre` / `com.revrobotics` / `org.photonvision` appears
   above the line, a tool swap becomes a refactor and the subsystem stops being portable. The corpus
   shows **22 of 24** IO-layer teams violate this; treat clean confinement as a distinguishing
   marker and enforce it with a checkstyle/spotless import rule.

These three are not independent — they are the same property seen three ways. You can only test in
isolation (1) and lift out as a library (2) *because* the vendor and the siblings are kept out (3).

## How each subsystem doc is structured

Every doc in the series follows the same seven sections, so you always know where to look:

1. **What it does** — the job and which mechanisms collapse into the archetype.
2. **How it operates** — the control truth, where the loop lives ("the line"), the sim model, a
   class diagram.
3. **The contract** — the `XxxIO` interface (methods) + the `XxxIOInputs` fields, and what the
   contract deliberately omits.
4. **Real implementations from the corpus** — the interface, the `<device>` impl, the sim impl, and
   the subsystem, quoted and attributed to `<team#> <name> — <repo>/<path>`.
5. **Variations across teams** — how named mechanisms and teams diverge, with code references.
6. **The ethic, applied** — a worked JUnit test (mock below / test above), the library-extraction
   test, and the vendor-discipline callout for that archetype.
7. **Checklist** — "is your subsystem intact?"

## Appendix — the subsystem with no IO control loop (LEDs / status output)

About twenty teams ship an **LED/status** subsystem, and it is the deliberate exception to this
template: it has **no sensor feedback and no control loop**, only an output buffer the rest of the
robot writes patterns to. There is little to abstract — an `LEDs` subsystem wrapping an
`AddressableLED` + buffer, with methods like `setPattern(...)` that other subsystems or the
`Superstructure` call to surface state (have-piece, aligned, climbing). It still obeys rule 3 (no
vendor type leaks — `AddressableLED` is WPILib), but it has no `XxxIO` worth a deep-dive, no sim
model, and no meaningful unit test. Build it as a thin output sink; don't force the quartet onto it.
