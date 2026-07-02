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

**Block.** The one recurring shape: a configured transfer function with memory. A block takes `Config`
once, then each tick runs a pure step `(State′, Command_out[]) = update(Command_in, Observations)`. A
motor is a block, a subsystem is a block, and the superstructure is a block — they differ only in
which of the four channels they populate and in whether their children are motors or subsystems. The
robot is a tree of blocks, commands flowing down and state flowing up. See
[the Portable Component Model](../part-3/25-portable-component-model.md).

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

**RobotState.** The central world model — the single object every subsystem writes its measurements
into and every consumer reads its estimates out of, so no one reads a raw sensor twice. In block
terms it is an *estimator*: a block that takes observations in and emits a fused estimate, "a sensor
that does work." See [the state seam](../part-1/04-the-state-seam.md).

**Superstructure.** The coordination block — the one place that decides what every subsystem should be
doing, enforcing interlocks and sequencing so no button-binding has to. It is structurally the *same
kind of block* as a subsystem; it differs only in that its `Command_out` feeds subsystems rather than
motors. See [the coordination seam](../part-1/05-the-coordination-seam.md).

## The IO layer vocabulary

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

**Vendor confinement (the vendor-confinement rule).** The single non-negotiable of the IO layer: a
vendor type — `com.ctre.*`, `com.revrobotics.*`, `org.photonvision.*` — may appear *only below the IO
line*, inside a concrete `XxxIO<device>` implementation. It must never appear in a subsystem, in
`RobotState`, in the `Superstructure`, or in any test. This is what makes hardware swaps and sim local
to one file.

## Command / state vocabulary

**`u` / `x` (Command / State).** The two data channels every block carries, named after the
state-space control pair: `u` is the *command* flowing in from above (the setpoint), `x` is the
*state* flowing back — `Command` and `State`. The names were chosen to be frame-invariant: they mean
the same thing no matter who reads them, at every altitude of the tree. See the naming rationale
below.

**Config / Command / State / Command_out.** The four serializable channels ("PODs") of a block:

- **`Config`** — identity and calibration set (mostly) once per session: CAN IDs, gear ratios, gains,
  limits, standard deviations. Kept separate from per-tick data, with a runtime door for the rare
  parameter that must change live.
- **`Command`** (`u`) — the per-tick command in, from the block above.
- **`State`** (`x`) — the per-tick state out: estimate + status (below).
- **`Command_out`** (`u′`) — the commands this block emits *downward* to its children, returned as a
  value, never pushed as a side-effect.

**Estimate vs status.** The two halves of `State`. The **estimate** is the measured or fused physical
quantity — position, velocity, pose. The **status** is what the block is *doing* — its FSM node,
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

**Why `Block`, not Component / Node / Unit / Module.** The recurring shape needed a noun, and most
candidates collide:

- **`Node`** — rejected: graph node, linked-list node, ROS node, k8s node all claim it; maximally
  overloaded.
- **`Unit`** — rejected hard: collides with WPILib's `Units` measure library *in this very codebase*.
- **`Module`** — rejected: collides with a swerve **module** and with Java **modules**.
- **`Component`** — acceptable runner-up, mildly spent (UI components) but understood; ROS uses it for
  composable nodes.
- **`Block`** — chosen. It comes straight from block diagrams — the exact config-in / ports /
  internal-state model — so the wiring metaphor ("wire output ports to input ports") is native to the
  word. It is the least-spent option in application software: *basic-block* and *blockchain* live in
  distant contexts and rarely collide in robot code.

**Why `XxxIOTalonFX`, not `XxxIOReal`.** The real implementation is named for the *device it drives*,
not for the abstract fact that it is "the real one." `ElevatorIOTalonFX` tells you at a glance what
hardware is below the line, and it scales: when a mechanism has a Kraken variant and a NEO variant, or
a comp-bot and a practice-bot with different electronics, `…Real` gives you a name collision while
`…TalonFX` / `…SparkMax` / `…Comp` stay distinct and self-documenting. "Real" also lies in REPLAY,
where nothing is real; the device name never does.

**Why `Command` / `State`, not `Input` / `Output`.** The channels are named for what they *are* in
control terms (`u` command, `x` state), not for their direction relative to some particular reader.
"Input" and "Output" are reader-relative: one block's output is the next block's input, so the words
flip meaning as you move through the tree and stop meaning anything stable. `Command` and `State` are
frame-invariant — a command is a command whether you are sending or receiving it, and state is state
whether you measure it or read it — which is exactly the property a name needs to survive a change of
reader across every level of the block tree. See
[the Portable Component Model](../part-3/25-portable-component-model.md).
