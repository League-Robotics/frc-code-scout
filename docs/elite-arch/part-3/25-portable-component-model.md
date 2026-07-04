---
title: 25. The Portable Component Model — the faceplate
weight: 25
---
This is the core of the proposal. One shape describes every active thing on the robot, and the rest of
Part III is consequences of it.

## The faceplate: four channels and one step

Call each active thing on the robot a **component** — a motor, a sensor, a subsystem, the
superstructure. The word stays lowercase and informal, because there is deliberately no shared
supertype (see [§A discipline, not a base class](#a-discipline-not-a-base-class)). What every
component shares is its **faceplate** — the fixed set of sockets it presents to the rest of the
robot, the same four jacks on the front of every module no matter what circuitry sits behind them.
The faceplate is four serializable data objects plus one pure step:

```
configure(Config)                                          // once: parameters / calibration / identity
(State′, Command_out[]) = update(Command_in, Observations) // each tick: fold in → advance → emit
state() -> State                                           // read the exposed state
```

- **`Config`** — what you parameterize it with: CAN IDs, gear ratios, gains, interlock tables. Mostly
  set once, with a defined runtime door for the parts that retune live ([§Config](#config-is-parameters)).
- **`Command_in`** — the intent you send it this tick: a setpoint, a goal, a mode request.
- **`State`** — what it exposes: its estimate (the measured/fused quantity) **and** its status
  (mode, `atGoal`, health).
- **`Command_out`** — the intents it emits for the components below it. *A component's `Command_out`
  is literally its children's `Command_in`.* Commands are the edges between components.

`Observations` is deliberately not a fifth jack on the faceplate. It is **the `State` of the
component's children (and of designated peers such as `RobotState`)**, collected by the outer wiring
layer and handed to `update` as its second argument. The tick's timestamp rides in `Observations` too
— it is a fact about the world, delivered like any other.

```d2
direction: down
CFG: "Config — parameters / calibration"
ABOVE: parent
CMP: "Component
configure(Config) once
(State′, Command_out[]) = update(Command_in, Observations)"
BELOW: children
CFG -> CMP: configure (once)
ABOVE -> CMP: "Command_in — intent from above"
CMP -> ABOVE: "State — estimate + status" { style.stroke-dash: 4 }
CMP -> BELOW: "Command_out — intent to below"
BELOW -> CMP: "Observations — children's State (+ timestamp)" { style.stroke-dash: 4 }
```

Naming follows the [motor spec's](26-portable-motor-interface.md) rule — a name must survive its
reader — which is where `Command`/`State` are defended in full against AdvantageKit's
`Inputs`/`Outputs`.

## The fill-pattern *is* the taxonomy

The non-obvious result — the thing that makes this more than restating the actor model — is that
**which of the faceplate's channels a component populates classifies what kind of component it is.**
There is no separate type hierarchy for sensors versus actuators versus controllers; the fill-pattern
— which jacks are wired, which are left empty like a chip's NC pins — is the type:

| Component kind | Config | Cmd in | State | Cmd out | one line |
|---|:--:|:--:|:--:|:--:|---|
| **Sensor** (color, light) | ✓ | – | ✓ | – | a pure source of observations |
| **Actuator / leaf** (motor) | ✓ | ✓ | ✓ | – | command in, state out, no children |
| **Estimator** (`RobotState`) | ✓ | – | ✓ | – | a sensor that *fuses* |
| **Subsystem** (elevator, drive) | ✓ | ✓ setpoint | ✓ | ✓ motor cmds | a controller over leaves |
| **Executive** (superstructure) | ✓ | ✓ goal | ✓ | ✓ subsystem goals | a controller over subsystems |

Three things fall out of the table. **A subsystem and a superstructure are the same kind** — both fill
all four channels, differing only in whether their children are motors or subsystems; this is why
"even the executive fits." **A sensor and an estimator share a fill-pattern and differ in what they
observe** — both command channels empty, state out; the sensor's `Observations` come from hardware,
while the estimator's are the `State` of designated peers (drive odometry, vision poses), which it
fuses. Its `Command_in` is genuinely empty — nobody commands an estimate. And **the robot is a tree of
components**: commands flow *down* (driver → executive → subsystem → motor → hardware) and state flows
*up*.

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
- **Push form (don't):** the component calls `child.setControl(...)` internally — now it is coupled to
  its children's identities, the seam you protected is gone, and you cannot test it in isolation.

So the "emit a command for something below" is the *output of a pure function*, and an **outer wiring
layer** (the periodic loop, `RobotContainer`) routes each component's `Command_out` to the next
component's `Command_in`. The component is ignorant of who consumes its output — exactly as a rack
module doesn't know what's patched into its output jack. This is the IO-seam principle
([ch. 3](../part-1/03-the-io-seam.md)) applied recursively, up the whole tree.

## No wall-clock reads inside `update`

The companion rule, with the same weight. `update` never calls `Timer.getFPGATimestamp()` — or any
clock: the tick's timestamp arrives inside `Observations`, like every other fact about the world. A
component that reads the clock has smuggled in a hidden input — replay would feed it the recorded
commands and observations while it silently reads *now*, and the same log would produce different
outputs on different days. Deltas, timeouts, debounces, and profile clocks are all computed from the
observed timestamp. Time is data; treat it like the rest.

## `State` is estimate **and** status

For a motor, state is just the physical measurement — its measured position *is* its state variable.
Above the leaf, state splits in two: the **estimate** (the measured or fused quantity) and the
**status** (what the component is doing — its mode, `atSetpoint`, fault flags). For a subsystem you
need `atGoal`; for an executive the status (which mode, is it interlocked, is it ready) is the
*primary* output and the estimate is secondary. So `State` carries `{ estimate, status }`. This is
also why every level is named `…State` (`MotorState`, `RobotState`): naming device, subsystem, and
world state the same reveals they are the same kind of thing at different scales.

## `State` versus internal memory

`State` is what a component *exposes* on its faceplate, not everything it remembers behind it. A
component may keep internal memory — a PID integrator, motion-profile progress, a debounce timer —
that never appears in its `State`, provided `update` stays deterministic: the same `Command_in`,
`Observations`, and internal history must always produce the same outputs. The consequence, stated
honestly: replay is guaranteed bit-identical only when re-run **from tick 0 of a complete log with
deterministic code** — which is exactly AdvantageKit's actual model. Re-entering a log mid-stream
would require snapshotting every component's internal memory each tick, and we deliberately do not
require that.

## Config is parameters {#config-is-parameters}

`Config` is identity and calibration that does not change within a control session — kept as its own
channel, separate from the per-tick `Command`, so slow structural change never pollutes the command
log. Most of it is write-once; a defined subset is runtime-settable (PID gains, current limits, vision
trust) through a `reconfigure(partialConfig)` door. The boundary test: *if it changes every loop it's
a `Command`; if it identifies or calibrates the component across a session it's `Config`.*

## A discipline, not a base class {#a-discipline-not-a-base-class}

The failure mode of every "universal component interface" is the inner-platform effect:
`Component<Config, CmdIn, State, CmdOut>` with four Java generics metastasizes through every signature
and constrains nothing, because an interface that fits a color sensor *and* a superstructure
necessarily says almost nothing. So the model is delivered as a **contract you follow**, not a
superclass you extend:

> Every component takes a `Config` POD, accepts a `Command` POD, exposes a `State` POD (estimate +
> status), advances via one pure `update` that *returns* its outgoing commands, and obeys the
> lifecycle. Each is its own concrete types; there is no shared supertype carrying them.

Followed consistently, that convention buys uniform logging, replay, sim-testing, and ROS-bridging at
every scale — which is the entire point — without a lowest-common-denominator interface. This is also
why *faceplate* is a word of the book's vocabulary and never a name in the code: the concrete types
keep their natural names (`ElevatorCommand`, `MotorState`, `ElevatorIO`), and the faceplate is the
shape they all share. Appendix B records the naming decision in full — including why the earlier
working name, *block*, lost. The leaf hardware adapters keep their established `…IO` suffix — an
`…IO` is the downward edge of a leaf component, not a competing concept.

Why trust this shape? Because it is simultaneously a **ROS 2 lifecycle node** (parameters +
subscriptions + publications + managed states) and a **Simulink block** (parameters + ports + internal
state, composed by wiring ports) — the Hewitt actor is at best a distant cousin, since actors are
asynchronous and never synchronously return their outputs. When one structure is independently arrived
at by battle-tested communities, it is load-bearing — and we get to steal their refinements rather
than rediscover them. The next chapters do exactly that.

## The contract, worked once: an elevator

Before the instances, here is the whole contract in one place — a single elevator component, small
enough to read in a minute. This is *illustrative of the contract, not a finished library*: real code
would carry more fields, more status, and the lifecycle. First the three PODs:

```java
record ElevatorConfig(double gearRatio, double drumRadiusM,
                      double maxVelMps, double maxAccelMps2,
                      double kP, double kG) {}

record ElevatorCommand(double heightM) {}                  // Command_in: one goal

record ElevatorState(double heightM, double velMps,        // estimate
                     boolean atGoal, boolean connected) {} // status

record ElevatorObs(double timestampS, MotorState motor) {} // children's State + the tick's time

record ElevatorTick(ElevatorState state,                   // what update returns
                    List<MotorCommand> commandsOut) {}
```

Then the pure step — a profiled setpoint, no clock, no hardware, emission as the return value:

```java
ElevatorTick update(ElevatorCommand cmd, ElevatorObs obs) {
    double dt = obs.timestampS() - lastTs;                   // time is an observation
    lastTs = obs.timestampS();                               // internal memory, not State
    setpoint = profile.calculate(dt, setpoint,               // TrapezoidProfile — pure math
        new TrapezoidProfile.State(cmd.heightM(), 0.0));
    double height = obs.motor().positionRad() * cfg.drumRadiusM() / cfg.gearRatio();
    double velMps = obs.motor().velocityRadS() * cfg.drumRadiusM() / cfg.gearRatio();
    double volts  = cfg.kP() * (setpoint.position - height) + cfg.kG();
    var state = new ElevatorState(height, velMps,
        Math.abs(cmd.heightM() - height) < 0.02,             // atGoal
        obs.motor().connected());
    return new ElevatorTick(state,
        List.of(MotorCommand.voltage(volts)));               // emission is the return value
}
```

And the thin impure shell — a WPILib `Subsystem` whose `periodic()` is the wiring layer:

```java
public class Elevator extends SubsystemBase {
    private final ElevatorLogic logic = new ElevatorLogic(CONFIG);
    private final MotorIO io;                                // vendor types live below this line
    private ElevatorCommand cmd = new ElevatorCommand(0.0);

    public void setGoal(double heightM) { cmd = new ElevatorCommand(heightM); }

    @Override public void periodic() {
        var obs  = new ElevatorObs(Timer.getFPGATimestamp(), io.read());  // 1. read
        var tick = logic.update(cmd, obs);                                // 2. pure step
        io.apply(tick.commandsOut().get(0));                              // 3. actuate
        // 4. log cmd, obs, tick.state(), tick.commandsOut() — all PODs
    }
}
```

Everything the chapter argued is visible in these forty lines: the timestamp arrives inside
`ElevatorObs` rather than from a clock; `update` touches no hardware and returns its command instead
of pushing it; and the only impure code is the shell that reads, steps, and applies. A test constructs
an `ElevatorObs` by hand and asserts on the returned tick — no scheduler, no HAL. Chapters 26–28 work
this same contract at the leaf, the drivetrain, and the executive, starting with
[the portable motor interface](26-portable-motor-interface.md).
