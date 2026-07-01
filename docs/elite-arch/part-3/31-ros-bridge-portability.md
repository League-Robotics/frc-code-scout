---
title: 31. The ROS bridge and language portability
weight: 31
---
The last argument for the block model is also its proof of correctness. If the four-channel shape is
the right factoring of a robot component, it should map onto the broader field's component model — the
ROS 2 node — with no impedance mismatch. It does, exactly, and that is not a coincidence to admire but
a capability to use.

## A block is a ROS 2 node

Each block channel has a ROS 2 counterpart, one-for-one:

| Block channel | ROS 2 |
|---|---|
| `Config` (write-once + runtime door) | node **parameters** (+ `set_parameters`) |
| `Command_in` (setpoint) | a subscribed **topic**, or a **goal** for a long-running action |
| `State` (estimate + status) | a published **topic** (estimate) + the action **feedback/result** (status) |
| `Command_out` | topics **published** to downstream nodes |
| lifecycle | a **managed (lifecycle) node**'s states |
| `update` | the node's **spin** / `update()` callback |

The executive-as-action-server falls right out: a goal arrives (`Command_in`), the feedback channel is
"what it's doing" (`State.status`), and it commands subsystems (`Command_out`). Because the shape *is*
a ROS node, the bridge is a translation table, not a rewrite — and because the motor and swerve PODs
are kept structurally isomorphic to their ROS message targets ([ch. 26](26-portable-motor-interface.md),
[ch. 27](27-portable-swerve-interface.md)), the table is mechanical: a swerve drive is a `Twist`-in /
`Odometry`-out node with four `JointState` pairs underneath, which is precisely `ros2_control`'s
swerve-controller shape.

## Keep the semantics, drop the transport

There is a trap here, and the model is explicit about avoiding it. The actor/ROS framing tempts you to
build a *message bus* — a broker, in-process pub/sub, DDS mimicry. For one roboRIO and one coprocessor,
that is ceremony with no payoff, and the outside-robotics survey warns against it directly. So the rule
is to **keep the message semantics and drop the message transport:**

- **Keep the semantics** — typed, serializable, loggable PODs; a pure `update`; explicit
  `Config`/`Command`/`State`/`Command_out`. Everything that makes the actor model good.
- **Drop the transport** — no broker, no event bus. Wiring is direct typed calls and explicit
  composition: the outer layer calls `child.update(parent.commandOut)` in dependency order.

The decoupling comes from the typed PODs and the pure step, not from a transport. A real message — an
actual serialized payload over a wire — appears at exactly **one** edge: the inter-process link between
the RIO and a vision coprocessor. Everything on the RIO stays in-process function calls over PODs.

```d2
direction: right
RIO: "roboRIO — one process" {
  EXEC: Executive block
  SUB: Subsystem block
  MOT: Motor block
  EXEC -> SUB: "update() call"
  SUB -> MOT: "update() call"
}
COP: "Coprocessor — separate process
(PhotonVision / Orange Pi)"
COP -> RIO: "the ONE real message
(vision pose over the wire)"
RIO.style.fill: "#1f3a5a"
RIO.style.font-color: "#ffffff"
```

The blocks inside the RIO are wired by direct calls — same semantics as messages, none of the
transport cost. Only the genuinely inter-process edge becomes a real message, and *that* edge is where
the ROS bridge earns its keep: the coprocessor can be a ROS node publishing a pose topic, and the RIO's
`RobotState` block consumes it through the same `Command_in` channel it would use for any observation.

## proto3 is the source of truth

What makes the whole thing language-neutral rather than Java-bound is that the channels are defined
once in **proto3**, not in a Java interface. From that single schema, `protoc` generates first-class
message types for the robot (Java) and the tools (Python, Rust, C++, TypeScript), the thin port shim is
generated for the long-tail targets, and the ROS bridge is generated from the two schemas by applying
the two conventions the motor chapter fixed (`None` ↔ `NaN`, `oneof` ↔ mode-enum). Add a control mode
and it is one `oneof` arm plus one enum constant, propagating to every binding, the capability set, and
the ROS mapping at once.

This is what "portable" in *the League Architecture* finally means. The Elite Architecture is portable
across *seasons* — the seam survives a rewrite. The block model is portable across *languages and
frameworks* too: the same component contract describes the robot in Java, a simulation in Python, a
controller in a ROS graph, and a tool in TypeScript, because the contract lives in a schema and maps
without loss onto the component model the rest of robotics already uses. The shape was never an FRC
idiosyncrasy; naming it deliberately is what lets a student's robot code speak the same language as the
field it is preparing them for.

One honest caveat closes the part: the model is a proposal with real unresolved seams of its own. The
[final chapter](32-open-questions.md) lays them out.
