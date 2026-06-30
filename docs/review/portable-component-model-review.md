# Review: Portable Component Model Spec

**Date:** 2026-06-30
**Reviewer:** AI analysis (Hermes Agent)
**Spec under review:** `knowledge/specs/portable-component-model.md`
**Related specs:** `portable-motor-interface.md`, `portable-swerve-interface.md`

---

## Overall Verdict

This is **genuinely good design work** — the kind of structural thinking that could raise the ceiling on FRC architecture. The four-channel model (`Config`, `Command_in`, `State`, `Command_out`) is minimal, well-grounded in control theory + actor model + ROS lineage, and it earns its keep. I have substantive concerns, but they're at the implementation/practicality level, not at the conceptual level.

---

## What's Strong

### 1. The four-channel abstraction is the right factorization

The tuple `(Config, Command_in, State, Command_out)` as four serializable PODs + one pure `update` captures what every active thing in a robot does without overfitting to any particular altitude. Two things fall out:

- **The fill-pattern taxonomy table (§3) is elegant.** A sensor populates Config+State. An actuator adds Command_in. A subsystem/executive adds Command_out. Which channels a block populates *is* what kind of component it is — no arbitrary type hierarchy, no separate taxonomies for sensors vs actuators vs controllers.

- **It retro-justifies the motor and swerve specs cleanly (§10).** The motor spec is "the block contract specialized to a leaf actuator" — Config=CAN id+gains, Command=u, State=x, no Command_out. The swerve spec is "a mid-level block whose children are four module blocks, each two motor blocks." Both specs are stronger for being instances of something larger.

### 2. The pure-function discipline is the load-bearing rule

> `(State', Command_out[]) = update(Command_in, Observations)` — a return value, not a side effect.

This is the correct call and the spec argues it well. The comparison to the push model (§4) gets the stakes right: if a block calls `child.setControl(...)` internally, it's coupled to its children's identities, the D1 seam is gone above the leaf, and you can't test in isolation. Emission-as-return-value means every block is testable with recorded inputs, replayable from logs, and ROS-bridgeable without rewriting. This is the D1 IO-seam principle applied recursively up the whole tree.

### 3. The ROS / actor / block-diagram lineage provides real confidence

Showing that this shape is simultaneously a ROS lifecycle node, an actor, and a Simulink block (§1) means it isn't idiosyncratic — it's the intersection of three independent, battle-tested models. The ROS bridge table (§11: Config↔parameters, Command_in↔subscribed topic, State↔published topic + action feedback, Command_out↔published topics) maps cleanly with no impedance mismatch. When a structure is independently arrived at by three very different communities, it's probably load-bearing.

### 4. "Discipline, not a base class" is the correct instinct

The inner-platform warning (§9) is real and well-stated: `Block<Config, CmdIn, State, CmdOut>` with four Java generics would metastasize through every signature and constrain nothing because it's maximally generic. The motor spec already proved this approach works — expose PODs, follow the contract, no shared supertype. This spec applies the same discipline at every altitude.

### 5. Lifecycle baked into the shape is right

The `*IONull` as the block in its `fault` lifecycle state (§7) is a concrete, implementable hook for graceful degradation — the exact thing doc 06 §5 called for. Making `connected`/health part of `State.status` rather than an exception path means degradation is a lifecycle transition of the standard shape, not a special case bolted on afterward.

### 6. Naming shows good taste

Rejecting `Unit` (collision with WPILib `Units`), `Module` (collision with swerve *modules*), and `Node` (maximally overloaded) for the right reasons. `Block` from block diagrams is the right choice — least-spent in application software, and it makes the "wire output ports to input ports" metaphor native.

---

## Concerns and Gaps

### 1. The `Observations` channel is under-specified (Open Question #1)

This is the biggest unresolved design tension. The block signature includes `Observations` as an input, but:

- **The taxonomy table has no `Observations` column.** How does a sensor's measurement get *into* the parent block? The text says "state flows up" — but is a parent's `Observations` simply its children's `State` PODs, collected by the routing layer? If so, `Observations` isn't a distinct fifth channel; it's "the children's State, gathered before update()."

- **The estimator row illustrates the problem.** The table says `Cmd in: –` for an estimator, but the text says it "takes observations *in*." Observations aren't Command_in (they're not intent), but the table has no column for them. The four-channel model implicitly has *five* channels once you account for the feedback path.

- **The corollary in §4** acknowledges the distinction — "Command_in is the setpoint from above; Observations is the feedback from below/sensors" — but doesn't close on whether Observations is a named channel or an implementation detail of the routing layer.

**Recommendation:** Model the feedback path explicitly — a block's `Observations` input is the set of its children's most recent `State`, collected by the outer routing layer, not by the block itself. Then `update(Command_in, ChildrensState)` and the four-channel taxonomy survives without a fifth column. Close Open Question #1 with that decision.

### 2. The tree model has a real tension with `RobotState`

"Commands flow down, state flows up" works perfectly for command flow — it's strictly hierarchical. But state doesn't always flow in a tree. `RobotState` is a **cross-cutting peer**, not a node in the command hierarchy:

- The drive subsystem feeds odometry into it
- Vision feeds measurements into it
- The superstructure *reads* from it for field-relative targeting
- Other subsystems may read from it for targeting

Calling `RobotState` "a sensor that does work" (§3) acknowledges the oddity but doesn't resolve it. In a pure tree, `RobotState` would be a parent whose children are the drive subsystem and vision — but that inverts the actual power relationship (the superstructure doesn't command `RobotState`; `RobotState` doesn't command the drive). It's a shared blackboard — an observer in the control-theory sense — not a node in a command hierarchy.

This isn't fatal — you can have a tree for command flow and a DAG for state flow — but the spec claims "the robot is a tree of blocks" without qualifying that state consumers form a *different* graph than command flow.

**Recommendation:** Acknowledge the dual-graph explicitly. Commands form a tree (top-down). State forms a DAG (can flow to multiple consumers, including cross-cutting ones like `RobotState`). The block contract is the same shape in both graphs; it's the *wiring* that differs.

### 3. Execution order in a tick needs explicit treatment

If every block calls `update()` once per tick, and `Command_out` feeds children's `Command_in`, you need an execution model. Two natural options:

- **Two-pass:** Top-down command pass (executive → subsystem → motor), then bottom-up state pass (motor → subsystem → executive). Implicit in the spec but never stated.
- **Single-pass with previous-tick commands:** Children update before parents, using the *previous* tick's commands. Simple but introduces a one-tick lag between command issuance and state reflection.

For a spec that insists on concrete implementation discipline (§4, §9), the execution model deserves at least a paragraph.

**Recommendation:** Commit to the two-pass model (command pass, then state pass). It's the natural fit for the "commands down, state up" metaphor and avoids the one-tick lag. State it explicitly.

### 4. The routing layer is the unbuilt bridge (Open Question #2)

`Command_out[]` is an array — but which child gets which command? The spec says "an outer wiring layer routes each block's `Command_out` to the next block's `Command_in`" without specifying the mapping. Two plausible models:

- **Index-based:** Children are ordered; `Command_out[0]` goes to child 0. Fragile — reordering children breaks the wiring silently.
- **Named/targeted:** Each emitted command carries a target child identifier. The routing layer dispatches by name. More robust but adds ceremony.

**Recommendation:** Prefer explicit hand-wired composition in `RobotContainer.periodic()` for FRC scale (as the spec leans toward in §8). It's clearer, debuggable, and fits the "semantics not transport" rule. The question isn't "generic scheduler vs hand-wired" — it's "do we provide a helper that validates the wiring graph for completeness?" That helper (check that every block's `Command_out[]` has corresponding consumers, every `Command_in` has a producer) would be more valuable than a generic topological scheduler.

### 5. WPILib integration is the elephant

The pure-function discipline is elegant, but FRC robots run on WPILib's `CommandScheduler`. To adopt this model, a team either:

- **(a) Replaces** WPILib's scheduler with a custom executor that calls `update()` in dependency order. High ceremony, high payoff — but you're fighting the framework.
- **(b) Wraps** each block in a WPILib `Subsystem` whose `periodic()` delegates to `update()`, with explicit wiring in `RobotContainer`. Lower ceremony, keeps WPILib integration.

The spec gestures at both (§4: "a scheduler, the `RobotContainer`, the periodic loop") but doesn't commit.

**Recommendation:** Endorse option (b) as the pragmatic path. A block is a `Subsystem` whose `periodic()` calls `update()`; the wiring lives in `RobotContainer.periodic()` as explicit calls. This keeps the pure-function contract intact while working *with* WPILib rather than against it. The spec should show a concrete wiring example.

### 6. Config's boundary with Command gets blurry at altitude

A motor's Config (CAN ID, gear ratio, gains) is clearly "once at construction." But §6 says a superstructure's Config is an "interlock table" — is that static? What about reconfiguring between matches (adding a climber, switching auto routines, toggling a mechanism on/off)?

The boundary test — "if it changes every loop, it's a `Command`; if it identifies or calibrates the block across a session, it's `Config`" — only covers the extremes. There's a "changes between matches but not during" gray area that neither Config nor Command cleanly owns.

The `reconfigure(partialConfig)` door helps, but it conflates two different concerns: runtime parameter tuning (PID gains — genuinely "slow Config update") and structural reconfiguration (interlock tables, enabled mechanisms — essentially a mode switch). These deserve different mechanisms.

**Recommendation:** Split `reconfigure` into two doors: `tune(partialConfig)` for runtime parameter adjustment (gains, limits) and `reconfigure(partialConfig)` for structural changes (interlock tables, mechanism enable/disable). The distinction matters because mode switches may require lifecycle transitions (disable → reconfigure → re-enable), while tuning does not.

---

## What's Missing

1. **No treatment of the scheduler/routing layer concretely.** For a spec that says "follow this contract," the thing that *enforces* the contract — calls `update()`, routes `Command_out[]`, collects children's `State` as `Observations` — is the biggest missing piece. The open questions acknowledge this but the spec should close on answers.

2. **No bridging advice for WPILib.** Every FRC team adopting this model would need to decide: replace the scheduler, or wrap blocks in WPILib primitives. The spec should pick one and show a concrete example.

3. **The Observations channel needs a decision, not an open question.** It's central enough to the block contract that punting on it undermines the spec's concreteness.

4. **No treatment of `RobotState`'s cross-cutting nature.** It's the only block in the taxonomy that doesn't fit the pure tree model cleanly, and the spec's "sensor that does work" characterization avoids the structural question.

---

## Summary: Ready to Close

The spec is **conceptually ready**. The four-channel model, the pure-function discipline, the fill-pattern taxonomy, and the ROS lineage are all correct and well-argued. The motor and swerve specs are genuinely instances of it.

Before promoting to a build-spec recipe (Open Question #3), close the two load-bearing open questions:

| # | Question | Recommended resolution |
|---|---|---|
| 1 | Observations channel | Model it as "children's State, collected by the routing layer" — no fifth channel. |
| 2 | Scheduler vs. hand-wired | Endorse hand-wired in `RobotContainer.periodic()` for FRC scale; provide a graph-validation helper. |

And address the three structural gaps:

| Gap | Action |
|---|---|
| Execution order | State the two-pass model explicitly (command pass down, state pass up). |
| `RobotState` cross-cutting | Acknowledge the dual-graph: commands form a tree, state consumers form a DAG. |
| Config vs. mode switches | Split `reconfigure` into `tune()` (parameter) and `reconfigure()` (structural); structural changes may require lifecycle transitions. |

With those resolved, the Portable Component Model becomes the genus the motor and swerve specs are species of — not just in theory, but in a form teams can actually wire up and run.