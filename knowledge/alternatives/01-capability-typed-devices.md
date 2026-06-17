# Capability-Typed Devices and the Hardware Object

*A device-level seam that lives **below** the IO line: vendor devices behind interfaces named for what
they **do**, assembled by one hardware object. An alternative to the build spec's subsystem-level
`XxxIO` seam — and, properly guard-railed, composable with it.*

## Where this sits relative to the build spec

`build-spec/elite-architecture.md` draws the honest abstraction boundary at the **subsystem**: one
`ElevatorIO` interface per mechanism, with `ElevatorIOTalonFX` / `ElevatorIOSim` implementations. The
subsystem speaks in mechanism semantics (`setHeight(m)`); vendor types live inside the IO impl. That is
the recommended default and it is right for most teams.

This document describes a **second, lower seam**: abstracting the *device itself* — a motor, an encoder —
behind an interface named for a capability the caller depends on. It is not a replacement for the
subsystem IO seam; it can live *inside* IO impls, or (for simple mechanisms) it can *be* the seam. It earns
its keep when you have several mechanically-similar mechanisms to share an implementation across, or a
genuine need to outlive a single vendor.

> **Corpus reality check** (measured across the season repos in `data/code-index.duckdb`). The *shared*
> vendor interface barely exists: WPILib's `MotorController` is imported by 23 teams and called **47×
> total**, against `setControl` (CTRE) **797×** and `setReference` (REV) **301×** — everyone programs the
> vendor's own control model. A *device-level* motor abstraction shows up in ~10 teams (`MotorIO`
> interface in 254 and 2910; `MotorIO` class in 1678, **5137 Iron Kodiaks**, 971; a `Motor` type in 971,
> 2412, 4099, 4504, 5026, and 4738), but almost all of them **leak vendor types** (254's `MotorIO`
> imports `com.ctre.phoenix6` `MotionMagicConfigs` / `NeutralModeValue`). The *vendor-clean,
> capability-segregated* form described here is rare — which is why it is an alternative, not the default.
> The supporting infrastructure is common, though: configured-device factories (`TalonFXFactory` in 6
> teams incl. 254/1678/3061, `PhoenixUtil` in 8, `CTREConfigs` in 7) — the layer this pattern sits on.

## Thesis

You don't abstract "a motor." You abstract a **role** — a small interface named for what the caller
commands (*go to this position*, *run at this speed*) — and you implement it by wrapping a concrete vendor
device with its configuration baked in for one purpose. A single **hardware object** constructs every
device, owns its configuration, and hands each subsystem the *narrow interface* it needs.

The design rests on one observation: **once you've decided the motor's job, you've decided the control
strategy** (FOC or not; position vs. velocity vs. torque). From that point the *commands* collapse to a
vendor-neutral vocabulary, and the only thing still vendor-shaped is *configuration*. So you abstract the
command surface and seal the config surface inside the impl.

## 1. Interfaces are named by capability, never by vendor

The rule that makes the whole thing work: **the interface name describes a capability the caller depends
on, not the hardware that provides it.**

- ❌ `ITalonMotor`, `ICTREFOCMotor`, `SparkPositionMotor` — vendor leaks into the name; callers couple to a brand.
- ✅ `PositionMotor`, `VelocityMotor`, `TorqueMotor` — named for what you ask of them.

Split by capability rather than building one universal `Motor` god-interface (interface segregation). A
device implements the *set* of role interfaces it can actually honor.

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

Two non-negotiables: signatures speak **mechanism units** and **neutral enums**. The moment a
`NeutralModeValue`, a `Rotation`, or a `StatusSignal` appears in the interface, the abstraction has failed
and you've just renamed a `TalonFX`. (Naming note: WPILib idiom drops the `I-` prefix and uses the plain
name or an `…IO` suffix — `PositionMotor` or `PositionMotorIO`. The prefix isn't the point; the capability
naming is.)

## 2. Optimizations are orthogonal capabilities — model them separately

FOC is *an efficiency optimization* — "do the same job, better" — and an optimization should be optional
and orthogonal, not baked into the control interface. But FOC actually maps to **two distinct abstract
concepts**, and the honest design keeps them apart:

**(a) The efficiency/smoothness aspect → an optional mix-in capability.** It changes *how well* the job is
done, not *what* you command, so it is a separate interface a device implements only if it has it:

```java
/** Opt-in efficiency mode (e.g. FOC). Absent where unsupported — query, don't assume. */
public interface EfficiencyOptimizable {
    void setEfficiencyOptimization(boolean enabled);
}
```

A caller writes `if (motor instanceof EfficiencyOptimizable o) o.setEfficiencyOptimization(true);`. A
motor that can't do it simply doesn't implement the interface — capability presence lives in the **type
system**, not in a runtime flag that silently lies.

**(b) The torque-control aspect → a distinct command capability.** Commanding amps/force is a *different
verb*, not an optimization, so it is its own role interface, offered only by devices that can:

```java
public interface TorqueMotor {            // CTRE FOC today; whoever ships it tomorrow
    void setTorqueCurrent(double amps);
}
```

This is the crux of *abstract the capability, not the vendor*: today only CTRE implements `TorqueMotor`
and `EfficiencyOptimizable`. That's fine — abstracting over one implementation is cheap and
forward-looking. When a second vendor ships FOC (patents expire, REV catches up), you add an
implementation and **not one caller changes**.

## 3. The implementations — vendor types live here, fully

Below the interface, each impl talks to its device in the device's native language and uses its best
features:

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
    public void setNeutralMode(NeutralMode m) { /* map to NeutralModeValue */ }
    // ...
}

final class SparkMaxPositionMotor implements PositionMotor {      // NO FOC → offers fewer interfaces
    private final SparkMax spark;
    // MAXMotion config baked in; setPosition → getClosedLoopController().setReference(...)
}

final class SimPositionMotor implements PositionMotor {           // physics plant, no vendor at all
    private final ElevatorSim plant; /* ... */
}
```

`SparkMaxPositionMotor` implements *only* `PositionMotor` — it doesn't pretend to be a `TorqueMotor`. The
interface set a device offers **is** its honest capability advertisement. No lowest-common-denominator
flattening, no emulation that lies.

## 4. The hardware object — collect, configure, hand out narrow references

One object assembles the robot's devices. It is the **factory and the configuration home**, and it exposes
each device *through its capability interface*:

```java
final class Hardware {                          // one per robot variant (comp / practice / sim)
    private final RobotConfig cfg;              // per-robot CAN IDs, ratios, limits

    PositionMotor elevator()  { return new TalonFXPositionMotor(cfg.elevator().id(),  cfg.elevator().spec()); }
    VelocityMotor leftDrive() { return new TalonFXPositionMotor(cfg.leftDrive().id(), cfg.leftDrive().spec()); }
    GyroSource    gyro()      { return new Pigeon2Gyro(cfg.gyro().id()); }
    // ...
}
```

The subsystem receives **only the interface**, injected — never the concrete type, and never `Hardware`
itself:

```java
class Elevator extends SubsystemBase {
    private final PositionMotor motor;
    Elevator(PositionMotor motor) { this.motor = motor; }   // depends on a capability, not a vendor, not Hardware
    public Command toHeight(double m) { return run(() -> motor.setPosition(m / DRUM_RADIUS)); }
}
```

That detail is the line between this and the old `RobotMap` anti-pattern: the subsystem depends on
`PositionMotor`, a thing it can fully exercise — **not** on a god-object it has to reach through. The
hardware object *constructs and injects*; it does not retain shared mutable ownership two subsystems can
fight over, so the command scheduler's requirements stay meaningful.

## 5. Where the real / sim swap happens

The hardware object **is** the run-mode switch — one place decides what every interface resolves to:

```java
static Hardware create(RobotMode mode, RobotConfig cfg) {
    return switch (mode) {
        case REAL   -> new RealHardware(cfg);     // TalonFX / SparkMax impls
        case SIM    -> new SimHardware(cfg);      // SimPositionMotor, etc.
        case REPLAY -> new ReplayHardware(cfg);   // log-fed impls
    };
}
```

This is the "one place to configure simulation" benefit — achieved without a shared hardware god-object
and without any vendor type crossing into a subsystem.

## 6. Guardrails (the conditions under which this stays honest)

Break these and it degrades into `RobotMap` or a leaky universal `Motor`:

1. **Capability names, never vendor names** in interfaces. `PositionMotor`, not `TalonPositionMotor`.
2. **No vendor type in any interface signature.** Mechanism units + neutral enums only.
3. **Segregate by role.** Small interfaces (`PositionMotor`, `VelocityMotor`, `TorqueMotor`,
   `EfficiencyOptimizable`), not one `Motor` that does everything.
4. **Hand out narrow references.** A subsystem gets `PositionMotor`, never `Hardware`. The hardware object
   is a factory, not an ambient dependency.
5. **Subsystems still own their devices.** Hardware constructs and injects once; it does not broker shared
   live hardware between subsystems.
6. **Capability presence is typed; absence is defined.** A device implements an optional interface or it
   doesn't; never silently fake a capability you lack.
7. **Config stays vendor-flavored inside the impl.** Take the *union* of parameters and document the
   no-ops (REV ignores jerk, etc.). Don't intersect down to a tuning surface that throws away Motion Magic
   / FOC / fused encoders.
8. **Only abstract roles you actually command.** Build `PositionMotor` because your arm needs it — not a
   speculative universal motor API.

## 7. When to use it — and when not

**Reach for it when:**
- You have several mechanically-similar mechanisms (elevator + arm + wrist = "one motor, position
  control") and want to share one implementation and one `SimPositionMotor` across all of them.
- You run **multiple physical robots** or anticipate a **vendor change**, and want the swap to be a new
  impl rather than a subsystem rewrite.
- You want the FOC/optimization decision expressed once, in the type system, rather than re-litigated per
  call site.

**Don't, when:**
- You are single-vendor with a handful of mechanisms — the per-subsystem `XxxIO` seam from the build spec
  is less machinery for the same sim/test/replay payoff.
- You'd be abstracting capabilities you don't actually command. Speculative generality is the failure mode
  here.

## 8. Honest costs

- You **still write a new impl per vendor.** The abstraction protects *callers*, not the impl author —
  that's the point, but it isn't free.
- The neutral-spec → vendor-config mapper is **ongoing maintenance** as vendordeps evolve.
- It is **slightly contrarian to the build spec**, which draws the boundary at the subsystem. Both are
  valid; this trades a little more device-level machinery for cross-mechanism reuse and a clean
  cross-vendor future. They compose — capability-typed devices can live inside subsystem IO impls.

## Bottom line

Writing your own motor class is sensible when it is an **interface on top of a vendor device, named for a
capability, with the configuration for one purpose wired in.** Split it by role; model optimizations like
FOC as orthogonal opt-in capabilities; let each device advertise its real capability set through the
interfaces it implements; and let one hardware object construct, configure, and inject them as narrow
references. Vendor names stay out of every signature; vendor code stays sealed inside the impls. Draw the
seam at the command surface, keep a thin config mapper underneath, and the day a second vendor ships FOC
you add a class instead of editing a subsystem.

## See also

- `../build-spec/elite-architecture.md` — the default subsystem-level IO seam this is an alternative to.
- `../build-spec/subsystems/00-anatomy-of-a-subsystem.md` — the IO quartet this pattern can live inside.
- Prior art to compare against: 254's `MotorIO` (clean command surface, leaky config surface), 5137 Iron
  Kodiaks' generalized `MotorIO`, and published libs (YAMS, PurpleLib) that attempt the device-level
  capability seam.
