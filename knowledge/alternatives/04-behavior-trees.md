# Behavior Trees — Reactive, Composable Decision-Making

*Quick overview / reminder. A **behavior tree (BT)** structures "what should the robot do right now?" as a
tree that is re-evaluated ("ticked") every control cycle. A third answer to coordination, alongside the FSM
and the state-graph (`03-state-graph-coordination.md`) — it sits at the **strategy** layer, not the
mechanism layer.*

> **Status:** rare as an *explicit* BT in FRC; the command-based **cousin** is universal (see corpus check).
> Origin: game AI (Halo, mid-2000s) as a scalable replacement for FSMs; now standard in robotics (ROS2 Nav2,
> BehaviorTree.CPP). Maps onto WPILib's 20 ms loop — you tick the tree in `periodic()`.

## How it works

Each cycle the tree is ticked from the **root** down. Every node returns one of three statuses:

- **SUCCESS** — done, worked.
- **FAILURE** — done, didn't work.
- **RUNNING** — still going, tick me again next cycle. *(The key invention — lets an action span many ticks.)*

**Leaves** do the work: **Action** (run intake, drive to pose — returns RUNNING while busy) and **Condition**
(have a piece? at setpoint? — returns SUCCESS/FAILURE instantly).

**Composites** are the control flow:
- **Sequence** (→): children left-to-right; **fail fast**, succeed only if all succeed. Logical **AND** / "do in order."
- **Selector / Fallback** (?): children left-to-right; **succeed fast**, fail only if all fail. Logical **OR** / "try in priority order."
- **Parallel**: tick all children; resolve by a policy (succeed if M of N).

**Decorators** wrap one child: `Inverter`, `Repeat`, `Retry`, `Timeout`, `Cooldown`, condition guards.

## The headline idea: reactive priority for free

```
Selector  (priority — re-checked top→bottom EVERY tick)
├─ Sequence:  [being rammed?]    → [evade]
├─ Sequence:  [have piece?]      → [drive to goal] → [score]
├─ Sequence:  [piece visible?]   → [drive to piece] → [intake]
└─ [drive to staging / idle]
```

Because the whole tree re-ticks from the root each cycle, the top selector re-evaluates priorities
constantly: the instant `being rammed?` goes true, control jumps to *evade*, then back when it clears — with
**no explicit transitions wired**. In an FSM you'd hand-add an "→ evade" edge from every state. That's the
BT pitch: priority and preemption fall out of *structure*, not out of N² transitions.

## Strengths / tradeoffs

**Good:** modular (subtrees are graftable), scales linearly (add a node, not edges to/from everything),
reactivity/preemption built in.

**Costs:**
- **"Where am I?" is fuzzier** — no single nameable current state; it's implicit in which leaves are RUNNING + the blackboard. Harder to debug/log than an FSM.
- **State lives in a "blackboard"** — BTs are stateless control flow; shared data (target pose, have-piece) sits in a separate key-value store nodes read/write. A real coupling surface.
- **Memory-sequence gotcha** — a naive Sequence re-ticks from its first child each cycle; you usually want a *memory* variant so completed steps don't re-run.
- **It doesn't plan.** A BT is a hand-authored *reactive policy*, not a planner — it picks *what to pursue*, it doesn't *compute* a safe path the way `03`'s A*/state-graph does. Correctness is emergent, not analyzable like a graph.

## FRC: you're already half-using one

WPILib command-based is a BT cousin in disguise:

| BT | WPILib |
|---|---|
| Sequence | `SequentialCommandGroup` |
| Parallel | `ParallelCommandGroup` / `Race` / `Deadline` |
| Selector | `ConditionalCommand` / `SelectCommand` |
| Decorators | `.withTimeout()` `.until()` `.unless()` `.repeatedly()` |
| RUNNING / SUCCESS | `isFinished()` + interruption |

The delta that makes a *real* BT interesting: teams use command groups for **fixed autonomous routines**;
a BT is used as a **whole-robot reactive brain** (opportunistic play: "grab the closest piece unless
defended, else reposition"), re-deciding every tick.

## Where it sits next to the others (they compose)

- **Behavior tree** → *strategy* layer: "what to pursue now?" Reactive, modular; weak on explicit state / proof.
- **State graph + A\*** (`03`) → *mechanism* layer: "how to move the superstructure safely?" Computed, verifiable.
- **FSM** → either, at small scale; spaghetti as transitions multiply.

Clean stack: a BT action leaf emits a *goal* ("score high"); the superstructure (graph or FSM) executes it
safely. **BT decides intent; graph-search executes it.**

## Corpus reality check (`data/code-index.duckdb`)

- Explicit BT (BT-node/blackboard/tick tokens): **~1 team** (3015) — essentially absent.
- Command-based cousins: `SequentialCommandGroup` **49t**, parallel groups **37t**, `Conditional`/`SelectCommand` **23t** — universal.
- Takeaway: the *building blocks* are everywhere; using them as a top-level **reactive** tree is the unexplored part.

## Pointers

- Origin & theory: game-AI behavior trees (Halo); *Behavior Trees in Robotics and AI* (Colledanchise & Ögren).
- Libraries/tools: **BehaviorTree.CPP** + Groot editor; **ROS2 Nav2** (navigation as a BT).
- Related here: `03-state-graph-coordination.md` (the mechanism-layer partner), `../build-spec/subsystems/08-superstructure.md` (the coordination seam), rubric **D2**.

## Open question for any full write-up

Is the real FRC story "**use a true BT as the top-level brain**," or "**command-based already gives you 80% —
here's the 20% delta** (a persistent reactive root tick + a blackboard) worth adding"? Decide before building out.
