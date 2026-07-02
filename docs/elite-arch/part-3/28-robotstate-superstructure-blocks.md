---
title: 28. RobotState and Superstructure as blocks
weight: 28
---
The motor and swerve chapters recovered the bottom two layers as blocks. This chapter does the same
for the two *higher* seams of Part I — the world model and the coordinator — and in doing so collects
the payoff promised in [ch. 24](24-elite-to-league.md): the seams that looked like three different
shapes turn out to be the same block at different altitudes.

## `RobotState` is an estimator block

The state seam ([ch. 4](../part-1/04-the-state-seam.md)) is a block with an unusual fill-pattern: it is
**a sensor that fuses.** Its channels:

- **`Config`** — the vision standard deviations and trust weights.
- **`Command_in`** — empty. Nobody commands an estimate; what flows *into* this block — odometry from
  the drive, timestamped pose measurements from vision — arrives via the `Observations` channel, as
  the `State` of its designated peers ([ch. 25](25-portable-component-model.md)).
- **`State`** — the fused `Pose2d` plus confidence (and, at the elite end, game-piece and mechanism
  state).
- **`Command_out`** — none. It commands nothing; it only emits an estimate.

```d2
direction: right
DR: Drive subsystem
VIS: Vision subsystem
RS: "RobotState (estimator block)
Config: vision std-devs
update(observations) → fused estimate"
CONS: "Consumers: Auto · Path · Aim · Superstructure"
DR -> RS: "odometry (observations)" { style.stroke-dash: 4 }
VIS -> RS: "vision poses (observations)" { style.stroke-dash: 4 }
RS -> CONS: "State (estimate)" 
```

In control terms it is an **observer** — the block that infers hidden state from measurements — which
is exactly why pose estimation belongs in its own block rather than privately inside the drive
subsystem. The mechanics (the time-interpolating buffer, the fusion math) are Part II
([ch. 20](../part-2/20-the-world-model.md)); the point here is structural: both command channels are
empty — everything it consumes arrives as `Observations`, and it emits nothing but `State` — and that
emptiness is what distinguishes an estimator from a controller.

There is one honesty note, which [ch. 32](32-open-questions.md) returns to. `RobotState` does not sit
in the command tree — nobody *commands* it and it commands nothing. It is a **cross-cutting peer**, a
shared blackboard that many blocks read. Commands form a tree; state, with `RobotState` as a hub, forms
a DAG. Same block contract, different wiring.

## `Superstructure` is an executive block

The coordination seam ([ch. 5](../part-1/05-the-coordination-seam.md)) is a block that fills **all
four** channels:

- **`Config`** — the interlock table and the goal graph.
- **`Command_in`** — one robot-wide goal from the driver or an autonomous routine.
- **`State`** — its FSM mode and readiness flags (here the *status* half of state is the primary
  output; the estimate is secondary).
- **`Command_out`** — a per-subsystem goal for each mechanism.

```d2
direction: down
DRV: Driver / Auto
SUP: "Superstructure (executive block)
Config: interlock table, goal graph
update(goal, observations) → subsystem goals"
S1: Elevator subsystem
S2: Arm subsystem
S3: Intake subsystem
RS: RobotState
DRV -> SUP: goal
SUP -> S1: setpoint
SUP -> S2: setpoint
SUP -> S3: setpoint
RS -> SUP: "pose / situation (observations)" { style.stroke-dash: 4 }
```

It is a controller whose plant is *other subsystems* instead of motors. The guarded transition function
that turns one goal into a legal sequence of setpoints — and holds the interlocks in one place — is
just this block's `update`.

## Why a subsystem and an executive are the same kind

Set the two side by side and the recursion is plain. A **subsystem** fills all four channels and its
`Command_out` feeds *motors*. A **superstructure** fills all four channels and its `Command_out` feeds
*subsystems*. Nothing else differs. The executive is not a special top-level construct; it is a block
whose children happen to be other blocks. This is what lets the model claim "even the coordinator
fits": the same interfaces carry intent downward and state upward at every altitude.

It is also why every level's exposed POD is named `…State`, and why above the leaf that `State` splits
into an estimate half and a status half — the argument is [ch. 25's](25-portable-component-model.md),
and these two blocks are its extreme instances: `RobotState` is nearly all estimate, the
superstructure's state nearly all status.

| Block | `Config` | `Command_in` | `State` | `Command_out` |
|---|---|---|---|---|
| **Motor** (leaf) | CAN id, gains | voltage/velocity/position | `MotorState` | — |
| **Swerve module** | gear, radius, offset | module setpoint | measured state | 2× motor command |
| **Drive subsystem** | track geometry | `SwerveRequest` | `SwerveDriveState` | 4× module setpoints |
| **`RobotState`** | vision std-devs | — | fused pose + confidence | — |
| **Superstructure** | interlock table | driver/auto goal | mode + readiness | per-subsystem goals |

(`RobotState`'s row has an empty `Command_in` by design — odometry and vision poses reach it as
`Observations`, not as commands.)

Read the table top to bottom and it is one shape applied at five altitudes — the genus
([ch. 25](25-portable-component-model.md)) and its species. The deep dives for these two seams are Part
II ([the world model](../part-2/20-the-world-model.md); coordination in
[ch. 22](../part-2/22-coordination-state-machines.md) and [ch. 23](../part-2/23-coordination-graphs-trees.md));
what Part III adds is that they are not separate inventions but the same block. The next three chapters
collect what that uniformity buys: [telemetry, replay, and tests for free](29-telemetry-replay-tests.md).
