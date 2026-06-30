# Motor IO Interfaces Across the Corpus — Survey of Other Teams

*Source: direct reading of `/Volumes/Cache/frc_team_repos` (63 teams, 25,395 Java
files, seasons 2022–2026). Counts are teams-with-at-least-one-match unless noted.
Cross-checked against the tree-sitter `data/code-index.duckdb` index (63 teams, 684
repos, 629,632 symbols, 279,746 parsed imports); vendor counts here are the
parsed-import figures, and the six reusable-`MotorIO` teams are confirmed exactly.*

This document answers a single question: **how do FRC teams interact with motors in
code, and what does the abstraction look like when they build one?** It surveys the
hardware landscape, shows the *full* motor-IO interfaces of the six teams that build a
reusable one, and dissects the design axes they disagree on.

> **This is the analysis of *everybody else's* motor interfaces — the prior art.**
> *Our own* design (the contract we distilled from this survey, recast as a
> language-neutral, ROS-translatable specification) is its own document:
> [../specs/portable-motor-interface.md](../specs/portable-motor-interface.md).
> The two are a pair: this one is the history, that one is ours.

---

## 1. The landscape: what's underneath

Motor *hardware* is near-universal CTRE + REV, and most teams run both vendors at once.

| Vendor type | Teams (of 63) | Notes |
|---|---|---|
| CTRE Phoenix 6 (`com.ctre.phoenix6`, `TalonFX`) | **52** | the modern default |
| CTRE Phoenix 5 (`com.ctre.phoenix.*`, legacy) | 51 | mostly older repos / Talon SRX |
| REV (`com.revrobotics`, `SparkMax`/`SparkFlex`) | 49 | NEO ecosystem |
| `TalonSRX` | 32 | legacy brushed/CIM |
| `SparkFlex` / `CANSparkFlex` | 25 | NEO Vortex |
| `ThriftyNova` | 2 | the long tail |

The dominant *call* idioms, corpus-wide:

- **`.set(...)`** — 8,626 occurrences. The legacy/duty-cycle setter (Phoenix 5, REV).
- **`.setControl(request)`** — 2,620 occurrences. The Phoenix 6 idiom: build a request
  object (`VoltageOut`, `MotionMagicVoltage`, `PositionVoltage`, `TorqueCurrentFOC`, …)
  and hand it to the motor. **Every motor abstraction in this document is, at bottom, a
  wrapper around `.setControl(request)`.**

## 2. The spectrum: how teams *structure* motor access

There are two populations, and the gap between them is the entire point of the build-spec.

| Tier | Pattern | Teams |
|---|---|---|
| **Raw** | Vendor type (`TalonFX`/`SparkMax`) instantiated directly inside `subsystems/` | **53** |
| **Partial IO** | Some `*IO.java` interface exists (AdvantageKit-style) | 27 |
| ↳ with sim impl | A `*IOSim.java` is present | 18 |
| ↳ with logged inputs | `@AutoLog` / `*IOInputs` struct present | 23 |
| **Reusable `MotorIO`** | A *motor-generic* IO reused across mechanisms | **6** |

The 53-team "raw" majority treat the subsystem *as* the motor wrapper: the vendor object
is a field, gear-ratio math is inline, and there is no seam where a simulated or replayed
motor could be substituted. The six teams in the bottom row — **254, 1678, 971, 2910,
2706, 5137** — instead define one motor contract and implement it once per device family
(`...TalonFX`, `...Sim`, `...SparkMax`). That single decision is what makes simulation
(D3), unit tests (D4), and log replay (D5) attach *for free* later. See also
[`03-io-layer-strategy-pattern.md`](03-io-layer-strategy-pattern.md).

---

## 3. The six reusable contracts, in full

Read these as six answers to the same design brief. They cluster on a few axes — covered
in §4 — but it's worth seeing the actual surface area first.

### 3.1 — 254 Cheesy Poofs (`com.team254.lib.subsystems.MotorIO`)

A lean pure `interface`. Mechanism-unit `double`s on the hot path; one `int slot` for PID
gain sets; `default` methods cascade the overloads down to one fully-specified primitive.
The companion `MotorInputs` is a flat `@AutoLog` struct.

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
    default void setMotionMagicSetpoint(
            double units, double velocity, double acceleration, double jerk, int slot) {
        setMotionMagicSetpoint(units, velocity, acceleration, jerk, slot, 0.0);
    }
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
    void setEnableAutosetPositionValue(boolean forward, boolean reverse);

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

### 3.2 — 2910 Jack in the Bot (`...subsystems.base.MotorIO`)

Closest sibling to 254, with two telling differences: the `@AutoLog` inputs class is
*nested* inside the interface, and it splits state into **motor-frame** (`motorRaw…`,
rotor-relative) vs **mechanism-frame** (`mechanismRaw…`, post-ratio) — so logs can show
both the raw rotor and the geared output. Almost every method is a `default {}` no-op,
making partial implementations legal (a roller impl simply never overrides the position
methods). It also leaks two vendor getters (`getTalon()`, `getConfig()`).

```java
public interface MotorIO {

    @AutoLog
    class MotorIOInputs {
        public String mechanismEndUnit = "David Units";
        public boolean connected = false;

        // talon.getRotor...() — motor-frame, independent of ratios
        public double motorRawPositionRotations = 0.0;
        public double motorVelocityRPS = 0.0;
        public double motorAccelerationRotationsPerSecondPerSecond = 0.0;
        public double motorVoltage = 0.0;
        public double motorStatorCurrentAmps = 0.0;
        public double motorSupplyCurrentAmps = 0.0;
        public double motorTemperatureC = 0.0;

        // talon.get...() — mechanism-frame, after rotorToSensor & sensorToMechanism ratios
        public double mechanismRawPositionInMechanismUnits = 0.0;
        public double mechanismVelocityPerSecondInMechanismUnits = 0.0;
        public double mechanismAccelerationPerSecondPerSecondInMechanismUnits = 0.0;
    }

    void updateInputs(MotorIOInputs inputs);

    BaseMotorConfig getConfig();
    TalonFX getTalon();
    double getMotorRotationsToMechanismUnitsRatio();

    default void setNeutralMode(NeutralModeValue mode) {}
    default void setEnableSoftLimits(boolean forward, boolean reverse) {}
    default void setEnableHardLimits(boolean forward, boolean reverse) {}
    default void setEnableAutosetPositionValue(boolean forward, boolean reverse) {}
    default void setTorqueCurrentFOC(double current) {}

    default void setOpenLoopDutyCycle(double dutyCycle) {}
    default void setVoltageOutput(double voltage) {}
    default void follow(CanDeviceId leaderID, MotorAlignmentValue motorAlignment) {}
    default void setVoltageConfig(VoltageConfigs config) {}

    default void setMechanismPositionSetpoint(double mechanismPosition) {}
    default void setMechanismPositionSetpoint(double mechanismPosition, int slot) {}
    default void setEncoderPositionAsZero() {}
    default void setEncoderPositionInMechanismUnits(double mechanismPosition) {}

    default void setMechanismVelocityPerSecondSetpoint(double mechanismVelocity) {}
    default void setMechanismVelocityPerSecondSetpoint(double mechanismVelocity, int slot) {}

    default void setMotionMagicSetpoint(double mechanismPosition, int slot) {}
    default void setMotionMagicSetpoint(double mechanismPosition, double velocity,
            double acceleration, double jerk) {
        setMotionMagicSetpoint(mechanismPosition, velocity, acceleration, jerk, 0);
    }
    default void setMotionMagicSetpoint(double mechanismPosition, double velocity,
            double acceleration, double jerk, int slot) {
        setMotionMagicSetpoint(mechanismPosition, velocity, acceleration, jerk, slot, 0.0);
    }
    default void setMotionMagicSetpoint(double mechanismPosition, double velocity,
            double acceleration, double jerk, int slot, double feedforward) {}
    default void setMotionMagicConfig(MotionMagicConfigs config) {}
}
```

### 3.3 — 971 Spartan Robotics (`...lib.superstructure.MotorIO`)

The minimalist, **type-safe** answer. An `abstract class` (not interface) using WPILib
**`Units`** measure types (`Voltage`, `Angle`, `AngularVelocity`, `Distance`) so a
unit mismatch is a *compile error*. Note the deliberate `Angle` vs `Distance` overloads of
`setPosition`/`resetPosition` — the same contract serves rotational and linear mechanisms.
Telemetry is not a separate struct: Lombok `@Getter` + AdvantageKit `@AutoLogOutput`
fields publish state directly, and a concrete `periodic()` logs the converted values.

```java
public abstract class MotorIO {
  protected final String name;

  @Getter protected final MotorConfig motorConfig;
  @Getter protected Optional<CANcoderConfig> cancoderConfig = Optional.empty();

  @Getter @AutoLogOutput(key = "{name}/Applied Voltage") protected Voltage appliedVoltage;
  @Getter @AutoLogOutput(key = "{name}/Supply Current")  protected Current supplyCurrent;
  @Getter @AutoLogOutput(key = "{name}/Stator Current")  protected Current statorCurrent;
  @Getter @AutoLogOutput(key = "{name}/Temperature")     protected Temperature temperature;
  @Getter @AutoLogOutput(key = "{name}/Connected")       protected boolean connected = false;

  @Getter protected Angle absolutePosition = Rotations.of(0.0);
  @Getter protected Angle position = Rotations.of(0.0);
  @Getter protected AngularVelocity velocity = RotationsPerSecond.of(0.0);

  /* Custom feedforward added to the position request */
  @Getter @Setter @AutoLogOutput(key = "{name}/Feedforward Voltage")
  protected Voltage feedforward = Volts.of(0.0);

  MotorIO(MotorConfig config) {
    this.motorConfig = config;
    this.name = config.NAME();
  }

  public void periodic() {
    Logger.recordOutput(name + "/Position", UnitUtil.toDouble(position, motorConfig.LOG_UNIT()));
    Logger.recordOutput(name + "/Absolute Position",
        UnitUtil.toDouble(absolutePosition, motorConfig.LOG_UNIT()));
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

### 3.4 — 2706 PhantomCatz (`...CatzAbstractions.io.GenericMotorIO<T>`)

A **generic** interface parameterized over its inputs type (`<T extends MotorIOInputs>`),
so each subsystem can extend the inputs struct. Distinctive choices: the inputs use
**arrays** (`appliedVolts[]`, `tempCelcius[]`) to log a leader *plus* its followers in one
struct; it exposes `getSignals()` so the robot can batch-refresh all status signals with
one CTRE `BaseStatusSignal.refreshAll(...)`; and it carries an explicit
`enable()/disable()/stop()` lifecycle. Setters are documented as "only applied through
Setpoints" — the control mode is chosen by a higher-level Setpoint object, not called
directly. Gains and motion-magic params are settable at runtime.

```java
public interface GenericMotorIO<T extends GenericMotorIO.MotorIOInputs> {

  public static class MotorIOInputs {
    public boolean isLeaderConnected = false;
    public boolean[] isFollowerConnected = new boolean[] {};

    public double position = 0.0;          // latency-compensated
    public double velocityRPS = 0.0;
    public double accelerationRPS = 0.0;
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
  public default void setSoftLimitsEnabled(boolean forward, boolean reverse) {}

  // Applied only through Setpoints:
  public default void setNeutralSetpoint() {}
  public default void setCoastSetpoint() {}
  public default void setVoltageSetpoint(double voltage) {}
  public default void setMotionMagicSetpoint(double mechanismPosition) {}
  public default void setVelocityFOCSetpoint(double mechanismVelocity) {}
  public default void setVelocitySetpointVoltage(double mechanismVelocity) {}
  public default void setDutyCycleSetpoint(double percent) {}
  public default void setPositionSetpoint(double mechanismPosition) {}

  public default void enable() {}
  public default void disable() {}
  public default void stop() {}

  public default void setGainsSlot0(double p, double i, double d,
      double s, double v, double a, double g) {}
  public default void setGainsSlot1(double p, double i, double d,
      double s, double v, double a, double g) {}
  public default void setMotionMagicParameters(double velocity,
      double acceleration, double jerk) {}

  public default void setNeutralMode(TalonFX fx, NeutralModeValue neutralMode) {}
  public default void setNeutralMode(TalonFXS fx, NeutralModeValue neutralMode) {}
}
```

### 3.5 — 5137 Iron Kodiaks (`frc.robot.io.MotorIO`)

The **maximal, fully-instrumented** contract — a concrete base class with the richest
inputs struct in the corpus (control-loop introspection: `error`, `propOutput`,
`derivOutput`, `intOutput`, `feedforward`; faults; limit flags; `encoderDiff` for
encoder-fusion debugging). Two ideas worth stealing: (1) every optional method defaults to
`unsupportedFeature()`, which raises a **dashboard `Alert`** rather than failing silently,
so commanding an unsupported mode is visible at the driver station; (2) it owns
`Alert`s for disconnect / hardware-fault / over-temp / limits and refreshes them in
`update()`. It also exposes encoder fusion (`connectEncoder`), continuous wrap, gravity-FF
type, and explicit sim-only hooks (`setMechPosition`, `disconnect`).

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
        public double supplyVoltage;
        public double supplyCurrent;
        public double torqueCurrent;

        public String controlMode;        // DutyCycle, Voltage, MotionMagic, ...

        public double setpoint;
        public double setpointVelocity;
        public double error;               // target - position
        public double feedforward;
        public double derivOutput;         // kD contribution
        public double intOutput;           // kI contribution
        public double propOutput;          // kP contribution

        public double temp;
        public double dutyCycle;
        public double encoderDiff;         // encoder vs motor, for sync visualization

        public boolean hitForwardLimit;
        public boolean hitReverseLimit;
        public boolean hardwareFault;
        public boolean tempFault;

        public double rawRotorPosition;
    }

    // ... constructor wires Alerts for disconnect / fault / temp / limits ...

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
    public MotorIOInputs getInputs() { return inputs; }

    // ---- Open-loop ----
    public void setDutyCycle(double value)      { unsupportedFeature(); }
    public void setVoltage(double volts)        { unsupportedFeature(); }
    public void setTorqueCurrent(double current){ unsupportedFeature(); }

    // ---- Closed-loop position (Motion Magic & direct), current- or voltage-based ----
    public void setGoalWithCurrentMagic(double goal, Supplier<Double> feedforward) { unsupportedFeature(); }
    public void setGoalWithCurrentMagic(double goal) { setGoalWithCurrentMagic(goal, null); }
    public void setGoalWithVoltageMagic(double goal) { unsupportedFeature(); }
    public void setVelocityWithCurrentMagic(double velocity) { unsupportedFeature(); }
    public void setVelocityWithVoltageMagic(double velocity) { unsupportedFeature(); }
    public void setGoalWithCurrent(double goal) { unsupportedFeature(); }
    public void setGoalWithVoltage(double goal) { unsupportedFeature(); }
    public void setVelocityWithCurrent(double velocity) { unsupportedFeature(); }
    public void setVelocityWithVoltage(double velocity) { unsupportedFeature(); }

    // ---- Neutral / follow / invert ----
    public void coast()   { unsupportedFeature(); }
    public void brake()   { unsupportedFeature(); }
    public void neutral() { unsupportedFeature(); }
    public void setBraking(boolean braking) { unsupportedFeature(); }
    public void follow(int motorId, boolean invert) { unsupportedFeature(); }
    public void setInverted(boolean inverted) { unsupportedFeature(); }

    // ---- Gains (individual + whole-slot) ----
    public void setkP(double kP) { unsupportedFeature(); }
    public void setkI(double kI) { unsupportedFeature(); }
    public void setkD(double kD) { unsupportedFeature(); }
    public void setkG(double kG) { unsupportedFeature(); }
    public void setkS(double kS) { unsupportedFeature(); }
    public void setkV(double kV) { unsupportedFeature(); }
    public void setkA(double kA) { unsupportedFeature(); }
    public void setGains(Slot0Configs gains) { unsupportedFeature(); }

    // ---- Limit switches & motion constraints ----
    public void connectForwardLimitSwitch(BitIO limitSwitch) { unsupportedFeature(); }
    public void connectReverseLimitSwitch(BitIO limitSwitch) { unsupportedFeature(); }
    public void setMaxVelocity(double maxVelocity) { unsupportedFeature(); }
    public void setMaxAccel(double maxAccel) { unsupportedFeature(); }
    public void setMaxJerk(double maxJerk) { unsupportedFeature(); }
    public void setContinuousWrap(boolean wrap) { unsupportedFeature(); }
    public void setFeedforwardType(GravityTypeValue type) { unsupportedFeature(); }
    public void setStaticFeedforwardType(StaticFeedforwardSignValue type) { unsupportedFeature(); }

    // ---- Encoder fusion & zeroing ----
    public void connectEncoder(EncoderIO encoder, double motorToSensorRatio, boolean fuse) { unsupportedFeature(); }
    public void connectEncoder(EncoderIO encoder, double motorToSensorRatio) { connectEncoder(encoder, motorToSensorRatio, true); }
    public void connectInternalSensor(double gearRatio) { unsupportedFeature(); }
    public void setOffset(double offset) { unsupportedFeature(); }
    public void setPosition(double position) { unsupportedFeature(); }

    // ---- Current limits & soft limits ----
    public void setStatorCurrentLimit(double a)        { unsupportedFeature(); }
    public void setSupplyCurrentLimit(double a)        { unsupportedFeature(); }
    public void setSupplyCurrentLowerLimit(double a)   { unsupportedFeature(); }
    public void setSupplyCurrentLowerTime(double s)    { unsupportedFeature(); }
    public void setLimits(double min, double max)      { unsupportedFeature(); }

    public void clearStickyFaults() { unsupportedFeature(); }
    public void setDisabled(boolean disabled) { unsupportedFeature(); }

    // ---- Simulation-only ----
    public void setMechPosition(double position) { unsupportedFeature(); }
    public void setMechVelocity(double velocity) { unsupportedFeature(); }
    public void disconnect() { unsupportedFeature(); }
}
```

### 3.6 — 1678 Citrus Circuits (`frc.lib.io.MotorIO`)

The most *architecturally* ambitious: an `abstract class implements Sendable` (778 lines)
where control is **reified as an immutable `Setpoint` value object**. Subsystems never call
`setVelocitySetpoint` directly — those are `protected`. Instead they build a `Setpoint`
(`Setpoint.withMotionMagicSetpoint(angle)`, `withVelocitySetpointAndCurrentLimit(v, …)`,
etc.) and call `applySetpoint(setpoint)`. The base class then owns: an `enabled` flag, the
"reapply last setpoint on enable" behavior, a `Mode` enum classifying control types, units
(`AngleUnit`/`TimeUnit`) baked into the instance, multi-follower input tracking, and full
`Sendable` dashboard wiring. Uses WPILib `Units` types throughout.

The core abstract contract (subclasses implement the device specifics):

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
    public abstract boolean getConfigFailed();
    public abstract void useSoftLimits(boolean enable);

    // protected — only invoked via a Setpoint's applier:
    protected abstract void setNeutralSetpoint();
    protected abstract void setCoastSetpoint();
    protected abstract void setVoltageSetpoint(Voltage voltage);
    protected abstract void setMotionMagicSetpoint(Angle mechanismPosition, int slot);
    protected abstract void setMotionMagicSetpoint(Angle mechanismPosition);
    protected abstract void setVelocitySetpoint(AngularVelocity mechanismVelocity, int slot);
    protected abstract void setVelocitySetpoint(AngularVelocity mechanismVelocity);
    protected abstract void setDutyCycleSetpoint(Dimensionless percent);
    protected abstract void setPositionSetpoint(Angle mechanismPosition, int slot);
    protected abstract void setPositionSetpoint(Angle mechanismPosition);

    public abstract void setMainConfig(TalonFXConfiguration configuration);
    public abstract void changeMainConfig(UnaryOperator<TalonFXConfiguration> configChanger);
    public abstract void changeFollowerConfig(UnaryOperator<TalonFXConfiguration> configChanger);

    // --- concrete lifecycle: the heart of the design ---
    public final void applySetpoint(Setpoint setpointToApply) {
        setpoint = setpointToApply;
        if (enabled) setpointToApply.apply(this);
    }
    public final void enable()  { enabled = true;  setpoint.apply(this); }
    public final void disable() { enabled = false; Setpoint.withNeutralSetpoint().apply(this); }
    public boolean getEnabled() { return enabled; }
    public abstract void disabledPeriodic();

    // last-read accessors: getVelocity(), getPosition(), getStatorCurrent(),
    // getSupplyCurrent(), getMotorVoltage(), getSetpoint(), getSetpointDoubleInUnits()
}
```

The control-mode classifier and the reified setpoint:

```java
public enum Mode {
    IDLE, VOLTAGE, MOTIONMAGIC, VELOCITY, DUTY_CYCLE, POSITIONPID;
    public boolean isPositionControl() { /* MOTIONMAGIC, POSITIONPID */ }
    public boolean isVelocityControl() { /* VELOCITY */ }
    public boolean isNeutralControl()  { /* IDLE */ }
    public boolean isVoltageControl()  { /* VOLTAGE, DUTY_CYCLE */ }
}

public static class Setpoint {
    private final UnaryOperator<MotorIO> applier;   // how to push this onto the IO
    public final Mode mode;
    public final double baseUnits;                   // target, in WPILib base units

    // Factory surface (each returns an immutable Setpoint):
    static Setpoint withNeutralSetpoint();
    static Setpoint withCoastSetpoint();
    static Setpoint withVoltageSetpoint(Voltage v);
    static Setpoint withDutyCycleSetpoint(Dimensionless pct);
    static Setpoint withPositionSetpoint(Angle p);                 // + (Angle, int slot)
    static Setpoint withMotionMagicSetpoint(Angle p);             // + (Angle, int slot)
    static Setpoint withMotionMagicSetpointAndCurrentLimit(Angle p, Current maxStator, Current maxSupply);
    static Setpoint withVelocitySetpoint(AngularVelocity v);      // + (…, int slot)
    static Setpoint withVelocitySetpointAndCurrentLimit(AngularVelocity v, Current maxStator, Current maxSupply);
    static Setpoint withVelocitySetpointAndVoltageLimit(AngularVelocity v, Voltage peakFwd, Voltage peakRev);
    static Setpoint withCustomSetpoint(UnaryOperator<MotorIO> applier, Mode mode, double baseUnits);

    public void apply(MotorIO io) { applier.apply(io); }
}
```

The `…AndCurrentLimit` / `…AndVoltageLimit` factories mutate the `TalonFXConfiguration`
in place before applying the setpoint — i.e. the *setpoint* can carry a transient config
change (e.g. "go to this position but cap stator at 40 A"). That is the single most
powerful idea in the six, and the hardest to retrofit.

---

## 4. The design axes they disagree on

| Axis | Lean (254, 2910, 5137*) | Type-safe (971, 1678) |
|---|---|---|
| **Form** | `interface` (254, 2910, 2706) | `abstract class` (971, 1678, 5137) |
| **Units** | raw `double`, mechanism units by convention | WPILib `Units` (`Angle`, `Voltage`, …), compile-checked |
| **Control entry** | direct setters (`setVoltageOutput`, `setVelocitySetpoint`) | reified `Setpoint`/value object (1678, 2706) |
| **Inputs** | flat `@AutoLog` struct (254, 5137, 2706, 2910) | `@AutoLogOutput` fields + `periodic()` (971) |
| **Optional methods** | `default {}` no-op (2910, 2706) or `unsupportedFeature()`-alert (5137) | `abstract` — every impl must satisfy (254, 971, 1678) |
| **Motor vs mechanism frame** | mostly mechanism-only; 2910 logs both | mechanism-frame (gear math in impl) |
| **Followers** | `follow(id, oppose)` call | `followerInputs[]` array + per-follower logging (1678, 2706) |
| **Slots** | `int slot` parameter for multiple gain sets (254, 2910, 2706) | per-`Setpoint` (1678) |

Recurring **inputs** fields (the consensus telemetry): `connected`, `position`,
`velocity`, `appliedVolts`, `statorCurrent`, `supplyCurrent`, `tempCelsius`,
`rawRotorPosition`. Richer impls add: `acceleration`, `torqueCurrent`, control-loop
introspection (`error`, `setpoint`, P/I/D contributions — 5137), limit flags, fault flags.

Recurring **control** verbs (the consensus command surface):
- **open-loop:** duty cycle, voltage, torque-current FOC
- **closed-loop:** position (PID), profiled position (Motion Magic), velocity — each with
  an optional gain `slot` and an optional arbitrary feedforward
- **neutral:** brake / coast (and "neutral" = the configured default)
- **config:** gains, motion constraints (vel/accel/jerk), current limits, soft limits,
  continuous wrap, gravity-FF type, invert
- **sensor:** zero, set-current-position, encoder fusion + ratio, offset
- **topology:** follow(leader, oppose)
- **sim:** force mechanism position/velocity, force-disconnect

---

## 5. Appendix — file locations (corpus)

| Team | File |
|---|---|
| 254 | `254-cheesy-poofs/2025/FRC-2025-Public/src/main/java/com/team254/lib/subsystems/MotorIO.java` |
| 1678 | `1678-citrus-circuits/2026/C2026-Public/src/main/java/frc/lib/io/MotorIO.java` |
| 971 | `971-spartan-robotics/2026/971-second-robot-2026/src/main/java/frc/robot/lib/superstructure/MotorIO.java` |
| 2910 | `2910-jack-in-the-bot/2026/2026CompetitionRobot-Public/src/main/java/org/frc2910/robot/subsystems/base/MotorIO.java` |
| 2706 | `2706-phantomcatz/2026/RobotCode2026-Rebuilt/SeasonCode2026/.../CatzAbstractions/io/GenericMotorIO.java` |
| 5137 | `5137-iron-kodiaks/2026/2026-season/src/main/java/frc/robot/io/MotorIO.java` |
