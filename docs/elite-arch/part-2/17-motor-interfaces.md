---
title: 17. Motor interfaces
weight: 17
---

# 17. Motor interfaces

*Part I drew the IO seam at the subsystem: one `ElevatorIO` per mechanism, vendor types sealed inside the implementation. This chapter goes one level lower, to the device. It surveys how teams in the corpus actually talk to motors in code — the reusable `MotorIO` contracts six teams build, the design axes they disagree on, and the rarer idea of capability-typed devices where an interface is named for what it does, not the brand that does it. It is the prior art on which Part III will build a single portable motor interface.*

Code is quoted to study the technique, not to copy.

This is a deep dive supporting [Part I ch.5, the IO seam](../part-1/03-the-io-seam.md). That chapter established the rule: a subsystem speaks mechanism semantics (`setHeight(m)`), and the vendor type (`TalonFX`, `SparkMax`) lives only inside the IO implementation. Here we look at what happens *below* that line — at the device-level abstractions a handful of teams build to talk to motors directly.

Two questions drive the chapter. First, the corpus survey: how do FRC teams interact with motors in code, and what does the abstraction look like when they build a reusable one? Second, the alternative: the capability-typed-devices idea, which appeared in [Part I's alternatives entry](../part-1/08-alternatives.md) and is shown here in full — interfaces named by capability (`PositionMotor`, not `ITalonMotor`), a single hardware object that constructs and configures every device, and FOC modeled as an orthogonal opt-in.

Part III will propose a single portable motor interface distilled from this evidence; see [Part III](../part-3/) generally. This chapter is the history that proposal answers to.

## The landscape underneath

Motor hardware in the corpus is near-universal CTRE plus REV, and most teams run both vendors at once.

| Vendor type | Teams (of 63) | Notes |
|---|---|---|
| CTRE Phoenix 6 (`com.ctre.phoenix6`, `TalonFX`) | 52 | the modern default |
| CTRE Phoenix 5 (`com.ctre.phoenix.*`, legacy) | 51 | mostly older repos / Talon SRX |
| REV (`com.revrobotics`, `SparkMax`/`SparkFlex`) | 49 | NEO ecosystem |
| `TalonSRX` | 32 | legacy brushed/CIM |
| `SparkFlex` / `CANSparkFlex` | 25 | NEO Vortex |
| `ThriftyNova` | 2 | the long tail |

The dominant call idioms, corpus-wide:

- **`.set(...)`** — 8,626 occurrences. The legacy/duty-cycle setter (Phoenix 5, REV).
- **`.setControl(request)`** — 2,620 occurrences. The Phoenix 6 idiom: build a request object (`VoltageOut`, `MotionMagicVoltage`, `PositionVoltage`, `TorqueCurrentFOC`, and so on) and hand it to the motor.

Every motor abstraction in this chapter is, at bottom, a wrapper around `.setControl(request)`. A second number frames the alternative discussed later: WPILib's shared `MotorController` interface is imported by 23 teams but called only 47 times total, against `setControl` (CTRE) 797 times and `setReference` (REV) 301 times. Teams program the vendor's own control model, not a shared one.

## The spectrum of motor access

There are two populations, and the gap between them is the whole point.

| Tier | Pattern | Teams |
|---|---|---|
| Raw | Vendor type (`TalonFX`/`SparkMax`) instantiated directly inside `subsystems/` | 53 |
| Partial IO | Some `*IO.java` interface exists (AdvantageKit-style) | 27 |
| ↳ with sim impl | A `*IOSim.java` is present | 18 |
| ↳ with logged inputs | `@AutoLog` / `*IOInputs` struct present | 23 |
| Reusable `MotorIO` | A motor-generic IO reused across mechanisms | 6 |

The 53-team raw majority treat the subsystem as the motor wrapper: the vendor object is a field, gear-ratio math is inline, and there is no seam where a simulated or replayed motor could be substituted. The six teams in the bottom row — 254, 1678, 971, 2910, 2706, 5137 — instead define one motor contract and implement it once per device family (`...TalonFX`, `...Sim`, `...SparkMax`). That single decision is what lets simulation, unit tests, and log replay attach later for free.

The rest of this chapter reads those six contracts in full, then turns to the capability-typed variant.

## The six reusable contracts

Read these as six answers to the same design brief. They cluster on a few axes, covered after, but the surface area is worth seeing first.

### 254 Cheesy Poofs

A lean pure `interface`. Mechanism-unit `double`s on the hot path; one `int slot` for PID gain sets; `default` methods cascade the overloads down to one fully-specified primitive. The companion `MotorInputs` is a flat `@AutoLog` struct.

```java
public interface MotorIO {
    void readInputs(MotorInputs inputs);

    void setOpenLoopDutyCycle(double dutyCycle);

    // These are in the "units" of the subsystem (rad, m).
    void setPositionSetpoint(double units);

    default void setMotionMagicSetpoint(double units) {
        setMotionMagicSetpoint(units, 0);
    }
    void setMotionMagicSetpoint(double units, int slot);
    default void setMotionMagicSetpoint(
            double units, double velocity, double acceleration, double jerk) {
        setMotionMagicSetpoint(units, velocity, acceleration, jerk, 0);
    }
    // ... cascades to the fully-specified primitive ...
    void setMotionMagicSetpoint(
            double units, double velocity, double acceleration,
            double jerk, int slot, double feedforward);

    void setNeutralMode(NeutralModeValue mode);

    default void setVelocitySetpoint(double unitsPerSecond) {
        setVelocitySetpoint(unitsPerSecond, 0);
    }
    void setVelocitySetpoint(double unitsPerSecond, int slot);

    void setVoltageOutput(double voltage);

    void setCurrentPositionAsZero();
    void setCurrentPosition(double positionUnits);

    void setEnableSoftLimits(boolean forward, boolean reverse);
    void setEnableHardLimits(boolean forward, boolean reverse);

    void follow(CANDeviceId masterId, boolean opposeMasterDirection);

    void setTorqueCurrentFOC(double current);

    void setMotionMagicConfig(MotionMagicConfigs config);
    void setVoltageConfig(VoltageConfigs config);
}
```

```java
@AutoLog
public class MotorInputs {
    public double velocityUnitsPerSecond = 0.0;
    public double unitPosition = 0.0;
    public double appliedVolts = 0.0;
    public double currentStatorAmps = 0.0;
    public double currentSupplyAmps = 0.0;
    public double rawRotorPosition = 0.0;
}
```

Note `setNeutralMode(NeutralModeValue mode)` and the `MotionMagicConfigs` / `VoltageConfigs` parameters: this is a clean command surface that still leaks CTRE config types in its signatures. Hold that thought for the alternatives section.

### 2910 Jack in the Bot

Closest sibling to 254, with two telling differences. The `@AutoLog` inputs class is nested inside the interface, and it splits state into motor-frame (`motorRaw…`, rotor-relative) versus mechanism-frame (`mechanismRaw…`, post-ratio) — so logs show both the raw rotor and the geared output. Almost every method is a `default {}` no-op, making partial implementations legal: a roller impl never overrides the position methods. It also leaks two vendor getters, `getTalon()` and `getConfig()`.

```java
public interface MotorIO {

    @AutoLog
    class MotorIOInputs {
        public boolean connected = false;

        // talon.getRotor...() — motor-frame, independent of ratios
        public double motorRawPositionRotations = 0.0;
        public double motorVelocityRPS = 0.0;
        public double motorVoltage = 0.0;
        public double motorStatorCurrentAmps = 0.0;
        public double motorSupplyCurrentAmps = 0.0;
        public double motorTemperatureC = 0.0;

        // talon.get...() — mechanism-frame, after the ratios
        public double mechanismRawPositionInMechanismUnits = 0.0;
        public double mechanismVelocityPerSecondInMechanismUnits = 0.0;
    }

    void updateInputs(MotorIOInputs inputs);

    BaseMotorConfig getConfig();
    TalonFX getTalon();
    double getMotorRotationsToMechanismUnitsRatio();

    default void setNeutralMode(NeutralModeValue mode) {}
    default void setTorqueCurrentFOC(double current) {}
    default void setOpenLoopDutyCycle(double dutyCycle) {}
    default void setVoltageOutput(double voltage) {}
    default void follow(CanDeviceId leaderID, MotorAlignmentValue motorAlignment) {}

    default void setMechanismPositionSetpoint(double mechanismPosition) {}
    default void setMechanismPositionSetpoint(double mechanismPosition, int slot) {}
    default void setEncoderPositionAsZero() {}

    default void setMechanismVelocityPerSecondSetpoint(double mechanismVelocity) {}

    default void setMotionMagicSetpoint(double mechanismPosition, int slot) {}
    default void setMotionMagicSetpoint(double mechanismPosition, double velocity,
            double acceleration, double jerk) {
        setMotionMagicSetpoint(mechanismPosition, velocity, acceleration, jerk, 0);
    }
    // ... cascades ...
    default void setMotionMagicConfig(MotionMagicConfigs config) {}
}
```

The motor-frame / mechanism-frame split is the distinctive idea here: when a log shows a position glitch you can tell whether the rotor or the gearbox math is at fault.

### 971 Spartan Robotics

The minimalist, type-safe answer. An `abstract class`, not an interface, using WPILib `Units` measure types (`Voltage`, `Angle`, `AngularVelocity`, `Distance`) so a unit mismatch is a compile error. Note the deliberate `Angle` versus `Distance` overloads of `setPosition` / `resetPosition` — the same contract serves rotational and linear mechanisms. Telemetry is not a separate struct: Lombok `@Getter` plus AdvantageKit `@AutoLogOutput` fields publish state directly, and a concrete `periodic()` logs the converted values.

```java
public abstract class MotorIO {
  protected final String name;

  @Getter protected final MotorConfig motorConfig;

  @Getter @AutoLogOutput(key = "{name}/Applied Voltage") protected Voltage appliedVoltage;
  @Getter @AutoLogOutput(key = "{name}/Supply Current")  protected Current supplyCurrent;
  @Getter @AutoLogOutput(key = "{name}/Stator Current")  protected Current statorCurrent;
  @Getter @AutoLogOutput(key = "{name}/Temperature")     protected Temperature temperature;
  @Getter @AutoLogOutput(key = "{name}/Connected")       protected boolean connected = false;

  @Getter protected Angle position = Rotations.of(0.0);
  @Getter protected AngularVelocity velocity = RotationsPerSecond.of(0.0);

  public void periodic() {
    Logger.recordOutput(name + "/Position", UnitUtil.toDouble(position, motorConfig.LOG_UNIT()));
    Logger.recordOutput(name + "/Velocity",
        UnitUtil.toDouble(velocity, motorConfig.LOG_UNIT().per(Seconds)));
  }

  public abstract void setVoltage(Voltage goalVoltage);
  public abstract void setVelocity(AngularVelocity goalVelocity);
  public abstract void setPosition(Angle goalPosition);
  public abstract void setPositionVoltage(Angle goalPosition);
  public abstract void setPosition(Distance goalPosition);       // elevators
  public abstract void setPositionVoltage(Distance goalPosition);
  public abstract void resetPosition(Angle newPosition);
  public abstract void resetPosition(Distance newPosition);
  public abstract void setCoast();
}
```

This is the smallest surface of the six. Every method is `abstract`, so every implementation must satisfy the whole contract — no `default {}` escape hatch and no silent no-op.

### 2706 PhantomCatz

A generic interface parameterized over its inputs type (`<T extends MotorIOInputs>`), so each subsystem can extend the inputs struct. Distinctive choices: the inputs use arrays (`appliedVolts[]`, `tempCelcius[]`) to log a leader plus its followers in one struct; it exposes `getSignals()` so the robot can batch-refresh all status signals with one CTRE `BaseStatusSignal.refreshAll(...)`; and it carries an explicit `enable()` / `disable()` / `stop()` lifecycle. Setters are documented as applied only through Setpoints — the control mode is chosen by a higher-level object, not called directly. Gains and motion-magic params are settable at runtime.

```java
public interface GenericMotorIO<T extends GenericMotorIO.MotorIOInputs> {

  public static class MotorIOInputs {
    public boolean isLeaderConnected = false;
    public boolean[] isFollowerConnected = new boolean[] {};

    public double position = 0.0;          // latency-compensated
    public double velocityRPS = 0.0;
    public double[] appliedVolts = new double[] {};
    public double[] supplyCurrentAmps = new double[] {};
    public double[] torqueCurrentAmps = new double[] {};
    public double[] tempCelcius = new double[] {};
  }

  public default void updateInputs(T inputs) {}
  public default void setCurrentPosition(double mechanismPosition) {}
  public default BaseStatusSignal[] getSignals() { return new BaseStatusSignal[0]; }
  public default void zeroSensors() {}
  public default void setNeutralBrake(boolean wantsBrake) {}

  // Applied only through Setpoints:
  public default void setNeutralSetpoint() {}
  public default void setVoltageSetpoint(double voltage) {}
  public default void setMotionMagicSetpoint(double mechanismPosition) {}
  public default void setVelocityFOCSetpoint(double mechanismVelocity) {}
  public default void setDutyCycleSetpoint(double percent) {}
  public default void setPositionSetpoint(double mechanismPosition) {}

  public default void enable() {}
  public default void disable() {}
  public default void stop() {}

  public default void setGainsSlot0(double p, double i, double d,
      double s, double v, double a, double g) {}
  public default void setMotionMagicParameters(double velocity,
      double acceleration, double jerk) {}

  public default void setNeutralMode(TalonFX fx, NeutralModeValue neutralMode) {}
  public default void setNeutralMode(TalonFXS fx, NeutralModeValue neutralMode) {}
}
```

The follower-array inputs and `getSignals()` batching are oriented at the CAN-bus cost of refreshing many status signals each loop. The trailing `setNeutralMode(TalonFX, …)` overloads, taking the vendor type as an argument, are the clearest leak in this interface.

### 5137 Iron Kodiaks

The maximal, fully-instrumented contract — a concrete base class with the richest inputs struct in the corpus. It carries control-loop introspection (`error`, `propOutput`, `derivOutput`, `intOutput`, `feedforward`), faults, limit flags, and `encoderDiff` for encoder-fusion debugging. Two ideas worth studying. First, every optional method defaults to `unsupportedFeature()`, which raises a dashboard `Alert` rather than failing silently, so commanding an unsupported mode is visible at the driver station. Second, it owns `Alert`s for disconnect, hardware-fault, over-temp, and limits, refreshing them in `update()`.

```java
public class MotorIO {

    @AutoLog
    public static class MotorIOInputs {
        public boolean connected;

        // Mechanism values: arms/flywheels use rad & rad/s; elevators use m & m/s
        public double position;
        public double velocity;
        public double accel;

        public double appliedVoltage;
        public double supplyCurrent;
        public double torqueCurrent;

        public String controlMode;        // DutyCycle, Voltage, MotionMagic, ...

        public double setpoint;
        public double error;               // target - position
        public double feedforward;
        public double derivOutput;         // kD contribution
        public double intOutput;           // kI contribution
        public double propOutput;          // kP contribution

        public double temp;
        public double encoderDiff;         // encoder vs motor, for sync visualization

        public boolean hitForwardLimit;
        public boolean hitReverseLimit;
        public boolean hardwareFault;
        public boolean tempFault;
    }

    public void update() {
        Logger.processInputs(logPath, inputs);
        disconnectAlert.set(!inputs.connected);
        hardwareFaultAlert.set(inputs.hardwareFault);
        tempFaultAlert.set(inputs.tempFault);
        forwardLimitAlert.set(inputs.hitForwardLimit);
        reverseLimitAlert.set(inputs.hitReverseLimit);
    }

    private void unsupportedFeature() {
        if (Constants.currentMode != Mode.REPLAY)
            Alerts.create("An unsupported feature was used on " + getName(), AlertType.kWarning);
    }

    // ---- Open-loop ----
    public void setDutyCycle(double value)      { unsupportedFeature(); }
    public void setVoltage(double volts)        { unsupportedFeature(); }
    public void setTorqueCurrent(double current){ unsupportedFeature(); }

    // ---- Closed-loop position (Motion Magic & direct), current- or voltage-based ----
    public void setGoalWithCurrentMagic(double goal) { unsupportedFeature(); }
    public void setGoalWithVoltageMagic(double goal) { unsupportedFeature(); }
    public void setVelocityWithCurrent(double velocity) { unsupportedFeature(); }
    public void setVelocityWithVoltage(double velocity) { unsupportedFeature(); }

    // ---- Gains (individual + whole-slot) ----
    public void setkP(double kP) { unsupportedFeature(); }
    public void setkD(double kD) { unsupportedFeature(); }
    public void setGains(Slot0Configs gains) { unsupportedFeature(); }

    // ---- Encoder fusion & zeroing ----
    public void connectEncoder(EncoderIO encoder, double motorToSensorRatio, boolean fuse) { unsupportedFeature(); }
    public void setPosition(double position) { unsupportedFeature(); }

    // ---- Simulation-only ----
    public void setMechPosition(double position) { unsupportedFeature(); }
    public void disconnect() { unsupportedFeature(); }
}
```

The `unsupportedFeature()` pattern is the inverse of 971's all-`abstract` choice: instead of forcing every impl to satisfy the whole contract, it lets impls skip what they cannot do, and surfaces the gap as a runtime alert when something calls the missing method. The `Slot0Configs gains` parameter is again a CTRE type in the signature.

### 1678 Citrus Circuits

The most architecturally ambitious of the six: an `abstract class implements Sendable` (778 lines) where control is reified as an immutable `Setpoint` value object. Subsystems never call `setVelocitySetpoint` directly — those are `protected`. Instead they build a `Setpoint` (`Setpoint.withMotionMagicSetpoint(angle)`, `withVelocitySetpointAndCurrentLimit(v, …)`) and call `applySetpoint(setpoint)`. The base class owns an `enabled` flag, the reapply-last-setpoint-on-enable behavior, a `Mode` enum classifying control types, units baked into the instance, multi-follower input tracking, and full `Sendable` dashboard wiring.

```java
public abstract class MotorIO implements Sendable {
    public final AngleUnit unitType;
    public final TimeUnit time;
    protected final Inputs inputs;
    protected final Inputs[] followerInputs;
    private Setpoint setpoint = Setpoint.withNeutralSetpoint();
    private boolean enabled = true;

    public abstract void updateInputs();
    public abstract void setCurrentPosition(Angle mechanismPosition);
    public abstract void zeroSensors();
    public abstract void setNeutralBrake(boolean wantsBrake);
    public abstract TalonFXConfiguration getMotorIOConfig();
    public abstract void useSoftLimits(boolean enable);

    // protected — only invoked via a Setpoint's applier:
    protected abstract void setNeutralSetpoint();
    protected abstract void setVoltageSetpoint(Voltage voltage);
    protected abstract void setMotionMagicSetpoint(Angle mechanismPosition, int slot);
    protected abstract void setVelocitySetpoint(AngularVelocity mechanismVelocity, int slot);
    protected abstract void setDutyCycleSetpoint(Dimensionless percent);
    protected abstract void setPositionSetpoint(Angle mechanismPosition, int slot);

    // --- concrete lifecycle: the heart of the design ---
    public final void applySetpoint(Setpoint setpointToApply) {
        setpoint = setpointToApply;
        if (enabled) setpointToApply.apply(this);
    }
    public final void enable()  { enabled = true;  setpoint.apply(this); }
    public final void disable() { enabled = false; Setpoint.withNeutralSetpoint().apply(this); }
}
```

The control-mode classifier and the reified setpoint:

```java
public enum Mode {
    IDLE, VOLTAGE, MOTIONMAGIC, VELOCITY, DUTY_CYCLE, POSITIONPID;
    public boolean isPositionControl() { /* MOTIONMAGIC, POSITIONPID */ }
    public boolean isVelocityControl() { /* VELOCITY */ }
}

public static class Setpoint {
    private final UnaryOperator<MotorIO> applier;   // how to push this onto the IO
    public final Mode mode;
    public final double baseUnits;                   // target, in WPILib base units

    static Setpoint withNeutralSetpoint();
    static Setpoint withVoltageSetpoint(Voltage v);
    static Setpoint withMotionMagicSetpoint(Angle p);
    static Setpoint withMotionMagicSetpointAndCurrentLimit(Angle p, Current maxStator, Current maxSupply);
    static Setpoint withVelocitySetpoint(AngularVelocity v);
    static Setpoint withVelocitySetpointAndCurrentLimit(AngularVelocity v, Current maxStator, Current maxSupply);
    static Setpoint withCustomSetpoint(UnaryOperator<MotorIO> applier, Mode mode, double baseUnits);

    public void apply(MotorIO io) { applier.apply(io); }
}
```

The `…AndCurrentLimit` / `…AndVoltageLimit` factories mutate the `TalonFXConfiguration` in place before applying the setpoint — the setpoint can carry a transient config change, for example "go to this position but cap stator at 40 A." That is the most powerful idea in the six, and the hardest to retrofit. The cost is the matching one: `getMotorIOConfig()` returns a `TalonFXConfiguration`, so CTRE's config type is baked into the abstract base.

## The design axes they disagree on

The six cluster on a handful of decisions. Reading across them is more useful than any one in isolation.

| Axis | Lean (254, 2910, 5137) | Type-safe (971, 1678) |
|---|---|---|
| Form | `interface` (254, 2910, 2706) | `abstract class` (971, 1678, 5137) |
| Units | raw `double`, mechanism units by convention | WPILib `Units` (`Angle`, `Voltage`, …), compile-checked |
| Control entry | direct setters (`setVoltageOutput`, `setVelocitySetpoint`) | reified `Setpoint` value object (1678, 2706) |
| Inputs | flat `@AutoLog` struct (254, 5137, 2706, 2910) | `@AutoLogOutput` fields + `periodic()` (971) |
| Optional methods | `default {}` no-op (2910, 2706) or `unsupportedFeature()` alert (5137) | `abstract` — every impl must satisfy (254, 971, 1678) |
| Motor vs mechanism frame | mostly mechanism-only; 2910 logs both | mechanism-frame (gear math in impl) |
| Followers | `follow(id, oppose)` call | `followerInputs[]` array + per-follower logging (1678, 2706) |
| Slots | `int slot` parameter for multiple gain sets (254, 2910, 2706) | per-`Setpoint` (1678) |

Several themes are stable across all six.

**What crosses the line.** The command surface is mostly clean — mechanism-unit doubles or WPILib measure types in, no `StatusSignal` out. But config crosses in every one of them: `MotionMagicConfigs` and `VoltageConfigs` (254), `BaseMotorConfig` and `getTalon()` (2910), `Slot0Configs` (5137), `TalonFXConfiguration` (1678), and `setNeutralMode(TalonFX, …)` (2706). Commands abstract well; configuration resists.

**Loop placement.** Every contract assumes the control loop runs on the motor controller, not the roboRIO. The verbs are `setMotionMagicSetpoint`, `setPositionSetpoint`, `setVelocityFOCSetpoint` — they hand a target plus gains to the device and let its onboard PID close the loop. None of the six runs a software PID across the seam.

**Units.** Two camps: raw `double` in mechanism units by convention (254, 2910, 2706, 5137), or WPILib `Units` measure types that make a unit mismatch a compile error (971, 1678). The convention camp is terser; the type camp catches the rad-versus-rotation bug at build time.

**Config versus command.** The cleanest split is 1678's, where a `Setpoint` is the only way to command, and config-changing setpoints (`…AndCurrentLimit`) are a distinct, named subset. The looser designs mix runtime config setters (`setGainsSlot0`, `setMotionMagicParameters`) into the same flat surface as the commands.

**Capability tiers.** Designs handle "this motor cannot do that" three ways: make everything `abstract` so every impl is complete (971, 1678, 254); make everything a `default {}` no-op so partial impls are legal and silent (2910, 2706); or default to `unsupportedFeature()` so a missing method raises a visible alert (5137).

The consensus telemetry, present in nearly every inputs struct: `connected`, `position`, `velocity`, `appliedVolts`, `statorCurrent`, `supplyCurrent`, `tempCelsius`, `rawRotorPosition`. The consensus command verbs: open-loop (duty cycle, voltage, torque-current FOC); closed-loop (position PID, profiled position via Motion Magic, velocity — each with an optional gain slot and feedforward); neutral (brake / coast); config (gains, motion constraints, current limits, soft limits); sensor (zero, set-current-position, encoder fusion); topology (follow); and sim hooks (force position/velocity, force-disconnect).

## Capability-typed devices

The six contracts above abstract "a motor" — one interface, many control modes, and config types leaking through. The alternative seen in [Part I's alternatives entry](../part-1/08-alternatives.md) abstracts a **role** instead. It is shown here in full because it is the cleanest answer to the leak the survey exposes.

The rule that makes it work: the interface name describes a capability the caller depends on, not the hardware that provides it.

- Avoid `ITalonMotor`, `ICTREFOCMotor`, `SparkPositionMotor` — vendor leaks into the name; callers couple to a brand.
- Prefer `PositionMotor`, `VelocityMotor`, `TorqueMotor` — named for what you ask of them.

Split by capability rather than building one universal `Motor` god-interface. A device implements the set of role interfaces it can honor.

```java
public enum NeutralMode { BRAKE, COAST }      // a neutral concept, not NeutralModeValue / IdleMode

/** A motor you command to a mechanism position. Units are mechanism units (rad/m), not rotor rotations. */
public interface PositionMotor {
    void   setPosition(double positionRad);    // go to / hold
    double getPositionRad();
    double getVelocityRadPerSec();
    void   setVoltage(double volts);           // open-loop escape hatch
    void   setNeutralMode(NeutralMode mode);
}

/** A motor you command to a speed. */
public interface VelocityMotor {
    void   setVelocity(double radPerSec);
    double getVelocityRadPerSec();
    void   setVoltage(double volts);
    void   setNeutralMode(NeutralMode mode);
}
```

Two non-negotiables: signatures speak mechanism units and neutral enums. The moment a `NeutralModeValue`, a `Rotation`, or a `StatusSignal` appears in the interface, the abstraction has failed and you have renamed a `TalonFX`. This is exactly the config-leak the six corpus contracts all show; here the rule is enforced by keeping config out of the signature entirely.

### FOC as an orthogonal opt-in

FOC is an efficiency optimization — "do the same job, better" — so it should be optional and orthogonal, not baked into the control interface. The design splits it into two distinct concepts.

The efficiency aspect becomes an optional mix-in capability. It changes how well the job is done, not what you command, so it is a separate interface a device implements only if it has it:

```java
/** Opt-in efficiency mode (e.g. FOC). Absent where unsupported — query, don't assume. */
public interface EfficiencyOptimizable {
    void setEfficiencyOptimization(boolean enabled);
}
```

A caller writes `if (motor instanceof EfficiencyOptimizable o) o.setEfficiencyOptimization(true);`. A motor that cannot do it does not implement the interface — capability presence lives in the type system, not a runtime flag that silently lies.

The torque-control aspect is a different verb, not an optimization, so it is its own role interface:

```java
public interface TorqueMotor {            // CTRE FOC today; whoever ships it tomorrow
    void setTorqueCurrent(double amps);
}
```

Today only CTRE implements `TorqueMotor` and `EfficiencyOptimizable`. Abstracting over one implementation is cheap and forward-looking: when a second vendor ships FOC, you add an implementation and no caller changes.

### Vendor types live in the impl, fully

Below the interface, each impl talks to its device in the device's native language and uses its best features:

```java
final class TalonFXPositionMotor
        implements PositionMotor, VelocityMotor, TorqueMotor, EfficiencyOptimizable {

    private final TalonFX talon;                                  // vendor type, below the line
    private final MotionMagicVoltage posReq = new MotionMagicVoltage(0).withEnableFOC(true);
    private final double rotToRad;

    TalonFXPositionMotor(CanDeviceId id, MotorSpec spec) {        // declarative config in
        this.talon = TalonFXFactory.create(id, spec);            // applies + verifies config
        this.rotToRad = spec.mechanismRotationsToRadians();
    }
    public void setPosition(double rad) {
        talon.setControl(posReq.withPosition(rad / rotToRad));    // Motion Magic + FOC
    }
    public void setTorqueCurrent(double amps) { talon.setControl(new TorqueCurrentFOC(amps)); }
    public void setEfficiencyOptimization(boolean on) { posReq.EnableFOC = on; }
}

final class SparkMaxPositionMotor implements PositionMotor {      // NO FOC → offers fewer interfaces
    private final SparkMax spark;
    // MAXMotion config baked in; setPosition → getClosedLoopController().setReference(...)
}

final class SimPositionMotor implements PositionMotor {           // physics plant, no vendor at all
    private final ElevatorSim plant; /* ... */
}
```

`SparkMaxPositionMotor` implements only `PositionMotor` — it does not pretend to be a `TorqueMotor`. The interface set a device offers is its honest capability advertisement. No lowest-common-denominator flattening, no emulation that lies.

### The hardware object

One object assembles the robot's devices. It is the factory and the configuration home, and it exposes each device through its capability interface:

```java
final class Hardware {                          // one per robot variant (comp / practice / sim)
    private final RobotConfig cfg;              // per-robot CAN IDs, ratios, limits

    PositionMotor elevator()  { return new TalonFXPositionMotor(cfg.elevator().id(),  cfg.elevator().spec()); }
    VelocityMotor leftDrive() { return new TalonFXPositionMotor(cfg.leftDrive().id(), cfg.leftDrive().spec()); }
    GyroSource    gyro()      { return new Pigeon2Gyro(cfg.gyro().id()); }
}
```

The subsystem receives only the interface, injected — never the concrete type, and never `Hardware` itself:

```java
class Elevator extends SubsystemBase {
    private final PositionMotor motor;
    Elevator(PositionMotor motor) { this.motor = motor; }   // depends on a capability, not a vendor
    public Command toHeight(double m) { return run(() -> motor.setPosition(m / DRUM_RADIUS)); }
}
```

That detail is the line between this and the old `RobotMap` anti-pattern: the subsystem depends on `PositionMotor`, a thing it can fully exercise, not on a god-object it has to reach through. The hardware object also is the run-mode switch — one place decides what every interface resolves to:

```java
static Hardware create(RobotMode mode, RobotConfig cfg) {
    return switch (mode) {
        case REAL   -> new RealHardware(cfg);     // TalonFX / SparkMax impls
        case SIM    -> new SimHardware(cfg);      // SimPositionMotor, etc.
        case REPLAY -> new ReplayHardware(cfg);   // log-fed impls
    };
}
```

This is the "one place to configure simulation" benefit, achieved without a shared hardware god-object and without any vendor type crossing into a subsystem.

### The corpus reality check

The clean form is rare. Measured across the season repos: a device-level motor abstraction shows up in roughly 10 teams — the `MotorIO` interface in 254 and 2910; the `MotorIO` class in 1678, 5137, and 971; and a `Motor` type in 971, 2412, 4099, 4504, 5026, and 4738. But almost all of them leak vendor types, as the survey above showed in detail: 254's `MotorIO` imports `com.ctre.phoenix6` `MotionMagicConfigs` and `NeutralModeValue`. The vendor-clean, capability-segregated form described here is the rare case — which is why it is an alternative, not the default.

The supporting infrastructure, though, is common: configured-device factories such as `TalonFXFactory` (6 teams including 254, 1678, 3061), `PhoenixUtil` (8 teams), and `CTREConfigs` (7 teams). That is the layer this pattern sits on — the `TalonFXFactory.create(id, spec)` call inside the impl above.

## When the lower seam pays, and when it is over-engineering

Reach for capability-typed devices when:

- You have several mechanically-similar mechanisms — elevator plus arm plus wrist all reduce to "one motor, position control" — and want to share one implementation and one `SimPositionMotor` across all of them.
- You run multiple physical robots, or anticipate a vendor change, and want the swap to be a new impl rather than a subsystem rewrite.
- You want the FOC decision expressed once, in the type system, rather than re-litigated at each call site.

Do not, when:

- You are single-vendor with a handful of mechanisms. The per-subsystem `XxxIO` seam from Part I is less machinery for the same sim/test/replay payoff.
- You would be abstracting capabilities you do not actually command. Speculative generality is the failure mode here — build `PositionMotor` because your arm needs it, not a universal motor API on spec.

The honest costs are three. You still write a new impl per vendor — the abstraction protects callers, not the impl author. The neutral-spec-to-vendor-config mapper is ongoing maintenance as vendordeps evolve. And it is slightly contrarian to Part I, which draws the boundary at the subsystem. Both are valid; the lower seam trades more device-level machinery for cross-mechanism reuse and a clean cross-vendor future. They compose: capability-typed devices can live inside subsystem IO impls.

Writing your own motor class is sensible when it is an interface on top of a vendor device, named for a capability, with the configuration for one purpose wired in. Split it by role, model FOC as an orthogonal opt-in, let each device advertise its real capability set through the interfaces it implements, and let one hardware object construct, configure, and inject them as narrow references. Vendor names stay out of every signature; vendor code stays sealed inside the impls. Part III takes this evidence and proposes one portable interface built on it.

## Related chapters

- [15. The control path](15-control-path.md)
- [16. Hardware abstraction](16-hardware-abstraction.md)
- [18. Subsystem archetypes](18-subsystem-archetypes.md)
- [19. The drivetrain subsystem](19-the-drivetrain-subsystem.md)
- [20. The world model](20-the-world-model.md)
- [21. Vision systems](21-vision-systems.md)
- [22. Coordination: state machines](22-coordination-state-machines.md)
- [23. Coordination: graphs and trees](23-coordination-graphs-trees.md)

Next: [18. Subsystem archetypes](18-subsystem-archetypes.md)
