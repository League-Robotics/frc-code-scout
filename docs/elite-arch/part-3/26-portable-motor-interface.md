---
title: 26. The portable motor interface — the leaf component
weight: 26
---
The motor is the leaf of the component tree: its faceplate carries `Config` (CAN id, gains),
`Command` (u), `MotorState` (x), and **no** outgoing-command channel. It is where the model touches metal, so it is
where the model is worked all the way down to a schema. Part II surveyed the six `MotorIO` shapes the
corpus actually uses ([ch. 17](../part-2/17-motor-interfaces.md)); this chapter takes the durable ideas
in them and recasts them as **two serializable data objects plus a capability-tiered port**, defined
once in proto3 and regenerable into any language — so the design choices show up as choices.

## Two data objects, named for what they are

A motor interface carries data in two directions, and each is a plain serializable object — not a bag
of method calls — so both can be logged, diffed, replayed, and sent over a wire:

- **`Command`** — what you're telling the motor to do. The intent. (A leaf has no outgoing-command
  channel, so the `_in` suffix is dropped: a motor's `Command_in` is just `Command`.)
- **`MotorState`** — what the motor is currently doing. Its physical state.

The dominant FRC convention (AdvantageKit) names the read struct `XxxIOInputs` — and has no symmetric
`Outputs` POD at all: the write side is imperative setters, and output logging is ad-hoc
`recordOutput(...)` calls. We reject the `Inputs` naming, and the critique carries either way. That
name is *relational, not identity*: "input" only means something once you say "input to what," and it
inverts under viewpoint — from the code's chair a sensor reading is an input; from control
theory's chair the *command* is the input (`u`) and the reading is the output. The rule we adopt
instead, used throughout Part III: **a name must survive a change of reader.** `Command` and
`MotorState` do — a command is a command from any viewpoint — and they are exactly
the state-space pair `u`/`x`. `MotorState` is honest for a motor specifically: a motor's measured
position and velocity *are* its state variables, so "state" is accurate here in a way it is not for a
whole robot, where hidden state must be *estimated* (which is what `RobotState`,
[ch. 28](28-robotstate-superstructure-blocks.md), is for).

## The schema: a `oneof` command, a flat state

The data is the hard, consistency-critical part; proto3 is the source of truth. The command is a
tagged union over control modes — `oneof` structurally enforces *at most* one mode at a time, so you
*cannot* set voltage and position together; an unset `oneof` is still valid on the wire, so the
boundary validates that `control` is set before any command is applied — plus optional modifiers:

```proto
message Command {
  oneof control {                       // the discriminant — at most one; boundary validates it's set
    double  duty_cycle        = 1;      // [-1, 1]
    double  voltage           = 2 [(unit) = "V"];
    double  torque_current    = 3 [(unit) = "A"];
    double  position          = 4;      // PID-to-position
    double  profiled_position = 5;      // Motion Magic / trapezoid
    double  velocity          = 6;
    Neutral neutral           = 7;      // BRAKE / COAST
  }
  optional uint32 slot                = 8;   // modifiers — null = "use default / don't override"
  optional double feedforward_voltage = 9  [(unit) = "V"];
  optional double max_stator_current  = 10 [(unit) = "A"];   // transient cap for this command
}

message MotorState {
  bool connected = 1;                        // discriminant — always present
  optional double position       = 2;        // rad or m   (null = "not reported this tick")
  optional double velocity       = 3;
  optional double applied_voltage = 6 [(unit) = "V"];
  optional double stator_current  = 8 [(unit) = "A"];
  optional double temperature     = 11 [(unit) = "degC"];
  optional bool   hardware_fault  = 15;
  // … electrical, thermal, controller-introspection, and limit fields elided — as is the
  // declaration of the (unit) FieldOptions extension the annotations above require …
}
```

Two rules carry the schema. **Nullable payloads, non-null discriminants:** absence must be
distinguishable from a real value, and `0.0` is a real reading while `NaN` is fragile — so payloads are
`optional` while the discriminants (`Command.control`, `MotorState.connected`) are always present. In
`MotorState`, null means "unknown / not reported by this device this tick"; in `Command`, null means
"use the configured default / don't override." And **names carry their own meaning:** a field is named
for the *quantity* (`stator_current`), never the unit (`stator_amps`) — the unit is machine-readable
metadata — and every bound is `max_`/`min_`-prefixed, so a bare `stator_current` is unambiguously a
*reading*, never a limit.

## One message set for the whole capability spectrum

Real motors form a spectrum — PWM-only (set a duty cycle, nothing comes back), PWM-plus-encoder
(open-loop command, but position readable), smart controller (onboard closed loop, gains, motion
profiling). Rather than one fat interface full of `unsupported()` stubs or N forked message types,
capability factors onto **two independent axes** while the messages stay unified:

| Axis | What upgrades it | How it's expressed |
|---|---|---|
| **Command** — which control modes are accepted | an onboard controller | typed port tiers (`BasicMotor` → `SmartMotor`) + declared `Capabilities.command_modes` |
| **Observation** — which state fields come back | a sensor / encoder | populated `MotorState` fields + `Capabilities.state_fields` |

The axes are orthogonal — an encoder upgrades observation without touching command — and the nullable
`Command`/`MotorState` already express both: a PWM motor's `Command` only ever sets `duty_cycle`, and
its `MotorState` populates only `connected`. So there is exactly **one `Command` and one `MotorState`
on the wire** (uniform translation, logging, replay), plus a **declared `Capabilities`** per motor and
**generated typed port tiers** for compile-time ergonomics:

```text
interface Motor {                         // universal data plane — every motor, capability-validated
    void          apply(Command cmd);     // the ONLY `apply`: rejects modes not in capabilities()
    MotorState    read();                 // once per tick; fields per capabilities()
    Capabilities  capabilities();
}
interface BasicMotor : Motor {            // PWM-class: open-loop only
    void setDutyCycle(double pct); void setVoltage(double v); void setNeutral(Neutral m);
}
interface SmartMotor : BasicMotor {       // onboard closed loop + config
    void setPosition(double units);  void setVelocity(double ups);  void resetPosition(double units);
    void setGains(uint32 slot, Gains g);  void setCurrentLimits(CurrentLimits c);
}
```

`apply(Command)` is the data-plane entry — where ROS-originated, replayed, and logged commands enter —
and it validates the mode against `capabilities()` at runtime. The `set…` helpers give hand-written
robot code compile-time guidance: a `BasicMotor` reference simply *has no* `setPosition`. The port is
not an RPC service; `apply`/`read` are in-process calls, and ROS is reached by translation, not by
making this a gRPC endpoint. This is the [capability-typed-devices pattern](../part-1/08-alternatives.md)
— interfaces named by capability, not vendor — reconciled with a single message schema.

Where the purity boundary sits deserves one explicit paragraph, because the component's `update`
never touches this port. The `…IO` adapter — the object that owns the vendor handle — is the **impure
shell**: its `read()` samples hardware into a `MotorState`, its `apply(Command)` pushes a command out
to metal. The wiring layer calls `read() → update() → apply()` each tick, in that order, and
everything between the two IO calls is pure ([ch. 25](25-portable-component-model.md)). The component
computes; the shell touches the world.

## Units and nullability, settled by codegen

Units follow ROS **REP-103**: everything SI by convention (m, rad, m/s, V, A, °C), bare `double`, with
the unit declared in the schema as metadata (`[(unit) = "rad/s"]`). That makes the corpus's
raw-doubles-versus-`Measure`-types debate a *codegen choice* — from the same annotation, emit raw
`double` accessors for the hot path or typed `Measure<Angle>` accessors where ergonomics win — and the
wire form stays SI doubles, so translation to ROS is identity on the numbers. Nullability gets one
idiom per language (`Optional<Double>` in Java, `None` in Python, `Option<f64>` in Rust); `NaN` is
**not** an in-code value — it exists only as a wire encoding on the ROS side, converted once at the
boundary, so no application code ever sees both.

One allocation decision is settled here because it constrains every generated binding: **the in-loop
channel types are plain mutable records/structs, and proto3 is the schema source of truth that appears
only at the log-and-wire boundary.** Generated protobuf-java messages are immutable,
builder-allocating objects — constructing them every 20 ms tick on a two-core roboRIO is a steady
garbage-collection tax, which is why WPILib itself serializes with QuickBuffers rather than
protobuf-java. So the hot loop passes reusable in-memory types generated *from* the schema, and the
protobuf encoding is produced only when a tick is logged or crosses the wire
([ch. 31](31-ros-bridge-portability.md)).

## Crossing to ROS, both directions

Because the proto is kept structurally isomorphic to the ROS target messages, the bridge is a
mechanical field map, not hand-tuned logic, and it needs exactly two conventions:

| Concern | Mapping |
|---|---|
| geometry, units, field names | **identity** — mirrored from `geometry_msgs`, both REP-103 SI |
| nullability | `None` ↔ `NaN` (ROS's own "no data" idiom) |
| `Command` `oneof` | ↔ `{ uint8 mode, double value }` — the `oneof` case ↔ the mode constant, lossless |

Commands cross from ROS too, and they are safe by construction: an arriving `Command` is validated
against `capabilities()` — a `POSITION` command to a PWM-only motor is rejected or clamped, exactly as
`ros2_control` refuses to write an interface a hardware component never exported. The leaf is now a
clean component. The next chapter composes four pairs of these into a drivetrain:
[the portable swerve interface](27-portable-swerve-interface.md).
