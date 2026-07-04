---
title: Appendix B — Glossary & naming decisions
weight: 2
---
**Every load-bearing term in this book earns its place, and several were chosen against plausible
alternatives that were already spent.** This appendix is two things at once: a glossary of the terms
the architecture depends on, and a record of the naming decisions behind the few that were contested.
The rule that governed those decisions is the same one that governs the code — *a name must survive a
change of reader, and you do not import a word the destination domain has already spent.* Read the
definitions to understand the vocabulary; read the rationale entries to understand why the vocabulary
is what it is.

## Core terms

**Component.** The informal noun for any active thing on the robot — a motor, a sensor, a subsystem,
`RobotState`, the superstructure. Deliberately lowercase and never a type: there is no `Component`
supertype, only the shared shape below. See
[the Portable Component Model](../part-3/25-portable-component-model.md).

**Faceplate.** The one recurring shape: the four-channel interface every component presents, like a
rack module's front panel — the same jacks in the same places no matter what circuitry sits behind
them. A component takes `Config` once, then each tick runs a pure step
`(State′, Command_out[]) = update(Command_in, Observations)`. A motor, a subsystem, and the
superstructure present the same faceplate — they differ only in which of the four channels they
populate and in whether their children are motors or subsystems. The robot is a tree of components,
commands flowing down and state flowing up. *Faceplate* is a word of the book's prose, never a name in
the code: the concrete types keep their natural names, and the faceplate is the shape they all share.
See [the Portable Component Model](../part-3/25-portable-component-model.md).

**Seam.** A deliberate boundary in the code where one concern is cut off from another so each side can
change without disturbing the other. The architecture is built on three of them.

**The three seams.** The whole foundation reduces to three cuts:

- **The IO seam** — between a subsystem's logic and its physical devices (the hardware boundary).
- **The state seam** — between where a fact is *measured* and where it is *used*, mediated by a
  central world model (`RobotState`) rather than read directly off sensors.
- **The coordination seam** — between a subsystem's job (*run this mechanism well*) and the robot's
  job (*decide what all the mechanisms should be doing*), owned by the `Superstructure`.

See [the IO seam](../part-1/03-the-io-seam.md), [the state seam](../part-1/04-the-state-seam.md), and
[the coordination seam](../part-1/05-the-coordination-seam.md).

**IO line / IO seam.** The line between a subsystem's logic and its hardware. Above the line lives
mechanism intent and (often) the control loop; below it live the concrete device drivers. Its
defining rule is vendor confinement (below). "IO seam" names the *boundary*; "IO line" is the same
boundary viewed as a wall you must not let vendor types cross. See
[hardware abstraction and the IO line](../part-2/16-hardware-abstraction.md).

**Fill-pattern taxonomy.** How components are classified: not by a type hierarchy but by *which of the
faceplate's channels they populate* — a sensor emits `State` but takes no `Command`, an actuator the
reverse, an estimator turns `Observations` into an estimate, an executive's output is mostly status.
See [the Portable Component Model](../part-3/25-portable-component-model.md).

**RobotState.** The central world model — the single object every subsystem writes its measurements
into and every consumer reads its estimates out of, so no one reads a raw sensor twice. In faceplate
terms it is an *estimator*: a component that takes observations in and emits a fused estimate, "a
sensor that does work." See [the state seam](../part-1/04-the-state-seam.md).

**Superstructure.** The coordination component — the one place that decides what every subsystem should
be doing, enforcing interlocks and sequencing so no button-binding has to. It is structurally the *same
kind of component* as a subsystem; it differs only in that its `Command_out` feeds subsystems rather
than motors. See [the coordination seam](../part-1/05-the-coordination-seam.md).

## The IO layer vocabulary

**IO layer (location) vs hardware abstraction (property).** "IO layer" names a *location* — where the
boundary sits, one interface per subsystem at the logic/device line. "Hardware abstraction" names a
*property* — whether the control loop lives above or below that line. See
[hardware abstraction and the IO line](../part-2/16-hardware-abstraction.md).

**The IO quartet.** The four files that make up one subsystem's IO layer, generated together:

- **`XxxIO`** — the interface naming the hardware boundary (e.g. `ElevatorIO`, `GyroIO`, `ModuleIO`).
- **`XxxIOInputs`** — the inputs struct (below) the interface fills.
- **`XxxIO<device>`** — the real implementation, *named for the device it drives* (below), e.g.
  `ElevatorIOTalonFX`.
- **`XxxIOSim`** — the simulation implementation, backed by a WPILib physics model.

**Inputs struct.** A plain, serializable data object (`XxxIOInputs`) that carries everything crossing
the hardware boundary *upward* — position, velocity, applied voltage, current, temperature, a
`connected` flag. The interface exposes a single `updateInputs(inputs)` method that fills it, rather
than a fistful of getters. The reason it exists is logging: because every value crossing the boundary
lands in one recordable object, the whole match can be replayed through the real code. See
[hardware abstraction and the IO line](../part-2/16-hardware-abstraction.md).

**Null-object IO.** The do-nothing member of the IO family — a full, valid implementation whose
methods are deliberately empty, so a subsystem with unplugged hardware runs as a safe no-op instead of
crashing, and REPLAY has something inert to hold the seam open. Written either as a named class
(`ElevatorIONull`, `NoElevator`) or, where the interface's methods all default to empty, as an
anonymous `new ElevatorIO() {}` that costs zero files.

**Fault.** A detected abnormal condition — a disconnected device, a stale sensor — carried explicitly
as part of a component's *status* (and, at the seam, as the inputs struct's `connected` flag), so
degradation is a defined state rather than a crash.

**Vendor confinement (the vendor-confinement rule).** The single non-negotiable of the IO layer: a
vendor type — `com.ctre.*`, `com.revrobotics.*`, `org.photonvision.*` — may appear *only below the IO
line*, inside a concrete `XxxIO<device>` implementation. It must never appear in a subsystem, in
`RobotState`, in the `Superstructure`, or in any test. This is what makes hardware swaps and sim local
to one file.

## Command / state vocabulary

**`u` / `x` (Command / State).** The two data channels every component carries, named after the
state-space control pair: `u` is the *command* flowing in from above (the setpoint), `x` is the
*state* flowing back — `Command` and `State`. The names were chosen to be frame-invariant: they mean
the same thing no matter who reads them, at every altitude of the tree. See the naming rationale
below.

**Config / Command / State / Command_out.** The four serializable channels ("PODs") of the faceplate:

- **`Config`** — identity and calibration set (mostly) once per session: CAN IDs, gear ratios, gains,
  limits, standard deviations. Kept separate from per-tick data, with a runtime door for the rare
  parameter that must change live.
- **`Command`** (`u`) — the per-tick command in, from the component above.
- **`State`** (`x`) — the per-tick state out: estimate + status (below).
- **`Command_out`** (`u′`) — the commands this component emits *downward* to its children, returned as
  a value, never pushed as a side-effect.

**`Observations`.** The per-tick measurements a component receives from below — its children's `State`,
or, at a leaf, raw sensor readings crossing the boundary upward. The second argument of the pure
step, alongside `Command_in`.

**Goal vs setpoint (and wanted vs current).** A **goal** is a robot-wide requested outcome ("score
L4"); a **setpoint** is the numeric target one mechanism holds, derived from the goal by the
superstructure. **Wanted/current** (2910's names; *target* and *goal* are synonyms for the first)
is the two-enum pattern that keeps the requested state and the state actually in effect separate,
with a transition function as the only writer of the second. See
[coordination state machines](../part-2/22-coordination-state-machines.md).

**Estimate vs status.** The two halves of `State`. The **estimate** is the measured or fused physical
quantity — position, velocity, pose. The **status** is what the component is *doing* — its FSM node,
current goal, `atGoal`/`isReady` flags, fault state. For a motor the two coincide (its state *is* its
measurement); above the leaf they split, and for an executive the status is the *primary* output.

## Run modes & payoffs

**Run modes (REAL / SIM / REPLAY).** The three ways the same robot program runs, selected in exactly
one place at construction:

- **REAL** — the `XxxIO<device>` implementations talk to physical hardware.
- **SIM** — the `XxxIOSim` implementations talk to a physics model, so the whole robot runs on a
  laptop with no hardware.
- **REPLAY** — no-op IO holds the seams open while a recorded log feeds the inputs structs back
  through the unchanged logic, reproducing exactly what the robot decided.

**Deferred dividend.** The payoff of the IO seam that does not show up until later: because a subsystem
can be built with its `XxxIOSim`, it can be driven to completion in a CI test harness and asserted on
— unit testing robot code, which almost no team does and which the IO seam makes mechanically
possible. You pay the seam's cost up front; the testability dividend is deferred.

## Naming decisions

The following terms were chosen deliberately against alternatives that were already spent in a
neighboring domain. Each entry records the choice and why.

**Why *faceplate* (and how *block* lost).** The recurring shape needed a noun, and the search taught
us two things: most candidates collide, and the thing being named is the *interface shape*, not the
unit that presents it. The unit needs no reserved noun at all — lowercase *component* serves, and the
concrete types keep their natural names — but the shape needs a word the book can say precisely. It is
a **prose-only term**: it never appears as a type or identifier in code, which frees the choice to
optimize for the metaphor rather than for how it reads in a signature.

- **`Block`** — the original working name, chosen from block diagrams (the exact config-in / ports /
  internal-state model) as "the least-spent word in application software." That judgment missed the
  collision that matters most: **FTC's beginner programming language is literally called Blocks**, so
  for this book's own audience "rewrite your robot as blocks" reads as "go back to visual
  programming." Add code blocks and blocking calls, and the word fails the rule it was chosen under.
- **`Node`** — rejected: graph node, linked-list node, ROS node, k8s node all claim it; maximally
  overloaded.
- **`Unit`** — rejected hard: collides with WPILib's `Units` measure library *in this very codebase*.
- **`Module`** — rejected: collides with a swerve **module** and with Java **modules**.
- **`Panel`** — rejected: the destination domain has spent it on hardware (the Power Distribution
  Panel), Java has spent it (`JPanel`), and "elevator panel" confidently reads as a dashboard tab —
  the worst failure mode, a wrong meaning rather than a vague one.
- **`Jack`** — rejected for naming the wrong element: a jack is the socket you plug into, one endpoint
  of one wire, not the thing that has the sockets. Also a lifting mechanism teams literally build.
- **`Channels`** — rejected for self-collision: *channel* already names each of the four members, so
  the plural can't also name the whole; and in WPILib a channel is a roboRIO port number.
- **`Pinout`** / **`Signature`** — the runners-up, both sound: *pinout* is the electronics word for
  exactly this (a standard arrangement of connections many parts share, unused pins marked NC), and
  *signature* has the ML-module precedent for structurally-satisfied interfaces.
- **`Component`** — kept, but demoted to the informal unit noun rather than the shape's name; ROS 2
  uses it the same way for composable nodes.
- **Faceplate** — chosen. The rack-module image *is* the concept: every module presents the same jacks
  in the same places, whatever circuitry sits behind them; wiring is patching one module's output jack
  to another's input; and the fill-pattern taxonomy reads directly as *which jacks are populated*. The
  word is essentially unspent in robot code, and because it lives only in prose, its length never
  costs a signature.

**Why `XxxIOTalonFX`, not `XxxIOReal`.** The real implementation is named for the *device it drives*,
not for the abstract fact that it is "the real one." `ElevatorIOTalonFX` tells you at a glance what
hardware is below the line, and it scales: when a mechanism has a Kraken variant and a NEO variant, or
a comp-bot and a practice-bot with different electronics, `…Real` gives you a name collision while
`…TalonFX` / `…SparkMax` / `…Comp` stay distinct and self-documenting. "Real" also lies in REPLAY,
where nothing is real; the device name never does.

**Why `Command` / `State`, not `Input` / `Output`.** The channels are named for what they *are* in
control terms (`u` command, `x` state), not for their direction relative to some particular reader.
"Input" and "Output" are reader-relative: one component's output is the next component's input, so the
words flip meaning as you move through the tree and stop meaning anything stable. `Command` and `State`
are frame-invariant — a command is a command whether you are sending or receiving it, and state is
state whether you measure it or read it — which is exactly the property a name needs to survive a
change of reader across every level of the component tree. See
[the Portable Component Model](../part-3/25-portable-component-model.md).
