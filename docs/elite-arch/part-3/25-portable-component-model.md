---
title: 25. The Portable Component Model — the Block
weight: 25
---
This is the core of the proposal. One shape describes every active thing on the robot, and the rest of
Part III is consequences of it.

## The four channels and one step

A **`Block`** is a tuple of four serializable data objects plus one pure step:

```
configure(Config)                                          // once: parameters / calibration / identity
(State′, Command_out[]) = update(Command_in, Observations) // each tick: fold in → advance → emit
state() -> State                                           // read the exposed state
```

- **`Config`** — what you parameterize it with: CAN IDs, gear ratios, gains, interlock tables. Mostly
  set once, with a defined runtime door for the parts that retune live ([§Config](#config-is-parameters)).
- **`Command_in` (u)** — the intent you send it this tick: a setpoint, a goal, a mode request.
- **`State` (x)** — what it exposes: its estimate (the measured/fused quantity) **and** its status
  (mode, `atGoal`, health).
- **`Command_out` (u′)** — the intents it emits for the blocks below it. *A block's `Command_out` is
  literally its children's `Command_in`.* Commands are the edges between blocks.

```d2
direction: down
CFG: "Config — parameters / calibration"
ABOVE: parent
BLK: "Block
configure(Config) once
(State′, Command_out[]) = update(Command_in, Observations)"
BELOW: children
CFG -> BLK: configure (once)
ABOVE -> BLK: "Command_in (u) — intent from above"
BLK -> ABOVE: "State (x) — estimate + status" { style.stroke-dash: 4 }
BLK -> BELOW: "Command_out (u′) — intent to below"
BELOW -> BLK: "Observations — children's State" { style.stroke-dash: 4 }
```

Naming follows the [motor spec's](26-portable-motor-interface.md) rule — a name must survive a change
of reader. `Command` = u and `State` = x are the state-space control pair, frame-invariant from any
viewpoint, where `Inputs`/`Outputs` silently pick a reference frame and invert under the other one.

## The fill-pattern *is* the taxonomy

The non-obvious result — the thing that makes this more than restating the actor model — is that
**which channels a block populates classifies what kind of component it is.** There is no separate
type hierarchy for sensors versus actuators versus controllers; the channel fill-pattern is the type:

| Component kind | Config | Cmd in (u) | State (x) | Cmd out (u′) | one line |
|---|:--:|:--:|:--:|:--:|---|
| **Sensor** (color, light) | ✓ | – | ✓ | – | a pure source of observations |
| **Actuator / leaf** (motor) | ✓ | ✓ | ✓ | – | command in, state out, no children |
| **Estimator** (`RobotState`) | ✓ | observations | ✓ | – | a sensor that *fuses* |
| **Subsystem** (elevator, drive) | ✓ | ✓ setpoint | ✓ | ✓ motor cmds | a controller over leaves |
| **Executive** (superstructure) | ✓ | ✓ goal | ✓ | ✓ subsystem goals | a controller over subsystems |

Three things fall out of the table. **A subsystem and a superstructure are the same kind** — both fill
all four channels, differing only in whether their children are motors or subsystems; this is why
"even the executive fits." **A sensor and an estimator differ by one channel** — the estimator takes
observations in and fuses, the sensor only emits. And **the robot is a tree of blocks**: commands flow
*down* (driver → executive → subsystem → motor → hardware) and state flows *up*.

```d2
direction: down
DRV: Driver / Auto
EXEC: "Executive (superstructure)"
SUBA: Subsystem
SUBB: Subsystem
MOT: Motor (leaf)
HW: Hardware
DRV -> EXEC: goal
EXEC -> SUBA: subsystem goal
EXEC -> SUBB: subsystem goal
SUBA -> MOT: motor command
MOT -> HW: voltage
HW -> MOT: "state up" { style.stroke-dash: 4 }
MOT -> SUBA: "state up" { style.stroke-dash: 4 }
SUBA -> EXEC: "state up" { style.stroke-dash: 4 }
```

## Emission is a return value, never a side effect

The single most important implementation rule. `update` *returns* its outgoing commands; it does not
hold references to its children and push into them.

- **Return-value form (do this):** a test feeds a recorded `Command_in` + `Observations` and asserts
  on `(State′, Command_out)` with zero hardware and no scheduler. Replay re-runs the same pure
  function over a log. ROS bridges it as publish-after-spin.
- **Push form (don't):** the block calls `child.setControl(...)` internally — now it is coupled to its
  children's identities, the seam you protected is gone, and you cannot test it in isolation.

So the "emit a command for something below" is the *output of a pure function*, and an **outer wiring
layer** (the periodic loop, `RobotContainer`) routes each block's `Command_out` to the next block's
`Command_in`. The block is ignorant of who consumes its output — exactly as a block-diagram block
doesn't know what's wired to its output port. This is the IO-seam principle ([ch. 3](../part-1/03-the-io-seam.md))
applied recursively, up the whole tree.

## `State` is estimate **and** status

For a motor, state is just the physical measurement — its measured position *is* its state variable.
Above the leaf, state splits in two: the **estimate** (the measured or fused quantity) and the
**status** (what the block is doing — its mode, `atSetpoint`, fault flags). For a subsystem you need
`atGoal`; for an executive the status (which mode, is it interlocked, is it ready) is the *primary*
output and the estimate is secondary. So `State` carries `{ estimate, status }`. This is also why
every level is named `…State` (`MotorState`, `RobotState`): state flows up, device → subsystem →
world, and naming every level the same reveals they are the same kind of thing at different scales.

## Config is parameters {#config-is-parameters}

`Config` is identity and calibration that does not change within a control session — kept as its own
channel, separate from the per-tick `Command`, so slow structural change never pollutes the command
log. Most of it is write-once; a defined subset is runtime-settable (PID gains, current limits, vision
trust) through a `reconfigure(partialConfig)` door. The boundary test: *if it changes every loop it's
a `Command`; if it identifies or calibrates the block across a session it's `Config`.*

## A discipline, not a base class

The failure mode of every "universal component interface" is the inner-platform effect:
`Block<Config, CmdIn, State, CmdOut>` with four Java generics metastasizes through every signature and
constrains nothing, because an interface that fits a color sensor *and* a superstructure necessarily
says almost nothing. So the model is delivered as a **contract you follow**, not a superclass you
extend:

> Every component takes a `Config` POD, accepts a `Command` POD, exposes a `State` POD (estimate +
> status), advances via one pure `update` that *returns* its outgoing commands, and obeys the
> lifecycle. Each is its own concrete types; there is no shared `Block` supertype carrying them.

Followed consistently, that convention buys uniform logging, replay, sim-testing, and ROS-bridging at
every scale — which is the entire point — without a lowest-common-denominator interface. The name
`Block` comes from block diagrams (the exact config-in / ports / state model), the least-spent word in
application software: `Node` is overloaded, `Unit` collides with WPILib's `Units`, `Module` collides
with swerve modules. The leaf hardware adapters keep their established `…IO` suffix — an `…IO` is the
downward edge of a leaf block, not a competing concept.

Why trust this shape? Because it is simultaneously a **ROS 2 lifecycle node** (parameters +
subscriptions + publications + managed states), a **Hewitt actor** (private state, receive/send), and
a **Simulink block** (parameters + ports + internal state, composed by wiring ports). When one
structure is independently arrived at by three battle-tested communities, it is load-bearing — and we
get to steal their refinements rather than rediscover them. The next chapters do exactly that, starting
with the leaf: [the portable motor interface](26-portable-motor-interface.md).
