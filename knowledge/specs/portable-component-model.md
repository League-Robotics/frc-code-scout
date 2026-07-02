# The Portable Component Model — One Shape for Motors, Sensors, Subsystems, and Executives

*The parent abstraction the other specs are instances of. Every active thing in a robot — a motor, a
sensor, a subsystem, the world-model estimator, the superstructure — has the same shape: it is
**configured once, then each tick folds an incoming command together with fresh observations to
advance its state and emit commands for the things below it.** That is a configured transfer function
with memory. This spec formalizes that shape as a discipline (not a base class), shows that **which of
its four channels are populated is exactly the taxonomy of component kinds**, and recovers the
[motor](portable-motor-interface.md) and [swerve](portable-swerve-interface.md) specs as the leaf and
mid-level instances of it.*

The motor spec already committed to half of this — `Command` = u, `MotorState` = x. This spec
generalizes it up the whole stack and adds the two channels a leaf device doesn't need: **a
configuration channel** (every component is parameterized — even a color sensor has light-level
calibration) and **an outgoing-command channel** (a subsystem commands motors; a superstructure
commands subsystems). The result is a single recursive pattern: a robot is a *tree of identically
shaped blocks*, a motor at the leaves and an executive at the root.

---

## 0. The claim, stated precisely

A **block** is a tuple `(Config, Command_in, State, Command_out)` of serializable data objects plus
one pure step:

```
configure(Config)                                    // once; parameters / calibration / identity
(State', Command_out[]) = update(Command_in, Observations)   // each tick: fold in → advance → emit
state() -> State                                     // read the exposed state
```

- **`Config`** — what you parameterize it with at construction (and a slow runtime door; §6).
- **`Command_in` (u)** — the intent you send it this tick: a setpoint, a goal, a mode request.
- **`State` (x)** — what it exposes: its estimate/measurement **and** its status/mode (§5).
- **`Command_out` (u′)** — the intents it emits for the blocks below it. *A block's `Command_out` is
  literally its children's `Command_in`.* Commands are the **edges** between blocks.

Everything else in this spec is consequences of that definition. The two load-bearing refinements,
up front, because they're where the naive version goes wrong:

1. **Emission is a return value, never a side-effect (§4).** A block computes its outgoing commands; an
   *outer* layer routes them to children. The block never reaches out and pushes. This is what keeps it
   pure — testable in sim, replayable, ROS-translatable.
2. **It's a discipline, not a base class (§9).** You don't make everything `extends Block<C,U,X,O>`.
   You make every component expose `Config`/`Command`/`State` as PODs and advance via one pure
   `update`. The convention is the deliverable; the `interface` is at most documentation.

---

## 1. Why this shape, and why trusting it is safe

You can arrive at this structure from first principles (every device is configured, commanded, read,
and may drive other devices) — but the reason to *trust* it is that it is the intersection of three
independent, battle-tested models:

- **The ROS 2 (lifecycle) node** — *parameters* (Config) + *subscriptions* (Command_in) +
  *publications* (State **and** Command_out) + internal state, under a managed lifecycle. An executive
  that "takes a goal, reports what it's doing, and issues commands" is a ROS **action server** exactly.
- **The actor model** — a thing with private state that receives messages, updates state, sends
  messages.
- **The block diagram** (Simulink / Modelica) — a *block* has parameters, input ports, output ports,
  and internal state, and you build the system by **wiring output ports to input ports**. This is the
  control-engineering-native model and it is precisely `Config` + `Command_in` + `State` +
  `Command_out`.

When a structure is simultaneously a ROS node, an actor, and a block diagram, it is not an
idiosyncrasy — it's load-bearing. Practically, that means we get to **steal their refinements** (§5–§8)
rather than rediscover them. It also continues doc 06's thesis (`../corpus-analysis/06-lessons-from-broader-robotics.md`):
FRC reinvents ROS's component structure in-process — so let's reinvent it *deliberately*.

---

## 2. The four channels are four serializable PODs

The whole value proposition rests on all four channels being **plain serializable data objects**, not
ad-hoc method calls. Because they're data:

- **Config / Command / State / Command_out can all be logged.** Snapshot every block's four PODs each
  tick and you have AdvantageKit-grade replay and telemetry *for the entire robot at every scale*, for
  free — the inputs-struct idea (`logging.md`, the swerve spec §6.1) generalized from motors to
  executives.
- **`update` over PODs is a pure function**, so any block is unit-testable by feeding recorded inputs
  and asserting on outputs — no hardware, no scheduler (`testing.md`).
- **The PODs cross to ROS** as messages/parameters with a translation table, not a rewrite (§7).

This is the same decision the motor spec made for `Command`/`MotorState` (named u/x, not
Inputs/Outputs, because the names must be frame-invariant and survive a change of reader). The
component model inherits that naming discipline verbatim and extends it to `Config` and `Command_out`.

---

## 3. The payoff: the fill-pattern *is* the taxonomy

The non-obvious result — the thing that makes this more than "restating the actor model" — is that
**which channels a block populates classifies what kind of component it is.** You don't need a separate
type hierarchy for sensors vs actuators vs controllers; the channel fill-pattern *is* the type:

| Component kind | Config | Cmd in (u) | State (x) | Cmd out (u′) | one-line |
|---|:--:|:--:|:--:|:--:|---|
| **Sensor** (color, light, optical-flow) | ✓ calibration | – | ✓ measurement | – | a pure source of observations |
| **Actuator / leaf** (motor) | ✓ | ✓ | ✓ | – | command in, state out, no children |
| **Estimator / observer** (`RobotState`) | ✓ std-devs | observations | ✓ fused estimate | – | a sensor that *fuses* (an observer in the control sense) |
| **Subsystem** (elevator, drive) | ✓ geometry, limits | ✓ setpoint | ✓ measured + atGoal | ✓ motor cmds | a controller over leaves |
| **Executive** (superstructure) | ✓ interlock table | ✓ driver goal | ✓ mode + readiness | ✓ subsystem goals | a controller over subsystems |

Three things fall out of this table:

1. **A subsystem and a superstructure are the *same kind*** — both populate all four channels; they
   differ only in whether their children are motors or subsystems. This is why "even the executive
   fits": a coordinator is just a block whose `Command_out` feeds subsystems instead of motors. The
   recursion is the feature.
2. **A sensor and an estimator differ by one channel** — the estimator takes observations *in* and
   fuses; the sensor only emits. `RobotState` is "a sensor that does work."
3. **The robot is a tree of blocks**, commands flowing **down** (`u` → `u′` → `u″`…: driver → executive
   → subsystem → motor → hardware) and state flowing **up** (x: hardware → motor → subsystem →
   estimator → executive). This is the three-layer hybrid of doc 06, expressed as one shape repeated at
   every layer.

---

## 4. The step is pure; routing is someone else's job

The single most important implementation rule. Model the step as a pure transform:

```
(State', Command_out[]) = update(Command_in, Observations)
```

— **not** as a block that holds references to its children and pushes commands into them. The
difference decides whether the whole edifice is testable:

- **Return-value form (do this):** `update` returns its outgoing commands. A test feeds a recorded
  `Command_in` + `Observations` and asserts on `(State', Command_out)` with zero hardware and no
  scheduler. Replay re-runs the same pure function over a log. ROS bridges it as publish-after-spin.
- **Push form (don't):** the block calls `child.setControl(...)` internally. Now it's coupled to its
  children's identities, the seam you protected in two specs is gone, and you can't test it in
  isolation.

So the "emit a command for something else" you started from is **the output of a pure function**, and
an *outer wiring layer* (a scheduler, the `RobotContainer`, the periodic loop) routes each block's
`Command_out` to the next block's `Command_in`. The block is ignorant of who consumes its output —
exactly as a block-diagram block doesn't know what's wired to its output port.

> Corollary — `Observations` vs `Command_in`. A block has two *inputs*: the command from above (its
> setpoint) and the measurements from below/sensors (its feedback). Keep them distinct. In leaf form
> they often fold into the IO inputs-struct (the motor's `MotorState` already carries its own
> measurements); at higher levels the observation channel is how state flows up (a subsystem observes
> its motors' `State`).

---

## 5. `State` is two things: estimate **and** status

You said it without noticing: an executive "has a state that tells you what it's doing." For a motor,
state is just the physical measurement (x). Above the leaf, state splits:

- **Estimate** — the measured/fused physical quantity (position, velocity, pose).
- **Status / mode** — what the block is *doing*: its FSM node, its current goal, `atGoal`/`isReady`
  flags, fault status.

For a motor these coincide (its state *is* its measurement). For a subsystem you need `atSetpoint`; for
an executive the status (which mode, is it interlocked, is it ready) is the *primary* output and the
estimate is secondary. So `State` carries **`{ estimate, status }`**, and the motor spec's caveat —
"`MotorState` is honest for a motor *specifically*" — is exactly this: up the tree, the status half
appears. (This is also why `RobotState` is named `…State`: state flows up, device → subsystem → world,
and naming every level `…State` reveals they're the same kind of thing at different scales.)

---

## 6. `Config` is parameters — mostly once, with a runtime door

Config is **identity / calibration that doesn't change within a control session**: CAN IDs, gear
ratios, wheel radius, deadbands, vision std-devs, interlock tables. Most of it is set at construction.
But some genuinely is retuned live — PID gains, current limits, vision trust, soft limits. ROS keeps
*parameters* separate from *topics* for precisely this reason, and so should we:

- **Config is its own channel, separate from `Command_in`.** Do not smear runtime-tunable gains into
  the per-tick command — that conflates slow structural change with fast intent and pollutes the
  command log.
- **Most config is write-once; a defined subset is runtime-settable** (a slow, low-rate input). Model
  it as parameters with a `reconfigure(partialConfig)` door, not as a constructor-only blob.

The boundary test: *if it changes every loop, it's a `Command`; if it identifies or calibrates the
block across a session, it's `Config`.*

---

## 7. Lifecycle and degradation — bake it into the shape

Doc 06 flags graceful degradation as the discipline FRC most conspicuously skips, and the universal
block is the right place to fix it once. A real component has a lifecycle, straight from ROS 2 managed
nodes:

```
constructed → configured → enabled → (running) → disabled → fault/degraded
```

Two concrete requirements that follow:

- **A `connected`/health field in `State.status`** (the swerve `ModuleIO` already has `driveConnected`,
  `turnConnected`; the CTRE state has `FailedDaqs`). Health is part of state, not an exception.
- **A null/degraded implementation is first-class** — the `*IONull` object (build-spec) is the block in
  its `fault` lifecycle state: it accepts commands, emits safe/zero outgoing commands, and reports
  `connected = false`. Degradation becomes *a lifecycle transition of the standard shape*, not a
  special case bolted on. This is the structural hook doc 06 §5 asked for.

---

## 8. Keep the message *semantics*, drop the message *transport*

You framed this as "conceptually send them messages," and that mental model is right — but the
implementation must not be a message bus. For one RIO + one coprocessor, a broker/pub-sub is the DDS
mimicry doc 06 explicitly warns against. So:

- **Keep the semantics:** typed, serializable, loggable PODs; pure `update`; explicit Config/Command/
  State/Command_out. Everything that makes the actor model good.
- **Drop the transport:** no broker, no in-process event bus. Wiring is **direct typed calls and
  explicit composition** — the outer layer calls `child.update(parent.commandOut)` in dependency order.

The actor model is the *mental model*; in-process function calls over PODs are the *implementation*.
You get the decoupling from the typed PODs and the pure step, not from a transport. (When a real
second process appears — a coprocessor doing vision — *that* link, and only that one, becomes an actual
message; see the ROS bridge below.)

---

## 9. It's a discipline, not a base class

The failure mode of every "universal component interface" is the **inner-platform effect**: you write
`Block<Config, CmdIn, State, CmdOut>`, everything inherits it, four type parameters metastasize through
every signature, and the interface constrains nothing because it's maximally generic — real work
happens in casts and the abstraction is pure ceremony. Java generics with four parameters get ugly
fast, and a god-interface that fits a color sensor *and* a superstructure necessarily says almost
nothing.

So the component model is delivered the way the motor spec is — as a **contract you follow**, not a
superclass you extend:

> Every component (a) takes a `Config` POD, (b) accepts a `Command` POD, (c) exposes a `State` POD
> (estimate + status), (d) advances via one pure `update` that *returns* its outgoing commands, and (e)
> obeys the lifecycle. Each is its own concrete types; there is no shared `Block` supertype carrying
> them.

Followed consistently, that convention buys uniform logging, replay, sim-testing, and ROS-bridging at
every scale — which is the entire point — *without* a lowest-common-denominator interface. The
`interface Block<…>` may exist as documentation or for a generic scheduler, but nothing depends on
inheriting it.

---

## 10. Where it lands — the existing specs are instances

This spec doesn't replace the motor and swerve specs; it's the genus they're species of.

| Block | `Config` | `Command_in` | `State` | `Command_out` | spec |
|---|---|---|---|---|---|
| **Motor** (leaf) | CAN id, gains, inverts, limits | `Command` (u: voltage/velocity/position oneof) | `MotorState` (x) | — | [`portable-motor-interface.md`](portable-motor-interface.md) |
| **Swerve module** | `ModuleConstants` (gear, radius, location, offset) | `SwerveModuleState` setpoint | module measured state | 2× motor `Command` | [`portable-swerve-interface.md`](portable-swerve-interface.md) L1–L2 |
| **Drive subsystem** | track geometry, slip current | `SwerveRequest` (L4 union) | `SwerveDriveState` (pose + speeds + atGoal) | 4× module setpoints (+ gyro read up) | swerve spec L3–L4 |
| **`RobotState`** | vision std-devs | observations (odom, vision) | fused `Pose2d` + confidence | — (pure observer) | build-spec D7 |
| **Superstructure** | interlock table, goal graph | driver/auto goal | FSM mode + readiness | per-subsystem goals | build-spec D2 |

`portable-motor-interface` is "the block contract specialized to a leaf actuator." `portable-swerve-interface`
is "a mid-level block (the drive subsystem) whose children are four module blocks, each two motor
blocks." Writing this parent spec **retro-justifies** both: their `Command`/`State`/`Config` choices
aren't local conventions, they're this one shape applied at two altitudes. The swerve spec's
"seam-granularity" finding (§3.3 there) is just *at what level you draw a block boundary* — per-module
blocks vs one per-drivetrain block.

---

## 11. ROS bridge (because the shape is a ROS node)

A block maps to a ROS 2 node with no impedance mismatch — which is the proof it's the right factoring:

| Block channel | ROS 2 |
|---|---|
| `Config` (write-once + runtime door) | node **parameters** (+ `set_parameters`) |
| `Command_in` (setpoint) | a subscribed **topic**, or a **goal** for a long-running action |
| `State` (estimate + status) | a published **topic** (estimate) + the action **feedback/result** (status) |
| `Command_out` | topics **published** to downstream nodes |
| lifecycle | a **managed (lifecycle) node**'s states |
| `update` | the node's **spin**/`update()` callback |

The executive-as-action-server falls right out: goal in (`Command_in`), feedback = "what it's doing"
(`State.status`), and it commands subsystems (`Command_out`). The bridge is a translation table, not a
rewrite — and only an *inter-process* edge (RIO ↔ coprocessor) ever becomes a real message; everything
on the RIO stays in-process calls (§8).

---

## 12. Naming — decide it now, before it propagates

By your own rule (a name must survive a change of reader; don't import a term the destination domain
already spent), the noun for this thing needs deliberate choice — most candidates are taken:

| Candidate | Verdict |
|---|---|
| **`Block`** | **recommended.** From block diagrams — the exact config-in/ports/state model — and it makes the wiring metaphor ("wire output ports to input ports") native. Least-spent in application software (basic-block / blockchain live in different contexts and rarely collide in robot code). |
| `Component` | acceptable runner-up; ROS uses it for composable nodes. Mildly spent (UI components) but understood. |
| `Node` | reject — graph node, linked-list node, ROS node, k8s node; maximally overloaded. |
| `Unit` | **reject hard** — collides with WPILib's `Units` measure library *in this very codebase*. |
| `Module` | reject — collides with swerve **module** and Java **modules**. |

Recommendation: **`Block`** for the thing, and keep naming the *data objects* for what they are
(`Config`, `Command` = u, `State` = x, and the emitted `Command`s) — because, as with the motor spec,
the PODs are the stars and the wrapper noun is secondary. Whatever is chosen, the leaf-edge hardware
adapters keep their established `…IO` suffix (`MotorIO`, `ModuleIO`): an `…IO` is the downward edge of
a leaf `Block`, not a competing concept.

---

## 13. Summary of decisions

1. **A component is a configured transfer function with memory:** `Config` once, then
   `(State', Command_out[]) = update(Command_in, Observations)` each tick. Four serializable PODs + one
   pure step.
2. **The fill-pattern is the taxonomy** — sensor / actuator / estimator / subsystem / executive are
   distinguished by which of the four channels they populate, not by separate hierarchies.
3. **Emission is a return value, not a side-effect** — the block computes `Command_out`; an outer layer
   routes it. This is what keeps every block pure, testable, and replayable.
4. **`State` = estimate + status**; **`Config` = parameters (mostly once, with a runtime door)**, kept
   separate from per-tick `Command`.
5. **Lifecycle and degradation are part of the shape** — `connected`/health in `State.status`, the
   `*IONull` block as the `fault` state (doc 06 §5).
6. **Keep message semantics, drop message transport** — typed loggable PODs + pure update + explicit
   in-process wiring; no bus for one RIO.
7. **A discipline, not a base class** — no god-`interface` everyone inherits; the convention is the
   deliverable.
8. **The motor and swerve specs are instances** — this is their genus; it retro-justifies their
   `Command`/`State`/`Config` choices as one shape at two altitudes.
9. **Name it `Block`** (block-diagram lineage), keep the PODs named for what they are, keep `…IO` for
   the hardware edge.

The one-line version: **a robot is a tree of blocks — each one configured, commanded, observed, and
emitting commands to the block below — and the kind of block is just which channels it uses.**

---

## Pointers (sources & lineage)

This is a design synthesis, not a corpus measurement; its *instances* are corpus-grounded in the specs
it generalizes. The lineage:

- **ROS 2 node / lifecycle node / action server** — parameters, topics, managed states; the closest
  existing realization of this shape. (See doc 06 Pointers for ROS references.)
- **Actor model** — Hewitt actors: private state, receive/send messages.
- **Block diagrams** — Simulink / Modelica blocks: parameters + input/output ports + internal state;
  composition by port wiring. The naming and the "transfer function with memory" framing come from here.
- **Control theory** — the plant/observer/controller split (`../alternatives/02-physical-plant-simulation.md`);
  `Command` = u, `State` = x is the state-space pair.
- **BRICS "5 Cs"** (Computation, Communication, Coordination, Configuration, Composition) — the
  academic articulation that `Config` and `Composition` are first-class, not afterthoughts.

## See also (internal)

- [`portable-motor-interface.md`](portable-motor-interface.md) — the **leaf** instance; source of the
  `Command`/`MotorState` = u/x naming this spec generalizes.
- [`portable-swerve-interface.md`](portable-swerve-interface.md) — the **mid-level** instance (a drive
  subsystem block over module blocks over motor blocks); its seam-granularity = where you draw block
  boundaries.
- [`../corpus-analysis/06-lessons-from-broader-robotics.md`](../archived/corpus-analysis/06-lessons-from-broader-robotics.md) —
  the ROS-node/lifecycle/three-layer lineage and the "semantics not transport" rule (§0, §5, §7).
- [`../corpus-analysis/03-io-layer-strategy-pattern.md`](../archived/corpus-analysis/03-io-layer-strategy-pattern.md) —
  why the leaf edge is ports-and-adapters.
- [`../corpus-analysis/08-drivetrain-as-architecture.md`](../corpus-analysis/08-drivetrain-as-architecture.md) —
  the empirical drivetrain-as-three-roles (device / subsystem / world-model anchor) that this model
  generalizes: those three roles are three points on the block tree.

## Open questions

1. **Does `Observations` deserve its own named channel, or does it fold into `update`'s inputs?** Leaf
   blocks carry their own measurements in `State`; higher blocks observe children's `State`. Decide
   whether to model the feedback path explicitly or leave it as "read your children's state."
2. **One generic scheduler, or hand-wired composition?** A generic outer loop that topologically sorts
   blocks and routes `Command_out → Command_in` is possible (and very ROS-like). Decide whether that's
   worth building or whether explicit wiring in `RobotContainer` is clearer at FRC scale.
3. **Promote to a build-spec recipe?** If this holds up, `scaffold-robot`/`add-subsystem` could emit
   every component to this contract by default. Decide whether the model is stable enough to bake into
   the generators.
