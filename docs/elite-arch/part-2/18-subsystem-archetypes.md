---
title: 18. Subsystem archetypes
weight: 18
---

*Part I motivated the IO quartet in the abstract; this chapter applies it per mechanism. Game mechanisms — elevator, arm, shooter, intake — collapse to a small set of control archetypes, and the archetype, not the game name, decides the IO contract, the WPILib sim model, and the test. This chapter walks the four actuating archetypes, each with its sim model, an abridged real example, the one control decision it forces, and the testability point it turns on.*

[Chapter 3](../part-1/03-the-io-seam.md) introduced the IO seam and the four-file quartet that hangs off it: an interface, a hardware implementation, a sim implementation, and the subsystem that holds one of them. That chapter argued the seam is worth its cost. It deferred the per-mechanism detail to here. This is that detail — the same seam drawn four times, once for each control type a robot actually builds.

The companion chapters in this part fill in the surrounding machinery: the [control path](15-control-path.md) that runs above the seam, [hardware abstraction](16-hardware-abstraction.md) and [motor interfaces](17-motor-interfaces.md) that sit at and below it. The two seams that have no motors at all — the [world model](20-the-world-model.md) and the coordination layer ([state machines](22-coordination-state-machines.md), [graphs and trees](23-coordination-graphs-trees.md)) — are their own chapters. Vision, a sensor-only subsystem, is [chapter 21](21-vision-systems.md). The [drivetrain](19-the-drivetrain-subsystem.md), a special case with two interfaces and kinematics, comes next.

---

## The shared template

A subsystem is usually named after the game mechanism, but mechanisms collapse to a handful of control archetypes. The archetype determines three things: the shape of the IO contract, the WPILib simulation model that backs the fake hardware, and the unit test you can write. So the material is organized by archetype, each led by its most recognizable mechanism.

| Archetype | Mechanisms | Sim model | Contract shape |
|---|---|---|---|
| linear position | **Elevator**, Climber | `ElevatorSim` | position in, volts out |
| rotational position | **Arm**, Pivot, Wrist, Turret | `SingleJointedArmSim` | angle in, volts out |
| velocity | **Shooter**, Flywheel | `FlywheelSim` | speed in, volts out |
| roller + sensor | **Intake**, Indexer, Feeder, Manipulator | `DCMotorSim` + beam-break | run / stop + "have piece?" |

If a mechanism is not listed by name, find its archetype. Anything that goes to a height is linear position; anything that goes to an angle is rotational position; anything that spins to a speed is velocity; anything that moves game pieces past a sensor is a roller.

### The quartet, per archetype

Every subsystem in this chapter is the same four-file quartet — contract, device-named hardware impl, sim impl, subsystem — whose canonical shape and naming conventions are [chapter 16's](16-hardware-abstraction.md#naming-the-implementations). Two recurring companions ride along: an **`XxxIOInputs` struct** carries the readings, often `@AutoLog`-annotated so AdvantageKit logs and replays them, and a **no-op / null** implementation (`NoXxx` / `XxxIONull`) lets the robot run with the mechanism disabled. What changes per archetype is only what crosses the line and which WPILib model backs the fake hardware.

### The ethic, applied

[Chapter 16](16-hardware-abstraction.md#why-confinement-pays) states the ethic canonically: mock below and test above, keep the package liftable as a library, and never let a vendor type cross above the IO line — three views of the same property. The sections below do not restate it; they apply it to each archetype's specifics.

One mechanism is the deliberate exception to the quartet: an **LED / status** subsystem has no sensor feedback and no control loop, only an output buffer the rest of the robot writes patterns to. Build it as a thin output sink wrapping an `AddressableLED`; do not force the quartet onto it.

---

## Linear position — the reference archetype

A linear position mechanism moves a carriage to a commanded **height** along a rail and holds it against gravity. The robot has one if a thing goes up and down to setpoints: an **elevator** (the canonical case) or the extension stage of a **climber**. The job is "get to height *h* and stay there," so the subsystem reduces to a position controller plus a gravity feedforward. The corpus shows 17 of the 55 season-index teams with a clean `ElevatorIO` + `ElevatorIOSim` and 19 with a climber IO; an elevator doc and a climber doc would be about 85% the same.

This is the reference archetype — the other three are described as deltas against it.

### The control decision

State is **position** (meters) and its derivative **velocity** (m/s). Control is feedback on position plus a feedforward for gravity: a profiled PID drives the error to zero while a constant `kG` term holds the carriage up.

The one decision the archetype forces is **where the loop lives** — above or below the IO line:

- **Loop above the line** (recommended for a mechanism you simulate). The interface is a *device pipe*: `setVoltage(v)` plus `position()` / `velocity()` getters. The subsystem owns the single `ProfiledPIDController` and `ElevatorFeedforward`. Sim and Real run the **same** controller, so they stay in parity for free. SciBorgs (1155) builds it this way.
- **Loop below the line** (use to exploit firmware control). The interface is an *intent contract*: `runPosition(rad, ff)` / `runToHeight(h)`, and each implementation runs its own loop, typically Phoenix 6 MotionMagic on the motor. 6328 and 3636 do this. The cost: the sim impl must re-implement the loop, and the two can drift.

For a mechanism you intend to test in sim, prefer loop-above so the test exercises the controller that runs on the robot.

### The sim model

WPILib's **`ElevatorSim`** — a physics model of a gravity-loaded carriage on a motor and gearbox. It is the single reason this subsystem is testable: the sim impl wraps it, and a test steps it.

### The contract

The loop-above interface, from SciBorgs (1155), Reefscape 2025, `robot/elevator/ElevatorIO.java`:

```java
public interface ElevatorIO extends AutoCloseable {
  /** @param voltage Voltage inputted to gearbox. */
  public void setVoltage(double voltage);

  /** @return The encoder value in meters. */
  public double position();

  /** @return The encoder value in meters per second. */
  public double velocity();

  /** Resets the elevator encoder to a measurement of 0. */
  public void resetPosition();
}
```

Twelve lines, no imports at all — not even WPILib. That is the spine. The contract deliberately omits the vendor type, the game logic ("score L4"), and any other subsystem. It is only volts out and meters in. The loop-below style replaces `setVoltage` with `runPosition(positionRad, feedforward)` and adds `setPID(...)`.

When a team logs with an inputs struct instead of plain getters, the same readings appear as fields: `positionRad` / `leftHeight`, `velocityRadPerSec`, `appliedVolts`, `supplyCurrentAmps` (stall / jam detection), `tempCelsius`, and `motorConnected` (so the robot degrades safely if a motor is unplugged).

### The hardware implementation

The one file where a vendor type appears, from `robot/elevator/RealElevator.java`:

```java
import com.ctre.phoenix6.hardware.TalonFX;          // ◀ vendor import — allowed HERE, nowhere above
import com.ctre.phoenix6.controls.Follower;
// ...
public class RealElevator implements ElevatorIO {
  private final TalonFX leader   = new TalonFX(FRONT_LEADER, CANIVORE_NAME);
  private final TalonFX follower = new TalonFX(BACK_FOLLOWER, CANIVORE_NAME);

  public RealElevator() {
    follower.setControl(new Follower(FRONT_LEADER, true));
    // ...brake mode, current limit, sensor-to-mechanism ratio...
  }

  @Override public void setVoltage(double voltage) { leader.setVoltage(voltage); }
  @Override public double position() { return leader.getPosition().getValueAsDouble(); }
  @Override public double velocity() { return leader.getVelocity().getValueAsDouble(); }
  @Override public void resetPosition() { leader.setPosition(0); }
}
```

`com.ctre` lives in this file and only this file. Swapping to a SparkMax means writing one new `ElevatorIO` impl; the subsystem, the test, and the rest of the robot never know.

### The sim implementation

The same four methods, backed by physics instead of a motor, from `robot/elevator/SimElevator.java`:

```java
public class SimElevator implements ElevatorIO {
  private final ElevatorSim elevator =
      new ElevatorSim(
          LinearSystemId.createElevatorSystem(
              DCMotor.getKrakenX60(2), WEIGHT.in(Kilograms), SPROCKET_RADIUS.in(Meters), GEARING),
          DCMotor.getKrakenX60(2),
          MIN_EXTENSION.in(Meters), MAX_EXTENSION.in(Meters), true, MIN_EXTENSION.in(Meters));

  @Override public void setVoltage(double voltage) {
    elevator.setInputVoltage(voltage);
    elevator.update(Constants.PERIOD.in(Seconds));   // advance the physics one tick
  }
  @Override public double position() { return elevator.getPositionMeters(); }
  @Override public double velocity() { return elevator.getVelocityMetersPerSecond(); }
  @Override public void resetPosition() { elevator.setState(0, 0); }
}
```

Imports are WPILib only. This file is the entire reason the subsystem is testable on a laptop.

### The subsystem

The subsystem holds one `ElevatorIO`, owns the loop, and never names a motor type, from `robot/elevator/Elevator.java`:

```java
public class Elevator extends SubsystemBase implements AutoCloseable {
  private final ElevatorIO hardware;
  private final ProfiledPIDController pid = new ProfiledPIDController(kP, kI, kD, /*constraints*/);
  private final ElevatorFeedforward ff   = new ElevatorFeedforward(kS, kG, kV, kA);

  // the selection point: one place chooses the implementation
  public static Elevator create() {
    return new Elevator(Robot.isReal() ? new RealElevator() : new SimElevator());
  }
  public static Elevator none() { return new Elevator(new NoElevator()); }

  public Command goTo(double height) { return run(() -> update(height)).finallyDo(() -> hardware.setVoltage(0)); }

  private void update(double goal) {                 // the loop lives ABOVE the line
    double feedback    = pid.calculate(hardware.position(), goal);
    double feedforward = ff.calculateWithVelocities(/*...*/);
    hardware.setVoltage(feedback + feedforward);      // only volts cross down
  }
}
```

`create()` is the single selection point; `update()` is the controller both Real and Sim share.

### Variations

| Variation | Team | How it differs |
|---|---|---|
| `@AutoLog` inputs + loop below | 6328 | interface is `runPosition(rad, ff)` / `runVolts`; the TalonFX runs the position loop |
| Typed units (Kotlin) | 3636 | methods take `Distance` / `Voltage`; `runToHeight(Distance)` via MotionMagic; compile-time unit safety |
| Null object | 1155 | `NoElevator` does nothing, so the robot runs with the mechanism unplugged (`Elevator.none()`) |
| **Climber** = linear + load | 190 | same shape, simpler contract; `@AutoLog` inputs add an `isClimbed` latch |

Treat a **climber** as this archetype with three deltas: the load is one-directional (gravity always pulls the robot down once hooked), so a holding current or brake matters more than a tuned profile; many add a ratchet, so the IO exposes a `setRatchet` or the real impl ignores reverse voltage; and a `boolean isClimbed` / `atTop` input is the signal the Superstructure reads. The physics model stays `ElevatorSim` (or a coarse `DCMotorSim`).

### The testability point

Because `SimElevator` is just another `ElevatorIO`, the subsystem is unit-testable with zero hardware and zero other subsystems. This is SciBorgs' real test, from `ElevatorTest.java`:

```java
public class ElevatorTest {
  private Elevator elevator;

  @BeforeEach public void initialize() {
    setupTests();
    elevator = new Elevator(new SimElevator());   // ◀ mock the layer below
  }
  @AfterEach public void destroy() throws Exception { reset(elevator); }

  @ParameterizedTest
  @MethodSource("providePositionValues")
  public void reachesPosition(Distance height) {
    runUnitTest(elevator.goToTest(height));        // ◀ assert the layer above reaches setpoint
  }
}
```

`new Elevator(new SimElevator())` is the entire trick: construct the real subsystem against fake hardware, command a height, step the sim, assert it arrived. `goToTest(height)` returns a `Test` that runs `goTo(height)` to completion and asserts `position ≈ height` — the same routine doubles as an on-robot system check. One note on the helpers: `setupTests()`, `runUnitTest()`, `fastForward()`, and `reset()` are not WPILib — they are SciBorgs' (1155) own `TestingUtil`, a thin sim-time-stepping and assertion wrapper you build once and reuse in every test in this chapter.

One vendor-discipline caution this archetype illustrates: even SciBorgs leaks. Their `Elevator.java` carries `import com.ctre.phoenix6.SignalLogger;` to dump SysId state — a vendor type above the line in the subsystem itself. It is minor, but it is exactly the leak the corpus shows in 22 of 24 IO-layer teams. The fix is to route SysId state through a logging facade or confine `SignalLogger` to the real impl, and to enforce confinement with a checkstyle / spotless import rule rather than good intentions.

---

## Rotational position — angle plus an absolute encoder

A rotational position mechanism drives a joint to a commanded **angle** and holds it. The robot has one wherever something rotates to setpoints: an **arm** or **pivot** (a shoulder), a **wrist** (a second joint at the end of an arm), or a **turret** (continuous yaw). The job is "go to angle θ and hold" — the same shape as the elevator, with rotation in place of translation. The corpus shows 14 teams with a clean `ArmIO` + `ArmIOSim` and 13 for a pivot.

This is the elevator's twin. Two things make it harder.

### The control decision

State is **angle** (radians) and angular velocity (rad/s); control is profiled PID plus feedforward. Two differences from the linear case shape the contract:

- **Gravity is angle-dependent.** An elevator's `kG` is constant; an arm's gravity torque scales with `cos(θ)` — maximum horizontal, zero vertical. Use `ArmFeedforward` (which takes the angle), not `ElevatorFeedforward`.
- **Absolute position matters.** You cannot reliably home an arm to a hard stop. Real arms use an **absolute encoder** (a CANcoder or through-bore) so the joint knows its true angle on boot. This is the rotational subsystem's signature hardware detail.

The loop-above / loop-below decision is the same as linear, and the recommendation is the same: loop above for anything you simulate, so Sim and Real share one controller.

### The sim model

WPILib **`SingleJointedArmSim`** — a pendulum on a motor and gearbox. It needs the arm's **moment of inertia** and length, harder to estimate than an elevator's mass. A wrong MOI is the usual reason a rotational sim test will not settle.

### The contract

From SciBorgs (1155), Reefscape 2025, `robot/arm/ArmIO.java`:

```java
public interface ArmIO extends AutoCloseable {
  /** @return The position in radians. */
  public double position();
  /** @return The position in radians/sec. */
  public double velocity();
  /** Sets the voltage of the arm motor. */
  public void setVoltage(double voltage);
}
```

Three methods — smaller than the elevator's, because a rotational joint with an absolute encoder rarely needs `resetPosition()`. `position()` must read the **absolute** encoder, not a relative count. The contract omits the `TalonFX` / `CANcoder` type, the scoring-level logic, and any other subsystem. The loop-below variant replaces `setVoltage` with `setAngle(rad)` / `runSetpoint(...)`.

### The hardware implementation

The vendor type and the absolute encoder, both confined, from `robot/arm/RealArm.java`:

```java
import com.ctre.phoenix6.hardware.TalonFX;              // ◀ vendor — only here
import com.ctre.phoenix6.signals.FeedbackSensorSourceValue;
// ...
public class RealArm implements ArmIO {
  private final TalonFX leader;
  public RealArm() {
    leader = new TalonFX(ARM_PIVOT, CANIVORE_NAME);
    config.Feedback.FeedbackSensorSource = FeedbackSensorSourceValue.RemoteCANcoder; // absolute angle
    config.Feedback.FeedbackRemoteSensorID = CANCODER;
    // ...current limits, brake mode...
    leader.getConfigurator().apply(config);
  }
  @Override public double position() { return leader.getPosition().getValue().in(Radians); }
  @Override public double velocity() { return leader.getVelocity().getValue().in(RadiansPerSecond); }
  @Override public void setVoltage(double voltage) { leader.setVoltage(voltage); }
}
```

The CANcoder is used as the TalonFX's remote feedback source (`RemoteCANcoder`; `FusedCANcoder` if fused with the rotor sensor) — all of it inside the real impl, so "we switched to a through-bore on a SparkMax" is one new file. (A stray, unused `import com.revrobotics.spark.SparkMax;` lingers in this file — harmless, but exactly what an unused-import lint rule catches.)

### The sim implementation

The only line that changes from the elevator, from `robot/arm/SimArm.java`:

```java
public class SimArm implements ArmIO {
  private final SingleJointedArmSim sim =
      new SingleJointedArmSim(
          GEARBOX, GEARING, MOI, ARM_LENGTH.in(Meters),
          MIN_ANGLE.in(Radians), MAX_ANGLE.in(Radians), true, DEFAULT_ANGLE.in(Radians));

  @Override public double position() { return sim.getAngleRads(); }
  @Override public double velocity() { return sim.getVelocityRadPerSec(); }
  @Override public void setVoltage(double voltage) {
    sim.setInputVoltage(voltage);
    sim.update(Constants.PERIOD.in(Seconds));
  }
}
```

Swap `ElevatorSim` for `SingleJointedArmSim` and meters for radians; the rest of the archetype is identical. The subsystem is structurally the elevator's twin — one `ArmIO`, a `ProfiledPIDController`, a `create()` selection point, a `goToTest(angle)` system check — with one change: the feedforward is `ArmFeedforward.calculate(angleRad, velocity)` so the gravity term tracks `cos(θ)`.

### Variations

| Mechanism | Team | How it differs |
|---|---|---|
| Pivot (shoulder) | 1155 | identical to Arm; separate `PivotIO` / `RealPivot` / `SimPivot` / `NoPivot` package |
| `@AutoLog` + loop-below | 5026, 2910 | `ArmIOInputs` struct, on-motor control, `setAngle` / `runSetpoint` contract |
| Wrist (second joint) | 6328 | same archetype mounted on the arm; its zero is relative to the arm, so its feedforward needs the arm angle too |
| **Turret** (continuous yaw) | 2637, 254 | no gravity term, but angle is **continuous** — use `MathUtil.angleModulus` or a continuous-input PID so it takes the short way around |

The big split inside this archetype is gravity vs. no gravity: arm, pivot, and wrist need `ArmFeedforward`; a turret on a horizontal axis needs none but must handle wrap-around.

### The testability point

The test is the elevator's shape — construct the subsystem on `SimArm`, command angles, assert it arrives — but the rotational archetype teaches an honest caution. SciBorgs **disabled** their `ArmTest`:

```java
@Disabled // "Doesn't work :/"  ◀ honest, and instructive
public class ArmTest {
  Arm arm;
  @BeforeEach public void setup() { setupTests(); arm = Arm.create(); }

  @Test public void fullExtension() {
    runUnitTest(arm.goToTest(MIN_ANGLE));
    runUnitTest(arm.goToTest(MAX_ANGLE));
  }
  @RepeatedTest(5) public void randExtension() {
    runUnitTest(arm.goToTest(Radians.of(Math.random() * range).plus(MIN_ANGLE)));
  }
}
```

A sim test is only as good as its physics constants. An arm's moment of inertia is hard to estimate; if the MOI or `ArmFeedforward` gains are off, the sim arm overshoots or never settles inside the tolerance and the test flakes. The fix is not to delete the test but to measure MOI (from CAD or a pendulum swing) and tune the sim — at which point you have a real regression test *and* a validated feedforward. The pattern (`new Arm(new SimArm())`, command, assert) is correct; the discipline is in the constants.

Coordination — don't swing the arm into the elevator — lives in the `Superstructure`, not the arm. The arm neither knows nor cares that a wrist or an elevator exists, which is exactly why the arm package is liftable on its own.

---

## Velocity — reach a speed and hold it

A velocity mechanism spins a wheel up to a commanded **speed** and holds it while energy is drawn off — a game piece launched, a roller fed. The robot has one wherever a **flywheel** or **shooter** must reach an RPM before it acts. The job is "get to ω rad/s and stay within tolerance," so the subsystem is a velocity controller with a `kV` feedforward: no position, no gravity. The corpus shows 14 teams with a `ShooterIO` and sim, 9 with a `FlywheelIO` and sim. The single most-forked example in the corpus is the 6328 AdvantageKit flywheel template, copied verbatim into many repos including 5712's.

### The control decision

State is **angular velocity** (rad/s). Control is feedback on velocity plus a `kS` / `kV` feedforward (`SimpleMotorFeedforward`) — not `ElevatorFeedforward` or `ArmFeedforward`, because there is no gravity term. The defining property is the **"at speed" tolerance**: you act (shoot, feed) only when `|ω − ωₜ| < tolerance`, so the subsystem exposes an `atSetpoint()` or velocity reading the coordinator polls.

The control decision here is different from the position archetypes. Velocity loops run cleanly **on the motor** (Phoenix 6 `VelocityVoltage`, Spark closed-loop), so the common contract is a hybrid: the subsystem computes the **feedforward** and hands it down with the target — `setVelocity(velocityRadPerSec, ffVolts)` — and the impl runs the velocity **PID**. This is loop-below for the feedback, loop-above for the feedforward, and it keeps Sim and Real in parity because both consume the same `ffVolts`.

### The sim model

WPILib **`FlywheelSim`** — a motor driving a pure inertia (no gravity, no end stops). It models the one thing that matters here: **spin-up time**, the exponential approach to target ω set by the wheel's moment of inertia. A shooter sim that ignored this would let you "shoot" instantly; the real one makes you wait for the wheel.

### The contract

From the 6328 AdvantageKit template (here in 5712 Hemlock, `2024-Eos/.../subsystems/flywheel/FlywheelIO.java`):

```java
public interface FlywheelIO {
  @AutoLog
  public static class FlywheelIOInputs { /* velocityRadPerSec, appliedVolts, currentAmps */ }

  public default void updateInputs(FlywheelIOInputs inputs) {}
  public default void setVoltage(double volts) {}                              // open loop
  public default void setVelocity(double velocityRadPerSec, double ffVolts) {} // closed loop
  public default void stop() {}
  public default void configurePID(double kP, double kI, double kD) {}
}
```

`setVoltage` exists for open-loop spin-up and characterization; `setVelocity` carries the closed-loop target plus the subsystem-supplied feedforward; `configurePID` pushes gains down because the velocity loop runs on the motor. The inputs struct carries the controlled variable:

```java
@AutoLog
public static class FlywheelIOInputs {
  public double positionRad = 0.0;
  public double velocityRadPerSec = 0.0;   // ◀ the controlled variable
  public double appliedVolts = 0.0;
  public double[] currentAmps = new double[] {};
}
```

The contract omits the motor type, "is a note loaded," and any pivot or hood angle — that is a separate rotational subsystem.

### The sim implementation

The sim models spin-up by running the same velocity PID the real motor would, from `FlywheelIOSim.java`:

```java
public class FlywheelIOSim implements FlywheelIO {
  private FlywheelSim sim =
      new FlywheelSim(
          LinearSystemId.createFlywheelSystem(DCMotor.getNEO(1), 0.004, 1.5), // MOI, gearing
          DCMotor.getNEO(1));
  private PIDController pid = new PIDController(0.0, 0.0, 0.0);
  private boolean closedLoop = false;
  private double ffVolts = 0.0;
  private double appliedVolts = 0.0;

  @Override public void updateInputs(FlywheelIOInputs inputs) {
    if (closedLoop) {
      appliedVolts = MathUtil.clamp(pid.calculate(sim.getAngularVelocityRadPerSec()) + ffVolts, -12, 12);
      sim.setInputVoltage(appliedVolts);
    }
    sim.update(0.02);                                   // advance the inertia one tick
    inputs.velocityRadPerSec = sim.getAngularVelocityRadPerSec();
    inputs.appliedVolts = appliedVolts;
  }
  @Override public void setVelocity(double velocityRadPerSec, double ffVolts) {
    closedLoop = true; pid.setSetpoint(velocityRadPerSec); this.ffVolts = ffVolts;
  }
  // setVoltage(), stop(), configurePID() ...
}
```

The sim is fed the same `ffVolts` the subsystem computes, so a shooter that "gets to speed" in sim gets to speed on the robot. (5712's 2024 source builds the sim with the pre-2025 `FlywheelSim(gearbox, gearing, MOI)` constructor, which WPILib 2025 removed; the `LinearSystemId.createFlywheelSystem` form above is the current equivalent.)

### The subsystem

The subsystem owns the feedforward and treats sim as a separate robot with its own tuning, from `Flywheel.java`:

```java
public class Flywheel extends SubsystemBase {
  private final FlywheelIO io;
  private final FlywheelIOInputsAutoLogged inputs = new FlywheelIOInputsAutoLogged();
  private final SimpleMotorFeedforward ffModel;

  public Flywheel(FlywheelIO io) {
    this.io = io;
    switch (Constants.currentMode) {           // ◀ different feedforward gains per mode
      case REAL, REPLAY -> { ffModel = new SimpleMotorFeedforward(0.1, 0.05); io.configurePID(1.0,0,0); }
      case SIM          -> { ffModel = new SimpleMotorFeedforward(0.0, 0.03); io.configurePID(0.5,0,0); }
      default           -> ffModel = new SimpleMotorFeedforward(0.0, 0.0);   // the final field must be assigned on every path
    }
  }
  @Override public void periodic() { io.updateInputs(inputs); Logger.processInputs("Flywheel", inputs); }

  public void runVelocity(double velocityRPM) {
    var radPerSec = Units.rotationsPerMinuteToRadiansPerSecond(velocityRPM);
    io.setVelocity(radPerSec, ffModel.calculate(radPerSec));   // subsystem owns the feedforward
  }
  @AutoLogOutput public double getVelocityRPM() { return Units.radiansPerSecondToRotationsPerMinute(inputs.velocityRadPerSec); }
}
```

The source comment puts it well: the physics simulator is treated as a separate robot with different tuning. Sim and Real are two implementations behind one contract, each with its own constants, both exercised by the same code.

### Variations

| Variation | Team | How it differs |
|---|---|---|
| Shooter = flywheel + hood/feeder | 2637 | `ShooterIO` for the wheels, a separate rotational `PivotIO` / hood, a `FeederIO` roller; a `Shooting` command coordinates them |
| Plain-getter velocity | 1155 | no inputs struct; `ShooterIO` exposes `setVoltage` + `velocity()`, subsystem runs the PID above the line |
| Dual-wheel / spin | many | top and bottom (or left and right) wheels at different speeds for backspin — two `setVelocity` targets |

The recurring design point: a "shooter" is usually **three** archetypes — a velocity flywheel (this section), a rotational hood or pivot, and a roller feeder. Keep them as separate subsystems behind separate IO contracts and let a command compose them; don't fuse them into one class.

### The testability point

The velocity test asserts the wheel reaches and holds a commanded speed within tolerance — the RPM analog of the elevator reaching a height. SciBorgs' shooting test, abridged from `ShootingTest.java`:

```java
@BeforeEach public void setup() {
  setupTests();
  shooter = Shooter.create();  pivot = Pivot.create();  feeder = Feeder.create();  drive = Drive.create();
  shooting = new Shooting(shooter, pivot, feeder, drive);   // ◀ whole flow, all on sim
}

@ParameterizedTest @ValueSource(doubles = {200, 300, 350, 400, 500, 540})
public void shootSysCheck(double v) { runUnitTest(shooter.goToTest(RadiansPerSecond.of(v))); }

@ParameterizedTest @ValueSource(doubles = {-200, -100, 0, 100, 200})
public void testShootStoredNote(double vel) {
  run(shooting.shoot(RadiansPerSecond.of(vel)));
  fastForward();
  assertEquals(vel, shooter.rotationalVelocity(), VELOCITY_TOLERANCE.in(RadiansPerSecond)); // ◀ at speed?
}
```

`shootSysCheck` is the per-subsystem velocity check. `testShootStoredNote` is the larger prize: it constructs **four subsystems on sim and the command that coordinates them**, then asserts the end state. Because every subsystem mocks its hardware below, a whole behavior is testable with no robot — which works only if none of the four imports another. The composition lives in the `Shooting` command, not inside the shooter. That is the library rule paying off across subsystems.

The vendor leak to watch here: teams reach for a `TalonFX` velocity API in the subsystem to "just set the RPM." Keep the subsystem in rad/s and `ffVolts`; let the `*IOTalonFX` impl translate to a `VelocityVoltage` request.

---

## Roller / game-piece — the actuator is trivial, the sensor is the point

A roller subsystem moves a game piece *through* the robot: an **intake** pulls it in, an **indexer** or **feeder** moves it to the shooter, a **manipulator** or **claw** holds or ejects it. The actuation is trivial — run a wheel at a voltage. The defining part is the **sensor that answers "do we have it?"** — a beam-break, a distance sensor, or motor-stall current. A roller subsystem is less about control and more about detecting state transitions: empty → holding → ejected. It is the most common subsystem family in the corpus (18 teams with a clean `IntakeIO` + sim).

### The control decision

Actuation is open-loop **voltage** (`run(+6V)` / `stop`) or a simple velocity; a `DCMotorSim` suffices, with no position to hold and no gravity. The **state** is the game-piece sensor, and the subsystem's real job is to expose it (`hasGamePiece()`) so commands can do "intake **until** we have a piece, then stop."

Two sub-shapes:

- **Fixed roller** (indexer, feeder, fixed intake): one motor plus a sensor. Pure this archetype.
- **Deploying intake**: a roller plus a pivot that lowers and raises it — this archetype fused with the rotational one. The IO carries both `setRollerVoltage` and `setPivotPosition`. Keep them in one IO only if they are one mechanism.

### The sim model

WPILib **`DCMotorSim`** for the roller (and pivot). But the model that *matters* is the **sensor**: to test "intake until we have a piece," the sim impl must be able to report the beam-break as tripped on command. Most teams skip this, which is why rollers are the least-tested archetype.

### The contract

6328 noticed every roller is the same and extracted a base, so the intake is a one-line tag, from `RobotCode2024Public/.../subsystems/rollers/intake/IntakeIO.java`:

```java
public interface IntakeIO extends GenericRollerSystemIO {}
```

`GenericRollerSystemIO` carries `updateInputs` + `runVolts` + `stop`; `Intake`, `Feeder`, and `Indexer` are all `GenericRollerSystem`s differing only by constants. This is "generalize after the third copy" applied to the most-repeated subsystem.

The richer case carries both archetypes plus the sensor, from 3476 Code Orange, `Godzilla-ReefScapeOffseason/.../subsystems/intake/IntakeIO.java`:

```java
public interface IntakeIO {
  @AutoLog
  class IntakeIOInputs {
    public PivotData pivotData;        // the deploy joint (a rotational mechanism)
    public RollerData rollerData;      // the wheel
    public CanRangeData canRangeData;  // the game-piece sensor
  }
  default void setPivotVoltage(double voltage) {}
  default void setRollerVoltage(double voltage) {}
  default void setPivotPosition(double positionRotations) {}
  default boolean checkRollerStalled() { return false; }   // backup "have piece" via current
}
```

`setPivotPosition` is the rotational mechanism riding alongside the roller. The sensor crosses the IO line as a plain input. 3476 models it as a CANRange distance sensor with a `tripped` flag, plus a stall check as backup:

```java
record RollerData(boolean isMotorConnected, double voltage, double supplyCurrent,
                  double statorCurrent, double temperature, double velocityRPS) {}
record CanRangeData(boolean isSensorConnected, boolean tripped,   // ◀ "do we have a piece?"
                    double signalStrength, double distanceMeters) {}
```

Other teams use a `boolean beamBroken` (digital beam-break) or `checkRollerStalled()` (a current spike when a piece jams the wheel). Whatever the hardware, the sensor crosses the line as a boolean or double input, so sim can fake it. The contract omits the motor type, "should we be intaking right now," and the shooter.

### The sim implementation

`DCMotorSim` for the physics, with a vendor nuance worth noting, from 3476's `IntakeIOSim.java`:

```java
import com.ctre.phoenix6.sim.TalonFXSimState;   // ◀ a vendor type — allowed, this is BELOW the line
import edu.wpi.first.wpilibj.simulation.DCMotorSim;

public class IntakeIOSim extends IntakeIOReal {
  protected DCMotorSim rollerSim, pivotSim;
  // a Notifier ticks the DCMotorSim at 200 Hz; the TalonFXSimState feeds applied voltage back in
  // so the *real* TalonFX control code runs against simulated physics.
}
```

The nuance: this sim impl imports `com.ctre.phoenix6.sim`, and that is fine. Both `IOReal` and `IOSim` are *below* the line, so a vendor type is allowed in either. 3476 uses CTRE's sim-state (the controller simulates itself, high fidelity, tied to CTRE); SciBorgs keeps `SimElevator` pure WPILib (more portable). Both are valid — the rule is "no vendor *above* the line," not "no vendor in sim."

### Variations

| Variation | Team | How it differs |
|---|---|---|
| Generic roller base | 6328 | one `GenericRollerSystemIO` shared by intake / feeder / indexer |
| Roller + pivot + CANRange | 3476 | deploying intake; distance sensor `tripped` is the have-piece flag |
| Stall-current detection | 3476, many | no beam-break — `checkRollerStalled()` infers a held piece from current |
| Indexer / Feeder | 2637, 1155 | fixed roller + a beam-break; no pivot — the purest form of this archetype |
| Manipulator / Claw | 3636, 3061 | a roller or a servo-gripper that holds; "have piece" via a sensor or position |

### The testability point

This archetype teaches an uncomfortable truth. SciBorgs — the corpus testing leader — tests its elevator and shooter with real behavior assertions, but its `IntakeTest` is only a construction smoke-test:

```java
public class IntakeTest {
  @Test public void init() throws Exception {
    Intake.create().close();   // ◀ a construction smoke-test, no behavior asserted
    reset();
  }
}
```

Why? Because the interesting behavior — "run the roller until the beam-break trips, then stop" — needs the sensor simulated, and faking a beam-break is more work than wrapping a `DCMotorSim`. So teams test that the subsystem constructs and stop there.

The fix is small and high-value: make the game-piece sensor a plain IO input (a `boolean beamBroken` in the inputs struct) and give `IntakeIOSim` a way to set it. Then the real test becomes possible:

```java
// the test this archetype should have:
var intake = new Intake(simIO);
run(intake.intakeUntilHeld());     // command runs the roller
simIO.setBeamBroken(true);         // fake the piece arriving
fastForward();
assert intake.hasGamePiece();      // and assert the command reacted
```

That is the whole payoff of putting the sensor behind the IO line instead of reading a `DigitalInput` directly in the subsystem. The leak to watch: reading a WPILib `DigitalInput` beam-break in the subsystem is fine, but reading a CTRE CANrange or a SparkMax limit switch in the subsystem is a vendor leak — route it through the inputs struct.

---

## Reading the four together

The four archetypes are one seam drawn for four control types. The contract changes only in what crosses the line and which WPILib model backs the fake hardware:

| Archetype | Controlled variable | Feedforward | Sim model | The testability hinge |
|---|---|---|---|---|
| Linear position | height (m) | `ElevatorFeedforward` (constant `kG`) | `ElevatorSim` | command a height, assert it arrives |
| Rotational position | angle (rad) | `ArmFeedforward` (`cos θ`) | `SingleJointedArmSim` | same shape; depends on a measured MOI |
| Velocity | speed (rad/s) | `SimpleMotorFeedforward` (`kV`) | `FlywheelSim` | reaches and holds ω within tolerance |
| Roller / game-piece | open-loop voltage | none | `DCMotorSim` + faked sensor | react to a simulated sensor trip |

The decisions repeat too. Where does the loop live — above the line (Sim and Real share one controller, recommended for anything you test) or below (exploit firmware control, accept drift)? What does the sensor cross the line as (a getter, an inputs-struct field)? And in every case: the vendor type stays in the `*IO<device>` or `*IOSim` file, never above it.

Read a team's code and the archetype tells you what to expect: an `ElevatorSim` in the sim impl, an absolute encoder fused below the line in an arm, a `setVelocity(ω, ffVolts)` hybrid for a flywheel, a `boolean tripped` input on an intake. When those are present and confined, the subsystem can be tested in isolation and lifted out as a library. When the vendor type or a sibling import has crept above the line, it cannot — and that is the marker the rubric rewards.

---

Next: [19. The drivetrain subsystem](19-the-drivetrain-subsystem.md) — the special case with two interfaces (module and gyro), swerve kinematics, and a sim model of its own.
