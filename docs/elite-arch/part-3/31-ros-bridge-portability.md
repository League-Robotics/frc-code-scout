---
title: 31. The ROS bridge and language portability
weight: 31
---
The last argument for the component model is external. If the four-channel shape is a sound factoring of
a robot component, it should map cleanly onto the broader field's component model — the ROS 2 node. It
largely does, and the mapping is strong evidence that the factoring is conventional rather than
idiosyncratic — not a proof, but a capability to use.

## A component is a ROS 2 node

Each faceplate channel has a ROS 2 counterpart, one-for-one:

| Faceplate channel | ROS 2 |
|---|---|
| `Config` (write-once + runtime door) | node **parameters** (+ `set_parameters`) |
| `Command_in` (setpoint) | a subscribed **topic**, or a **goal** for a long-running action |
| `State` (estimate + status) | a published **topic** (estimate) + the action **feedback/result** (status) |
| `Command_out` | topics **published** to downstream nodes |
| lifecycle | a **managed (lifecycle) node**'s states |
| `update` | a **timer callback** (or `ros2_control`'s `ControllerInterface::update`) — not `spin`, which is the executor loop |

The executive-as-action-server falls right out: a goal arrives (`Command_in`), the feedback channel is
"what it's doing" (`State.status`), and it commands subsystems (`Command_out`). Because the shape *is*
a ROS node, the bridge is a translation table, not a rewrite — and because the motor and swerve PODs
are kept structurally isomorphic to their ROS message targets ([ch. 26](26-portable-motor-interface.md),
[ch. 27](27-portable-swerve-interface.md)), the table is mechanical: a swerve drive is a `Twist`-in /
`Odometry`-out node with four `JointState` pairs underneath — the shape a `ros2_control` swerve
controller takes (cf. `diff_drive_controller`; upstream ships no swerve controller, and the ones that
exist are third-party packages).

## What does not map

The table is a correspondence, not an identity, and three mismatches keep it honest. ROS topics are
asynchronous, many-to-many, and QoS-mediated — a publisher neither knows nor waits for its subscribers
— while component wiring is synchronous 1:1 calls in a fixed order. A ROS action goal has an
accept/reject/cancel handshake and runs for seconds, while `Command_in` is re-sent every 20 ms with no
handshake at all — so the executive-as-action-server analogy holds for the data (goal / feedback /
result), not the protocol. And executors, callback groups, and QoS profiles have no analog here,
because the component model deliberately has no transport to configure. The mapping earns its keep at the
one edge where a real message exists; it is not a claim that a robot of components *is* a ROS graph.

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
  EXEC: Executive
  SUB: Subsystem
  MOT: Motor
  EXEC -> SUB: "update() call"
  SUB -> MOT: "update() call"
}
COP: "Coprocessor — separate process
(PhotonVision / Orange Pi)"
COP -> RIO: "the ONE real message (vision pose over the wire)"
RIO.style.fill: "#1f3a5a"
RIO.style.font-color: "#ffffff"
```

The components inside the RIO are wired by direct calls — same semantics as messages, none of the
transport cost. Only the genuinely inter-process edge becomes a real message, and *that* edge is where
the ROS bridge earns its keep: the coprocessor can be a ROS node publishing a pose topic, and the RIO's
`RobotState` consumes it through the same `Command_in` channel it would use for any observation.

## proto3 is the source of truth

What makes the whole thing language-neutral rather than Java-bound is that the channels are defined
once in **proto3**, not in a Java interface. From that single schema, `protoc` generates first-class
message types for the robot (Java) and the tools (Python, Rust, C++, TypeScript); the thin port shim —
the `apply`/`read` interface of [ch. 26](26-portable-motor-interface.md) plus its POD structs, e.g. a
generated C++ or Python struct-and-adapter pair for a coprocessor target — is generated for the
long-tail targets; and the ROS bridge is generated from the two schemas by applying
the two conventions the motor chapter fixed (`None` ↔ `NaN`, `oneof` ↔ mode-enum). Add a control mode
and it is one `oneof` arm plus one enum constant, propagating to every binding, the capability set, and
the ROS mapping at once.

One boundary rule keeps the schema from becoming a 20 ms-loop garbage tax: the generated protobuf
types appear **only at the log-and-wire boundary**. In-loop, the channels are plain mutable
records/structs generated from the same schema — protobuf-java's immutable, builder-allocating
messages would churn the roboRIO's two-core garbage collector every tick, which is why WPILib itself
chose QuickBuffers over protobuf-java for its own serialization ([ch. 26](26-portable-motor-interface.md)).

This is what "portable" in *the League Architecture* finally means. The Elite Architecture is portable
across *seasons* — the seam survives a rewrite. The component model is portable across *languages and
frameworks* too: the same component contract describes the robot in Java, a simulation in Python, a
controller in a ROS graph, and a tool in TypeScript, because the contract lives in a schema and maps
without loss onto the component model the rest of robotics already uses. The shape was never an FRC
idiosyncrasy; naming it deliberately is what lets a student's robot code speak the same language as the
field it is preparing them for.

One honest caveat closes the part: the model is a proposal with real unresolved seams of its own. The
[final chapter](32-open-questions.md) lays them out.
