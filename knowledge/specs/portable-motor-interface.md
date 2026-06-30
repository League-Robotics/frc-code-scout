# A Portable, ROS-Harmonized Motor Interface

*A language-neutral specification for talking to a motor — the design that fell out
of surveying the corpus's six reusable `MotorIO` contracts
([../corpus-analysis/05-motor-io-interfaces.md](../corpus-analysis/05-motor-io-interfaces.md))
and asking what they'd look like freed from Java, AdvantageKit, and FRC-only assumptions.*

The corpus gave us six good motor abstractions, all welded to Java + AdvantageKit's
`@AutoLog`/`Inputs` conventions. This spec extracts the durable ideas and recasts them as
**two serializable data objects plus a capability-tiered port**, defined once in a
schema (proto3) and regenerated into any target language. It is designed to be
**translatable to and from ROS** in both directions, for state *and* commands.

> This is the **leaf instance** of the [portable component model](portable-component-model.md):
> a motor is a *block* with `Config` (CAN id, gains), `Command` (u), `MotorState` (x), and no
> outgoing-command channel. The `Command`/`State` = u/x naming defended below is where that parent
> model's naming discipline comes from.

---

## 1. The core decision: two data objects, named for what they are

A motor interface carries data in two directions. We model each as a **plain, serializable
data object** — not as a bag of method calls — so both can be logged, stored, diffed,
replayed, and sent over a wire (including ROS):

- **`Command`** — *what you're telling the motor to do.* The intent.
- **`MotorState`** — *what the motor is currently doing.* Its physical state.

### Why these names (and not `Inputs`/`Outputs`)

This is deliberate. The dominant FRC convention (AdvantageKit) calls the read-side struct
`Inputs` and the computed/command side `Outputs`. We reject that, for reasons that
generalize beyond FRC:

- **`Inputs`/`Outputs` are *relational*, not *identity*, names.** "Input" only means
  something once you say "input to what" — and the answer (a replay reconstructor) is an
  *external, optional* system that may not even exist for a given deployment. A name that
  depends on naming someone else's consumer is weaker than one that describes the thing.
- **They invert under viewpoint.** From the code's chair the sensor reading is an "input";
  from the plant's chair it's an output. From control theory's chair the *command* is the
  input (`u`) and the sensor reading is the output (`y`). So `Inputs`/`Outputs` silently
  pick a reference frame and mean the opposite under the other one.
- **`Command` / `MotorState` are frame-invariant.** A command is a command and a state is a
  state from any viewpoint — nothing to invert. And they are exactly the **state-space
  control pair**: `u` (the control/command) and `x` (the state). We're borrowing the
  formal vocabulary of the field this models, instead of contradicting it.

`MotorState` is honest for a *motor* specifically: a motor's measured quantities
(position, velocity) *are* its state variables, so "state" is accurate here in a way it is
not for a whole robot (where hidden state must be *estimated* → that's what a `RobotState`
seam is for). The minor overload with `RobotState` is a feature: state flows up the seams,
device → subsystem → world, and naming both ends `…State` reveals they're the same kind of
thing at different scales.

---

## 2. Design principles

1. **Two serializable PODs** — `Command` and `MotorState`. The interface reduces to
   `apply(Command)` / `read() -> MotorState`. Both directions are first-class data, so
   commands are loggable/replayable/translatable, not ad-hoc method calls.
2. **Nullable payloads, non-null discriminants.** Absence must be distinguishable from a
   legitimate value, and there is no safe in-band sentinel (`0.0` is a real reading;
   `NaN` is fragile). So payload fields are *optional*; the discriminants
   (`Command.control` mode, `MotorState.connected`) are always present.
   - In `MotorState`, null = **"unknown / not reported by this device this tick."**
   - In `Command`, null = **"use the configured default / don't override."**
3. **One "absent" idiom per language; `NaN` only on the wire.** See §7.
4. **Schema is the source of truth.** Defined in proto3; real codegen where it exists
   (Java, C++, Python, Rust, TS…), AI-generated bindings for exotic targets and the thin
   port shim. One file, many interfaces, regenerable on demand.
5. **Separate the data spec from the port.** The hard, consistency-critical, serializable
   part is the *data*. The port (two operations) is a thin, idiomatic per-language wrapper —
   **not** a gRPC/CORBA service.
6. **Capabilities are declared, not assumed.** Motors differ (PWM-only → PWM+encoder →
   smart controller). One message schema (the nullable superset) serves all of them; each
   motor *declares* what it supports (§5).
7. **Units by convention, declared in the schema.** SI per ROS **REP-103**, with the unit
   attached to each field as machine-readable metadata so codegen can emit raw or typed
   accessors (§6).
8. **ROS-translatable both directions, for state and commands.** Geometry mirrors
   `geometry_msgs`; scalar motor types mirror `ros2_control`/`JointState`; the bridge is
   generated, with exactly two documented conventions (§8).
9. **Names carry their own meaning.** Three conventions, applied without exception:
   - **Name the measurand, not the unit.** A field is named for the *quantity* it holds
     (`stator_current`, `max_peak_duration`), never the unit (`stator_amps`, `..._s`); the
     unit lives in the `(unit)` annotation (§6). This is the ROS convention too — field names
     are `position`/`velocity`/`effort`, never `meters`/`amps`.
   - **Every bound field is `max_`/`min_`-prefixed** so the name declares it's a limit *and*
     its direction. A bare `stator_current` is therefore unambiguously a *reading*
     (in `MotorState`), never a bound — the prefix is what distinguishes
     `max_stator_current` (a cap) from `stator_current` (the present draw).
   - **The bound-container suffix is meaningful:** `*Constraints` = shaping inputs *consumed
     by profile/trajectory generation* (`MotionConstraints`); `*Limits` = protective bounds
     the device *enforces continuously* in every mode (`CurrentLimits`).

---

## 3. The data model (proto3)

### 3.1 `geometry.proto` — mirror of `geometry_msgs`

For the multi-DOF objects (drivetrain, robot pose), reuse ROS's geometry vocabulary
field-for-field so translation is byte-trivial. (A single motor is 1-DOF/scalar and does
**not** use these — see §4.)

```proto
syntax = "proto3";
package robotics.geometry;
// All values SI per REP-103: m, rad, m/s, rad/s, N. Right-handed, x-fwd/y-left/z-up.

message Vector3    { double x = 1; double y = 2; double z = 3; }            // free vector (vel/accel/force)
message Point      { double x = 1; double y = 2; double z = 3; }            // position
message Quaternion { double x = 1; double y = 2; double z = 3; double w = 4; }

message Pose   { Point position = 1; Quaternion orientation = 2; }          // ≡ geometry_msgs/Pose
message Twist  { Vector3 linear = 1; Vector3 angular = 2; }                 // ≡ geometry_msgs/Twist  (≡ WPILib ChassisSpeeds)
message Accel  { Vector3 linear = 1; Vector3 angular = 2; }                 // ≡ geometry_msgs/Accel
message Wrench { Vector3 force  = 1; Vector3 torque  = 2; }                 // ≡ geometry_msgs/Wrench (force-domain dual of Twist)

message Time   { int32 sec = 1; uint32 nanosec = 2; }                       // ≡ builtin_interfaces/Time
message Header { Time stamp = 1; string frame_id = 2; }                     // ≡ std_msgs/Header — the frame discipline
```

> WPILib's `Pose2d`, `Twist2d`, and `ChassisSpeeds{vx,vy,omega}` are the planar projections
> of `Pose`/`Twist`. Harmonizing isn't adopting something foreign — it's giving the types
> you already use the ROS names and layouts. Carry a `Header` on every geometric quantity
> that lives in a coordinate frame (tf2 discipline); omit it for a scalar motor (use the
> joint *name* as identity instead, §4).

### 3.2 `control.proto` — reusable control sub-objects

```proto
syntax = "proto3";
package robotics.control;

// PID + FRC/CTRE feedforward terms. Harmonizes with control_toolbox/Pid (kp/ki/kd),
// extended with the feedforward terms FRC needs (ks/kv/ka/kg).
message Gains {
  double kp = 1; double ki = 2; double kd = 3;
  double ks = 4;            // static-friction FF (V)
  double kv = 5;            // velocity FF     (V per unit/s)
  double ka = 6;            // accel FF        (V per unit/s^2)
  double kg = 7;            // gravity FF      (V)
  optional double i_zone = 8;
}

// Suffix convention (it means something):
//   *Constraints = shaping inputs CONSUMED by profile/trajectory generation
//                  (not a continuous clamp; bound the generated motion).
//   *Limits      = protective bounds the device ENFORCES continuously, in every
//                  control mode (it clamps / refuses to exceed).
// Every bound field is named max_/min_ so the field itself declares its direction.

message MotionConstraints {          // shaping inputs for Motion Magic / trapezoid (+ S-curve)
  optional double max_velocity     = 1;   // unit/s
  optional double max_acceleration = 2;   // unit/s^2
  optional double max_jerk         = 3;   // unit/s^3   (S-curve smoothing bound; omit for pure trapezoid)
}

message CurrentLimits {              // continuously-enforced protective clamps
  optional double max_stator_current           = 1 [(unit) = "A"];   // cap on torque-producing current
  optional double max_supply_current           = 2 [(unit) = "A"];   // peak/burst cap on battery draw
  optional double max_supply_current_sustained = 3 [(unit) = "A"];   // reduced cap after the peak window elapses
  optional double max_peak_duration            = 4 [(unit) = "s"];   // how long max_supply_current is allowed before derating to sustained
}

// Rich controller introspection (the "fat" telemetry tier, à la 5137).
// Harmonizes with control_msgs/PidState.
message ControllerState {
  optional double setpoint = 1;
  optional double error    = 2;
  optional double p_term   = 3;
  optional double i_term   = 4;
  optional double d_term   = 5;
  optional double output_voltage = 6 [(unit) = "V"];
}
```

### 3.3 `motor.proto` — `Command`, `MotorState`, `Capabilities`

```proto
syntax = "proto3";
package robotics.motor;

import "control.proto";
import "google/protobuf/descriptor.proto";

// --- units as machine-readable metadata (REP-103 SI strings) ---
extend google.protobuf.FieldOptions { optional string unit = 50001; }

// ============================ COMMAND  (intent ≈ u) =========================
// Tagged union over control modes (EXACTLY one) + optional modifiers.
// `oneof` enforces "one mode at a time" structurally — you cannot set voltage AND position.
// Mechanism units: rotational = rad / rad·s⁻¹; linear = m / m·s⁻¹.
message Command {
  oneof control {                                   // the discriminant — always exactly one
    double  duty_cycle        = 1;                  // [-1, 1]
    double  voltage           = 2 [(unit) = "V"];
    double  torque_current    = 3 [(unit) = "A"];
    double  position          = 4;                  // PID-to-position
    double  profiled_position = 5;                  // Motion Magic / trapezoid
    double  velocity          = 6;
    Neutral neutral           = 7;                  // BRAKE / COAST
  }
  // modifiers — null = "use configured default / don't override"
  optional uint32 slot                = 8;
  optional double feedforward_voltage = 9  [(unit) = "V"];
  optional double max_stator_current  = 10 [(unit) = "A"];   // transient cap for this command
}
enum Neutral { BRAKE = 0; COAST = 1; }

// ============================ STATE  (x) ====================================
// Flat record. optional = "unknown / not reported by this device this tick".
message MotorState {
  bool connected = 1;                                       // discriminant — always present

  // mechanism frame (post gear-ratio / fused sensor)
  optional double position       = 2;                       // rad or m
  optional double velocity       = 3;                       // rad/s or m/s
  optional double acceleration   = 4;                       // rad/s^2 or m/s^2
  // motor frame (raw rotor) — for fusion / sanity
  optional double rotor_position = 5 [(unit) = "rad"];

  // electrical & thermal
  optional double applied_voltage = 6  [(unit) = "V"];
  optional double supply_voltage  = 7  [(unit) = "V"];
  optional double stator_current  = 8  [(unit) = "A"];
  optional double supply_current  = 9  [(unit) = "A"];
  optional double torque_current  = 10 [(unit) = "A"];
  optional double temperature     = 11 [(unit) = "degC"];

  // rich controller introspection (optional tier)
  optional robotics.control.ControllerState controller = 12;

  // limits & faults
  optional bool at_forward_limit = 13;
  optional bool at_reverse_limit = 14;
  optional bool hardware_fault   = 15;
}

// ============================ CAPABILITIES ==================================
// What a given motor actually supports — the portable, declared truth,
// modeled on ros2_control's exported command/state interfaces. Callers and the
// ROS bridge validate against it (a POSITION command to a PWM motor is rejected).
message Capabilities {
  repeated ControlMode command_modes = 1;   // which Command.control modes are accepted
  repeated StateField  state_fields  = 2;   // which MotorState fields get populated
  bool onboard_closed_loop = 3;             // closed loop on the device vs on the host
  bool runtime_gains       = 4;             // gains settable live
}
enum ControlMode {
  CM_DUTY_CYCLE = 0; CM_VOLTAGE = 1; CM_TORQUE_CURRENT = 2;
  CM_POSITION = 3; CM_PROFILED_POSITION = 4; CM_VELOCITY = 5; CM_NEUTRAL = 6;
}
enum StateField {
  SF_POSITION = 0; SF_VELOCITY = 1; SF_ACCELERATION = 2;
  SF_ELECTRICAL = 3; SF_TEMPERATURE = 4; SF_CONTROLLER = 5; SF_FAULTS = 6;
}
```

---

## 4. Capability spectrum: two axes, one message set

Real motors form a spectrum — PWM-only (set duty cycle, nothing back), PWM+encoder
(open-loop command, but position/velocity readable), smart controller (onboard closed loop,
gains, motion profiling). Rather than one fat interface full of `unsupported()` stubs (the
5137 approach) or N forked message types, factor capability on **two independent axes** and
keep the **messages unified**:

| Axis | What upgrades it | How it's expressed |
|---|---|---|
| **Command capability** — which control modes are accepted | an onboard controller | **typed port tiers** (`BasicMotor` → `SmartMotor`) + `Capabilities.command_modes` |
| **Observation capability** — which state fields come back | a sensor / encoder | populated `MotorState` fields + `Capabilities.state_fields` (no new methods — `read()` is identical) |

The axes are orthogonal: an encoder upgrades *observation* without touching *command*
(closed loop still runs on the host); an onboard controller upgrades *command*. The
**nullable `MotorState`/`Command` already express both** — a PWM motor's `Command` only ever
sets `duty_cycle`; its `MotorState` populates only `connected` (+ maybe `applied_voltage`).

So there is exactly **one `Command` and one `MotorState`** on the wire (uniform translation,
logging, replay), plus:

- a **declared `Capabilities`** per motor (the ros2_control-style portable truth), and
- **generated typed port tiers** for ergonomics and compile-time safety.

This is the [capability-typed-devices pattern](../alternatives/01-capability-typed-devices.md)
("interfaces named by capability, not vendor"), reconciled with a single message schema.

---

## 5. The port

Two layers. A universal **data plane** (needed for ROS, replay, logging — a `Command` is a
`Command` regardless of motor) plus **ergonomic tiered facades** that gate the methods a
given motor should expose.

**Verb convention.** `apply` is used for exactly one thing — handing over the whole
`Command` *object*. Every method that takes a *scalar or named value* is `set…` (it writes
one thing). So there is one `apply(Command)` and the rest are `set…`. The lone naming trap
is position: `setPosition` *commands* a move, while `resetPosition` *redefines* the current
position (seeds the sensor) — the same split 971 uses, so the two never collide.

```text
// Universal data plane — every motor. Capability-validated.
interface Motor {
    void          apply(Command cmd);     // the ONLY `apply` — takes the whole Command object;
                                          // rejects modes not in capabilities().command_modes
    MotorState    read();                 // call once per tick; fields per capabilities().state_fields
    Capabilities  capabilities();
}

// Ergonomic facades (generated). Command axis → compile-time tiers.
// Scalar helpers are `set…` — each writes one value (and builds a Command under the hood).
interface BasicMotor : Motor {            // PWM-class: open-loop only
    void setDutyCycle(double pct);
    void setVoltage(double volts);
    void setNeutral(Neutral mode);
}
interface SmartMotor : BasicMotor {       // onboard closed loop + config
    void setPosition(double units /*, slot, ff */);   // command a position (cf. resetPosition)
    void setVelocity(double unitsPerSec);
    void setProfiledPosition(double units);
    void resetPosition(double units);                 // redefine current position (seed) — NOT a move
    void setGains(uint32 slot, Gains gains);
    void setMotionConstraints(MotionConstraints c);
    void setCurrentLimits(CurrentLimits c);
}
```

- `apply(Command)` is the **data-plane entry** (ROS-originated commands, replayed commands,
  logged commands) — the one place a whole `Command` object enters. It validates the mode
  against `capabilities()` — the runtime backstop.
- The **`set…` helpers** give hand-written robot code compile-time guidance: a `BasicMotor`
  reference simply has no `setPosition`. Each is a thin builder that constructs a `Command`
  and routes it through `apply`.
- The port is **not** an RPC service. `apply`/`read` are in-process calls; ROS is reached by
  translation (§8), not by making this interface a gRPC/DDS endpoint.

### Lifecycle / direction (unchanged from the corpus pattern)

`read()` is a **fresh per-tick snapshot** — no memory; call it once at the top of the loop.
Commands flow *down* through `apply`; state flows *up* through `read`. Statefulness
(enable/disable, "reapply last command," dashboard alerts) belongs in an optional base class
over this interface, not in the data objects.

---

## 6. Units

Follow ROS **REP-103**: everything **SI by convention** (m, rad, m/s, rad/s, V, A, N, °C),
fields are bare `double`, and the unit is **declared in the schema** as machine-readable
metadata (`[(unit) = "rad/s"]`) rather than baked into a type.

This settles the corpus's units debate (raw-doubles-by-convention vs WPILib `Measure` types)
by making it a **codegen choice**: from the same annotation, the generator can emit raw
`double` accessors for the hot path *or* typed accessors (`Measure<Angle>` in Java, `pint`
quantities in Python). The wire form stays SI doubles, so **translation to ROS is identity
on the numbers** — no unit conversion at the bridge.

---

## 7. Nullability and per-language idioms

Each language uses **one** representation of "absent." `NaN` is **not** an in-code value; it
exists only as a wire encoding on the ROS side, and the bridge converts it on crossing so no
application code ever sees both.

| Context | "absent" | "present" |
|---|---|---|
| proto3 (source of truth) | field unset (explicit presence) | set |
| Python | `None` | `float` |
| Java | `Optional<Double>` / `OptionalDouble` | `double` |
| Rust | `Option<f64>` | `f64` |
| C++ | `std::optional<double>` | `double` |
| **ROS wire** | **`NaN`** (or empty array) | value |

proto3 `optional` gives true presence semantics, so inside generated code you already get
`None`/`Option`/`Optional` everywhere — `NaN` appears *only* when translating to ROS (which
lacks `optional`). **Python rule: always `None`, never `float('nan')`** — because
`nan != nan` silently breaks every equality/membership check while `x is None` is reliable.
The same one-idiom discipline holds in every target; the bridge is the sole place that knows
both `None` and `NaN`.

---

## 8. ROS translation (both directions, state and commands)

Source of truth stays in proto; ROS is reached through a **generated bridge**. Because the
proto is kept **structurally isomorphic** to the ROS target messages, the bridge is a
mechanical field map (itself AI-generatable from the two schemas), not hand-tuned logic.

### Translation ledger

| Concern | Translatability | Note |
|---|---|---|
| Geometry (`Vector3`/`Pose`/`Twist`/`Wrench`) | **Identity** | mirrored from `geometry_msgs` |
| Units | **Identity** | both REP-103 SI — numbers unchanged |
| Field names | **Identity** | ROS snake_case names (`position`, `velocity`, `effort`) |
| `Header` / frames | **Near-identity** | only split `Time{sec,nanosec}` |
| **Nullability** | **One convention** | ROS `.msg` has no `optional` → see below |
| **`Command` `oneof`** | **One mapping** | ROS has no sum type → see below |

### Convention 1 — `None` ↔ `NaN`

ROS already uses **`NaN` as its "no data" idiom** (e.g. `sensor_msgs/NavSatFix`,
`LaserScan`), and `JointState` omits unavailable fields via empty arrays. Map an unset
optional → `NaN` outbound, `NaN` → unset inbound. The loss is **benign in the direction it
happens**: outbound state is for rviz/rosbag/other nodes, and `NaN` is exactly how ROS
expects "unknown" to read there. The bridge does this conversion once, at the boundary.

### Convention 2 — `oneof` ↔ `{mode enum, value}`

ROS's idiom for "one of several modes" is a `uint8` enum tag + value fields. The mapping is
**lossless both ways** — only the *structure* differs (union vs flat+tag), not the
information; the `oneof` case ↔ the `mode` constant exactly:

```text
proto:  oneof control { double duty_cycle; double voltage; double position; double velocity; ... }
ROS  :  uint8   mode            # CM_DUTY_CYCLE=0 CM_VOLTAGE=1 CM_POSITION=3 CM_VELOCITY=5 ...
        float64 value               # interpreted per mode
        float64 feedforward_voltage # modifiers (NaN = unset)
        float64 max_stator_current
        uint32  slot
```

Use a **custom mirrored ROS message** in your own package as the always-available,
isomorphic path; optionally add adapters to *standard* ROS homes
(`trajectory_msgs/JointTrajectoryPoint`, `ros2_control` command interfaces) when an existing
ROS controller must drive the motors.

### Commands from ROS are safe by construction

Commands cross **both** directions (rare, but supported). When a `Command` arrives from ROS,
the receiving motor **validates it against `capabilities()`** — a `POSITION` command to a
PWM-only motor is rejected or clamped, exactly as `ros2_control` refuses to write an
interface a hardware component never exported. So "command-from-ROS" is guarded, not hoped.

---

## 9. Codegen workflow

1. **Author** `geometry.proto`, `control.proto`, `motor.proto` (above) as the committed
   source of truth.
2. **Generate** message types with `protoc` for first-class targets (Java for the robot;
   Python/Rust/C++/TS for tools). Deterministic, maintained.
3. **Generate** the thin port shim (`Motor`/`BasicMotor`/`SmartMotor`) and exotic-target
   bindings with AI from the schema — these are mechanical and the schema is unambiguous.
4. **Generate** the ROS bridge (proto ↔ mirrored `.msg`) from the two schemas, applying the
   two conventions in §8.
5. **Choose accessor flavor** per language from the `(unit)` annotations: raw `double` on
   the hot path, typed measures where ergonomics win.

Single source of truth; deterministic codegen where it exists; AI for the shim and the
long tail. Add a control mode → one `oneof` arm + one enum constant, and it propagates to
every binding, the capability set, and the ROS mapping.

---

## 10. Summary of decisions

- **`Command`** (intent, `u`) and **`MotorState`** (state, `x`) — two serializable PODs,
  named by identity, not `Inputs`/`Outputs`.
- **Nullable payloads, non-null discriminants**; null = "unknown" (state) / "don't override"
  (command); no sentinels.
- **One idiom per language for absent; `NaN` only on the ROS wire.**
- **`oneof`** for control modes (one-at-a-time enforced structurally) + optional modifiers.
- **One message set + declared `Capabilities` + typed port tiers** for the PWM→smart
  spectrum, on two axes (command / observation).
- **Units SI per REP-103**, declared as schema metadata; representation is a codegen choice.
- **Geometry mirrors `geometry_msgs`; scalar motor mirrors `ros2_control`/`JointState`.**
- **proto3 source of truth**, regenerable into any language by `protoc` or AI.
- **ROS-translatable both directions for state and commands**, via a generated bridge with
  exactly two conventions (`None`↔`NaN`, `oneof`↔`mode-enum`).

---

## Appendix A — Lineage: the Java-concrete draft (v1)

This spec evolved from a first, Java/AdvantageKit-concrete draft — the contract we distilled
directly from the corpus survey
([../corpus-analysis/05-motor-io-interfaces.md](../corpus-analysis/05-motor-io-interfaces.md))
before generalizing it into the language-neutral form above. It is preserved here as the
*history of ours*. Note what changed on the way to v2:

| v1 (below) | v2 (this spec) |
|---|---|
| `MotorIOInputs` struct (read) + method setters (command) | two PODs: `MotorState` + `Command` |
| named `Inputs`/setters (role/direction) | named `MotorState`/`Command` (identity; `x`/`u`) |
| primitive `double`, `0.0` defaults | **nullable** payloads; null = unknown / don't-override |
| `Request` record (reified control) | `Command` `oneof` (one-mode-enforced) |
| `Capability` enum set | `Capabilities` message + typed port tiers (two axes) |
| Java-only, `@AutoLog` | proto3 source of truth, any language |
| units by convention (comment) | units by REP-103 schema annotation |
| — | ROS-translatable (geometry + bridge) |

The v1 still used the inputs-struct / method-setter shape and the `Request` value object —
the direct predecessors of `MotorState` and `Command`.

```java
package frc.lib.io;

import java.util.EnumSet;
import java.util.Set;
import org.littletonrobotics.junction.AutoLog;

/**
 * Unified motor IO contract for every rotational or linear mechanism.
 *
 * UNIT CONVENTION (not type-enforced — keep it consistent per subsystem):
 *   rotational mechanisms  -> radians,  rad/s,  rad/s^2
 *   linear mechanisms      -> meters,   m/s,    m/s^2
 * The gear-ratio / rotor->mechanism conversion lives in the implementation;
 * subsystems and superstructure speak ONLY mechanism units.
 *
 * Implement the required methods; optional methods default to a no-op that
 * records the gap via {@link #onUnsupported}. Advertise what you actually
 * support through {@link #capabilities()} so callers can check at construction.
 */
public interface MotorIO {

    // ---------------------------------------------------------------- inputs
    @AutoLog
    class MotorIOInputs {
        public boolean connected = false;

        // mechanism frame (post gear-ratio / fused encoder)
        public double positionUnits = 0.0;
        public double velocityUnitsPerSec = 0.0;
        public double accelUnitsPerSecSq = 0.0;

        // motor frame (raw rotor) — for fusion debugging & sanity
        public double rawRotorPositionRot = 0.0;

        // electrical & thermal
        public double appliedVolts = 0.0;
        public double supplyVolts = 0.0;
        public double statorCurrentAmps = 0.0;
        public double supplyCurrentAmps = 0.0;
        public double torqueCurrentAmps = 0.0;
        public double tempCelsius = 0.0;

        // control-loop introspection
        public String controlMode = "Neutral";
        public double setpointUnits = 0.0;
        public double errorUnits = 0.0;
        public double feedforwardVolts = 0.0;

        // limits & faults
        public boolean atForwardLimit = false;
        public boolean atReverseLimit = false;
        public boolean hardwareFault = false;
        public boolean tempFault = false;
    }

    /** Read all device signals into {@code inputs}. Call once per loop, FIRST. */
    void updateInputs(MotorIOInputs inputs);

    // -------------------------------------------------------------- required
    // The irreducible minimum every motor can do.

    /** Open-loop fraction of bus voltage in [-1, 1]. */
    void setDutyCycle(double percent);

    /** Open-loop voltage (volts). */
    void setVoltage(double volts);

    /** Brake resists motion; coast frees the rotor. */
    void setNeutralMode(NeutralMode mode);

    /** Cut output now (applies the configured neutral mode). */
    void stop();

    // -------------------------------------------------------------- optional
    // Closed-loop control. mechanism units; `slot` selects a gain set;
    // `feedforwardVolts` is an arbitrary additive FF (0 to ignore).

    default void setTorqueCurrent(double amps) { onUnsupported("setTorqueCurrent"); }

    default void setPosition(double positionUnits) { setPosition(positionUnits, 0, 0.0); }
    default void setPosition(double positionUnits, int slot, double feedforwardVolts) {
        onUnsupported("setPosition");
    }

    /** Trapezoid / Motion-Magic-profiled move to a position. */
    default void setProfiledPosition(double positionUnits) { setProfiledPosition(positionUnits, 0, 0.0); }
    default void setProfiledPosition(double positionUnits, int slot, double feedforwardVolts) {
        onUnsupported("setProfiledPosition");
    }

    default void setVelocity(double unitsPerSec) { setVelocity(unitsPerSec, 0, 0.0); }
    default void setVelocity(double unitsPerSec, int slot, double feedforwardVolts) {
        onUnsupported("setVelocity");
    }

    // -- config (runtime-settable) --
    default void setGains(int slot, Gains gains) { onUnsupported("setGains"); }
    default void setMotionConstraints(double maxVel, double maxAccel, double jerk) { onUnsupported("setMotionConstraints"); }
    default void setStatorCurrentLimit(double amps) { onUnsupported("setStatorCurrentLimit"); }
    default void setSupplyCurrentLimit(double amps) { onUnsupported("setSupplyCurrentLimit"); }
    default void setSoftLimits(double minUnits, double maxUnits) { onUnsupported("setSoftLimits"); }
    default void enableSoftLimits(boolean forward, boolean reverse) { onUnsupported("enableSoftLimits"); }
    default void setContinuousWrap(boolean wrap) { onUnsupported("setContinuousWrap"); }
    default void setInverted(boolean inverted) { onUnsupported("setInverted"); }

    // -- sensor / zeroing --
    default void setCurrentPosition(double positionUnits) { onUnsupported("setCurrentPosition"); }
    default void zero() { setCurrentPosition(0.0); }

    // -- followers --
    default void follow(int leaderCanId, boolean opposeDirection) { onUnsupported("follow"); }

    // -- simulation-only (no-op on hardware; never "unsupported") --
    default void setSimState(double positionUnits, double velocityUnitsPerSec) {}
    default void setSimConnected(boolean connected) {}

    // --------------------------------------------------- reified control (opt)
    // The 1678/2706 path: an immutable, storable, replayable command that can
    // carry a transient current cap. Plain setters above are the easy path;
    // applyRequest is the powerful one. Default dispatches onto the setters.

    default void applyRequest(Request r) {
        switch (r.mode()) {
            case DUTY_CYCLE       -> setDutyCycle(r.value());
            case VOLTAGE          -> setVoltage(r.value());
            case TORQUE_CURRENT   -> setTorqueCurrent(r.value());
            case POSITION         -> setPosition(r.value(), r.slot(), r.feedforwardVolts());
            case PROFILED_POSITION-> setProfiledPosition(r.value(), r.slot(), r.feedforwardVolts());
            case VELOCITY         -> setVelocity(r.value(), r.slot(), r.feedforwardVolts());
            case NEUTRAL          -> stop();
            case COAST            -> setNeutralMode(NeutralMode.COAST);
        }
    }

    // -------------------------------------------------------- capability query
    /** What this implementation actually supports. Check at construction. */
    default Set<Capability> capabilities() { return EnumSet.noneOf(Capability.class); }
    default boolean supports(Capability c) { return capabilities().contains(c); }

    /**
     * Called when an optional method is invoked on an impl that didn't override
     * it. Default is silent; {@code MotorIOBase} overrides this to raise a
     * driver-station Alert (the 5137 pattern). NOT triggered in REPLAY.
     */
    default void onUnsupported(String method) { /* override to alert */ }

    // --------------------------------------------------------------- value types
    enum NeutralMode { BRAKE, COAST }

    enum ControlMode { DUTY_CYCLE, VOLTAGE, TORQUE_CURRENT, POSITION, PROFILED_POSITION, VELOCITY, NEUTRAL, COAST }

    enum Capability { DUTY_CYCLE, VOLTAGE, TORQUE_CURRENT, POSITION, PROFILED_POSITION,
                      VELOCITY, FOLLOWER, SOFT_LIMITS, CONTINUOUS_WRAP, RUNTIME_GAINS }

    /** kP..kG in one immutable bundle (matches 2706's slot setters / CTRE Slot configs). */
    record Gains(double kP, double kI, double kD, double kS, double kV, double kA, double kG) {}

    /**
     * Immutable control request. {@code value} is in mechanism units appropriate
     * to {@code mode}. {@code statorLimitAmps} <= 0 means "leave config alone";
     * a positive value applies a transient stator cap before the command (1678's
     * withCurrentLimit setpoints). Build with the factories.
     */
    record Request(ControlMode mode, double value, int slot,
                   double feedforwardVolts, double statorLimitAmps) {
        public static Request dutyCycle(double pct)            { return new Request(ControlMode.DUTY_CYCLE, pct, 0, 0, 0); }
        public static Request voltage(double v)                { return new Request(ControlMode.VOLTAGE, v, 0, 0, 0); }
        public static Request torqueCurrent(double a)          { return new Request(ControlMode.TORQUE_CURRENT, a, 0, 0, 0); }
        public static Request position(double u)               { return new Request(ControlMode.POSITION, u, 0, 0, 0); }
        public static Request profiledPosition(double u)       { return new Request(ControlMode.PROFILED_POSITION, u, 0, 0, 0); }
        public static Request velocity(double u)               { return new Request(ControlMode.VELOCITY, u, 0, 0, 0); }
        public static Request neutral()                        { return new Request(ControlMode.NEUTRAL, 0, 0, 0, 0); }
        public static Request coast()                          { return new Request(ControlMode.COAST, 0, 0, 0, 0); }
        public Request withSlot(int s)                         { return new Request(mode, value, s, feedforwardVolts, statorLimitAmps); }
        public Request withFeedforward(double v)               { return new Request(mode, value, slot, v, statorLimitAmps); }
        public Request withStatorLimit(double a)               { return new Request(mode, value, slot, feedforwardVolts, a); }
    }
}
```

The optional stateful base — `enable()/disable()`, "reapply last request," and dashboard
`Alert`s (the 1678/2706 lifecycle + 5137 alerts), kept off the pure interface:

```java
public abstract class MotorIOBase implements MotorIO {
    protected final String name;
    protected final MotorIOInputsAutoLogged inputs = new MotorIOInputsAutoLogged();
    private Request lastRequest = Request.neutral();
    private boolean enabled = true;
    private final Alert disconnected, hardwareFault, overTemp;

    protected MotorIOBase(String name) {
        this.name = name;
        disconnected  = new Alert(name + " disconnected", AlertType.kError);
        hardwareFault = new Alert(name + " hardware fault", AlertType.kError);
        overTemp      = new Alert(name + " overheating", AlertType.kWarning);
    }

    /** Call once per loop: refresh inputs, log, and update alerts. */
    public final void periodic() {
        updateInputs(inputs);
        Logger.processInputs(name, inputs);
        disconnected.set(!inputs.connected);
        hardwareFault.set(inputs.hardwareFault);
        overTemp.set(inputs.tempFault);
    }

    @Override public void applyRequest(Request r) {
        lastRequest = r;
        if (enabled) MotorIO.super.applyRequest(r);
    }
    public final void enable()  { enabled = true;  applyRequest(lastRequest); }
    public final void disable() { enabled = false; stop(); }

    @Override public void onUnsupported(String method) {
        new Alert(name + ": unsupported motor op '" + method + "'", AlertType.kWarning).set(true);
    }
}
```

### How v1 covered each team's use cases

- **254 / 2910** — plain `double`-unit setters, `int slot`, arbitrary FF, flat `@AutoLog`
  inputs: the required + optional setters *are* their surface. 2910's motor-vs-mechanism
  frame split is preserved (`rawRotorPositionRot` vs `positionUnits`).
- **971** — its `Angle`/`Distance` overloads collapse to one `setPosition(double units)`
  (radians for rotational, meters for linear, by the documented convention); a thin typed
  façade can restore compile-time units for teams that want it.
- **2706** — `applyRequest(Request)` is the "only applied through Setpoints" path;
  `Request` is immutable like its Setpoints; runtime `setGains`/`setMotionConstraints`
  and follower support map directly. Per-follower array logging is the one feature left to
  the implementation (log followers under sub-keys).
- **5137** — capability reporting + `onUnsupported` alerting *is* 5137's `unsupportedFeature()`,
  but queryable in advance; its rich introspection fields are in the inputs struct;
  current limits, soft limits, continuous wrap, sim hooks all present.
- **1678** — `Request` reifies the `Setpoint`; `withStatorLimit(amps)` reifies the
  `withCurrentLimit` setpoints; `MotorIOBase` supplies `enable()/disable()` + last-request
  reapply + the `Mode` introspection (via `controlMode` in inputs).

### v1's deliberate trade-offs (carried into v2 except where noted)

- **Doubles over `Units`.** Followed the 4-of-6 majority for hot-path speed and sim
  simplicity, unit correctness a *convention* not a compiler check. *(v2 keeps SI-by-convention
  but adds machine-readable unit annotations, §6.)*
- **No vendor types in the signature.** Exposes only `frc.lib.io` types and primitives — so
  `com.ctre`/`com.revrobotics` stays *below* the IO line, satisfying the rubric's hard rule.
  *(v2 strengthens this: only proto-defined types cross the wire.)*
- **No-op sim hooks, loud control gaps.** Calling `setSimState` on hardware is a legitimate
  no-op; calling `setPosition` on a duty-cycle-only roller is a bug — hence the asymmetry.
  *(v2 replaces the runtime `onUnsupported` alert with up-front `Capabilities` validation.)*
