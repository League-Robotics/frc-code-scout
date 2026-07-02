---
title: 23. Coordination II — state graphs and behavior trees
weight: 23
---

*The wanted/current FSM and the centralized `RobotManager` of [the previous chapter](22-coordination-state-machines.md) are where most elite teams stop. This chapter walks the two rungs past them: modeling the superstructure as a graph of legal states and searching for a safe path, and ticking a behavior tree as a reactive whole-robot brain. [Chapter 5](../part-1/05-the-coordination-seam.md) drew the coordination seam and [chapter 8](../part-1/08-alternatives.md) pointed past it to both paradigms as sound-but-uncommon. Part I argued *why* a team would climb here; this chapter shows the machinery and, for each rung, says plainly when it earns its complexity and when it is over-engineering.*

The two paradigms live at different layers and compose rather than compete. The state graph is a mechanism-layer answer to "how do I move the superstructure there *safely*?" — established but uncommon in the corpus, with configuration-space A\* as its far edge (effectively 254 alone). The behavior tree is a strategy-layer answer to a higher question — "what should the robot *pursue* right now?" — and is rarer still (one team, 3015). Beneath both sits the wanted/current FSM of [chapter 22](22-coordination-state-machines.md), the default coordination rung among elite teams. A clean stack would run top to bottom — a behavior tree decides intent ("score high"), the superstructure, graph or FSM, executes that intent safely — but no corpus team actually ships that composed stack. It is plausible, not observed.

---

## Part 1 — Coordination as graph search

### The N² problem the graph dissolves

Hand-coded coordination is an N² problem. For every `(from-state → to-state)` pair you write the ordered, interlock-safe sequence by hand, and get some of them subtly wrong. A robot with a stow state, a coral-intake state, and four scoring levels has on the order of `6 × 5 = 30` ordered transitions, each one a small sequence of "retract the wrist before the elevator moves, then raise, then extend." Every one is a place to forget an interlock. Add a state and you add transitions to and from every existing state.

Model it as a graph instead:

- **nodes** are states,
- **edges** are legal single moves, and
- **an edge exists only if that move is collision-free.**

You declare the safety rules once, locally, at edge-construction time, then let a shortest-path search compose any `from → to` request into a globally safe sequence. The interlocks stop being scattered `if` checks spread across thirty transition bodies and become *edge existence*. If a move would collide, the edge is not in the graph, so no path can route through it. That representation is the payoff; the search algorithm is a detail set by graph size.

```d2
direction: right
STOW -> CORAL_INTAKE
STOW -> L1
CORAL_INTAKE -> STOW
CORAL_INTAKE -> L2
L1 -> L2
L2 -> L3
L3 -> L4
L4 -> L3
L2 -> STOW
L4 -> STOW: "blocked: wrist clips elevator" { style.stroke-dash: 3 }
```

The dashed edge is the point: `L4 → STOW` directly would clip the wrist on the elevator, so that edge is simply absent. A request to go from `L4` to `STOW` finds the path `L4 → L3 → L2 → STOW` automatically. Nobody wrote that sequence. The search found it because those are the only edges that exist.

### The three rungs — climb only as far as collision complexity forces

The source survey lays out three rungs and is explicit that you should climb only as far as the mechanism's self-collision coupling demands.

**Rung 1 — flat enum FSM.** `Stow / Intake / Score` plus a few guards. Correct for a three-state robot with no self-collision coupling. This is the default and the subject of [chapter 22](22-coordination-state-machines.md), not this one.

**Rung 2 — named-state graph + precomputed shortest path.** *Established in elite FRC, uncommon.* Roughly 10–30 hand-named states; BFS or Dijkstra computes all-pairs paths **once at startup**, giving O(1) deterministic lookup at runtime. At this scale A\* buys nothing — its heuristic only saves node expansions, and there are few nodes to expand. This is the tractable, provably-safe sweet spot. Start here.

**Rung 3 — discretized configuration space + online A\*.** *Standard in general robotics, rare in FRC.* Grid the joint space (elevator × arm × wrist), make edges collision-free micro-moves, and run A\* with an admissible heuristic to plan a smooth, safe path **at runtime**. This buys two things the named-state graph cannot: **arbitrary** target configs rather than just named states, and **dynamic** collision geometry — a held game piece changes which edges exist, so you replan. The costs are bounded runtime inside the 20 ms loop, heuristic design, and a defined no-path fallback.

### The framing that makes A\* click

The A\* leap sounds exotic until you notice teams already run it — on the drivetrain. PathPlanner's `pathfindToPose` is `LocalADStar` (Anytime Dynamic A\*), routing the chassis around field obstacles in real time. The corpus survey counts **35 teams** running an A\*-family planner on the drivetrain. The technique is proven and familiar.

Rung 3 is the same algorithm in a different space. Instead of searching `(x, y, θ)` on the field where obstacles are walls and other robots, you search `(elevatorHeight, armAngle, wristAngle)` in configuration space where "obstacles" are self-collision regions. One layer up the robot, same idea.

```
drivetrain:    A* over (x, y, θ)            obstacles = field walls, robots
superstructure: A* over (elev, arm, wrist)  obstacles = self-collision volumes
```

### Corpus reality — established but uncommon

The survey's index counts, every one confirmed by reading source, place this paradigm precisely:

| Marker | Teams |
|---|---|
| `Superstructure` coordinator (any kind) | 28 |
| State-machine / `RobotManager` FSM | 17 |
| Named-state enums | 34 |
| Explicit state-graph / transition types | ~5 (190, 254, 2910, 3476, 5026) |
| A\* over the superstructure | effectively 254 alone |
| Dijkstra over the superstructure | 0 |
| A\*-family on the drivetrain (PathPlanner ADStar) | 35 |

One absence needs explaining: 6328, this chapter's worked example, is missing from the transition-type row. Its JGraphT-based graph is caught by a separate index marker — the `jgrapht` import, present in 3 teams — so the sweep for hand-rolled state-graph and transition types misses it by construction, not because the graph is unconfirmed.

Two readings stand out. Dijkstra is at zero because at small graph sizes people hardcode or BFS — nobody reaches for a weighted shortest-path algorithm on a 20-node graph. And genuine A\*-over-the-superstructure is a corpus of one.

### 6328 — the superstructure as a literal directed graph

Team 6328 (Mechanical Advantage) model the superstructure as a directed graph using the JGraphT library. States like `STOW`, `CORAL_INTAKE`, and `L4_CORAL` are graph vertices; the commands that move between them are edges. To reach a target the code runs a graph search and executes the edge commands along the resulting path.

The shape, abridged from the survey's description:

```java
// States are vertices; transition commands are edges.
Graph<SuperState, EdgeCommand> graph =
    new DefaultDirectedGraph<>(EdgeCommand.class);

graph.addVertex(SuperState.STOW);
graph.addVertex(SuperState.CORAL_INTAKE);
graph.addVertex(SuperState.L4_CORAL);
// ... ~10-30 named states

// An edge exists only for a legal, collision-free single move.
// The interlock IS the edge: an illegal move is simply not added.
graph.addEdge(SuperState.STOW, SuperState.CORAL_INTAKE, intakeEdge);
graph.addEdge(SuperState.CORAL_INTAKE, SuperState.L4_CORAL, raiseEdge);

// To honor a request: search, then run the edge commands in order.
List<EdgeCommand> path =
    DijkstraShortestPath.findPathBetween(graph, current, goal).getEdgeList();
```

One abridgment to flag: the snippet closes with JGraphT's `DijkstraShortestPath` because it is the one-line way to show the search, but 6328's shipped code walks the graph with its own BFS — which is why the corpus table above scores "Dijkstra over the superstructure" at zero.

The line worth dwelling on is the comment: *the interlock is the edge.* The survey states it directly — "the transition logic is data (a graph), not a tangle of if-statements." You never write `if (current == L4 && goal == STOW) { ... }`. You add the edges that are safe, omit the ones that are not, and the search composes the rest.

### 254 — A\* over the state graph

Team 254 take the same "superstructure = shortest path through a state graph" idea and name it outright. Their code carries an `AStarSolver`, an `AStarMap`, a `cachedAStar`, and a `SuperstructureStateMachine`, alongside a `CoralStateTracker` for game-piece state. The survey calls two of the strongest teams in FRC independently arriving at this representation the clearest convergence in the whole study.

```java
// 254's coordination names the algorithm and caches the result.
AStarSolver solver = new AStarSolver(stateGraph, heuristic);

// cachedAStar: bound-and-cache online search so the 20 ms loop stays predictable.
List<SuperState> path = cachedAStar.solve(current, goal);
```

The `cachedAStar` name is the design hinge made literal. Online A\* costs runtime; caching solved paths keeps the per-cycle cost bounded. This is the rung-3 discipline: precompute for small graphs, bound-and-cache online A\* for large ones.

A neighbor pattern from Team 1678 (Citrus Circuits) is worth naming here even though it is not a graph. Where most teams fold collision avoidance into the state graph, 1678 pull it into a separate `MotionPlanner` that owns the geometry — including a command named `UnsafePivotAndElevatorSynchronousToPositionMotionMagic` that coordinates two axes so they arrive together without colliding. Separating "where we want to be" (the superstructure's state) from "what path through space is safe to get there" (the planner) is the same decomposition the graph makes, reached by a different route.

### Why the graph is worth it

Three properties fall out of materializing the structure:

- **It can be exhaustively tested where hand-coded transitions cannot.** With the graph as data, you can assert that every `(from, to)` path is collision-free and terminates, that the graph is connected (or that unreachable states are intentional), and that no edge violates an interlock. Hand-coded transition bodies offer no such handle — you can only test the cases you remember to write. This is the same materialize-the-structure-then-test-it payoff that simulation gets from a physical plant.
- **It kills the N² hand-coding** and moves every interlock to one local place: edge construction.
- **Replanning and interruptibility are clean.** You are always at a node or partway along an edge, so a new goal means "finish the current edge or safe-stop, then replan from the next node."

### Design hinges, decided when building out

- **Edge cost = time-to-execute.** Then the search finds the *fastest* safe sequence, not merely the fewest steps.
- **An A\* heuristic must be admissible** (for example, configuration-space distance divided by max joint speed) or you lose the optimality guarantee.
- **Precompute for small graphs; bound-and-cache online A\* for large ones.** 254 literally ships `cachedAStar`.
- **Define the no-path fallback** — hold, or route to a known-safe state. A blocked or disconnected graph is a real runtime state, not an impossible one. A held game piece can delete the edges that would otherwise get you home.

### When not to build a graph

A few states with no real self-collision coupling means a flat enum FSM is correct, and the graph is over-engineering. The graph pays off only with many states, *real* interlocks, a wish for provable safety, or a need for arbitrary non-named target configs. The open question the survey leaves for any full build-out is which rung to center: the named-state graph (paved, deterministic, provably safe, A\* optional) or C-space A\* (arbitrary configs, dynamic obstacles, borrowed from general robotics). They share the "coordination = graph search" spine but diverge hard on cost and capability.

---

## Part 2 — Behavior trees

The state graph answers a mechanism-layer question: how do I move there safely? A behavior tree answers a different, higher question: what should the robot be doing at all? It sits at the strategy layer.

### How a behavior tree works

A behavior tree (BT) structures "what should the robot do right now?" as a tree that is re-evaluated — *ticked* — every control cycle. In WPILib terms, you tick the tree in `periodic()`, once per 20 ms loop. Each cycle the tree is ticked from the root down, and every node returns one of three statuses:

- **SUCCESS** — done, it worked.
- **FAILURE** — done, it didn't work.
- **RUNNING** — still going, tick me again next cycle.

`RUNNING` is the invention that makes the model work for robots. It lets a single action span many ticks: "drive to pose" returns `RUNNING` for as long as it takes, then `SUCCESS` once arrived, without blocking the loop.

### The node taxonomy

**Leaves** do the work and come in two kinds. An **Action** runs intake or drives to a pose and returns `RUNNING` while busy. A **Condition** asks a question — have a piece? at setpoint? — and returns `SUCCESS` or `FAILURE` instantly.

**Composites** are the control flow:

- **Sequence** (`→`): tick children left to right; **fail fast**, succeed only if all succeed. Logical AND, "do in order."
- **Selector / Fallback** (`?`): tick children left to right; **succeed fast**, fail only if all fail. Logical OR, "try in priority order."
- **Parallel**: tick all children; resolve by a policy such as "succeed if M of N succeed."

**Decorators** wrap a single child to modify its result: `Inverter`, `Repeat`, `Retry`, `Timeout`, `Cooldown`, condition guards.

**The blackboard** is shared working memory. BTs are stateless control flow, so any shared data — target pose, have-piece — lives in a separate key-value store that nodes read and write. This is a real coupling surface, not a detail to wave away.

### The headline: reactive priority for free

```
Selector  (priority — re-checked top to bottom EVERY tick)
├─ Sequence:  [being rammed?]    → [evade]
├─ Sequence:  [have piece?]      → [drive to goal] → [score]
├─ Sequence:  [piece visible?]   → [drive to piece] → [intake]
└─ [drive to staging / idle]
```

Because the whole tree re-ticks from the root each cycle, the top selector re-evaluates priorities constantly. The instant `being rammed?` goes true, control jumps to *evade*; when it clears, control falls back to whatever the next-highest condition allows — with no explicit transitions wired. In an FSM you would hand-add an "→ evade" edge from every state, which is the N² transition problem from Part 1 in a new costume. In a BT, priority and preemption fall out of the tree's structure. Add a higher-priority branch at the top and every lower branch is preempted by it automatically.

### 3015 Ranger Robotics — the one full behavior-tree runtime

Where every other surveyed team coordinates mechanisms with commands, a state machine, or a state graph, Team 3015 (Ranger Robotics) built a behavior-tree runtime in Kotlin under `lib/behaviorTree/` and run their robot on it. The source carries the textbook taxonomy:

- **Leaf nodes:** `CommandRunner` (run a WPILib command as a tree leaf), `Wait`, `SetVariable`, `ClearVariable`.
- **Decorator nodes:** `ConditionDecorator`, `InfiniteLoop`, `Loop`, `LoopUntilSuccess`, `ForceFailure`, `IsVarSet`.
- **A blackboard:** shared named variables the nodes read and write.

Each node returns `Success` / `Failure` / `Running` every tick, exactly as a behavior tree should. The library is unit-tested, and 3015 ship a separate visual `behavior_tree_editor` application to author the trees. The base shape, abridged:

```kotlin
sealed interface NodeStatus
object Success : NodeStatus
object Failure : NodeStatus
object Running : NodeStatus

abstract class BehaviorNode {
    abstract fun tick(blackboard: Blackboard): NodeStatus
}

// A leaf that runs a WPILib command as a tree action.
class CommandRunner(private val command: Command) : BehaviorNode() {
    private var started = false
    override fun tick(blackboard: Blackboard): NodeStatus =
        when {
            !command.isScheduled && !started -> { command.schedule(); started = true; Running }
            command.isFinished               -> Success
            else                             -> Running
        }
    // abridged: 3015's real implementation also resets `started` on completion
    // and can return Failure (an interrupted command is not a success)
}

// A decorator that only ticks its child while a blackboard flag is set.
class ConditionDecorator(
    private val key: String,
    private val child: BehaviorNode
) : BehaviorNode() {
    override fun tick(blackboard: Blackboard): NodeStatus =
        if (blackboard.isSet(key)) child.tick(blackboard) else Failure
}
```

That `CommandRunner` leaf is the bridge: it lets the BT command WPILib's scheduler — the BT decides intent and the existing command-based machinery executes it. The survey places 3015 as the worked example for the rung where transitions outgrow a switch statement, and notes the library transfers directly to robotics and game AI outside FRC.

### You are already half-using one

WPILib command-based is a behavior-tree cousin in disguise. The mapping is close enough to be uncomfortable:

| Behavior tree | WPILib command-based |
|---|---|
| Sequence | `SequentialCommandGroup` |
| Parallel | `ParallelCommandGroup` / `Race` / `Deadline` |
| Selector | `ConditionalCommand` / `SelectCommand` |
| Decorators | `.withTimeout()` `.until()` `.unless()` `.repeatedly()` |
| RUNNING / SUCCESS | `isFinished()` + interruption |

The corpus counts confirm the building blocks are everywhere and the assembled tree is not:

| Marker | Teams |
|---|---|
| Explicit BT (BT-node / blackboard / tick tokens) | ~1 (3015) |
| `SequentialCommandGroup` | 49 |
| Parallel command groups | 37 |
| `ConditionalCommand` / `SelectCommand` | 23 |

The delta that makes a *real* BT interesting is not the node types — teams have those. It is how the tree is used. Teams use command groups for **fixed autonomous routines**: a `SequentialCommandGroup` is a pre-authored play that runs once. A behavior tree is used as a **whole-robot reactive brain** that re-decides every tick — "grab the closest piece unless defended, else reposition" — opportunistic play, not a scripted routine. The persistent reactive root tick plus a blackboard is the unexplored 20%.

### The costs, stated plainly

A behavior tree is not free, and the survey is direct about the tradeoffs:

- **"Where am I?" is fuzzier.** There is no single nameable current state. It is implicit in which leaves are `RUNNING` plus the blackboard contents. This is harder to debug and log than an FSM, where the current state is one enum value you can put on the dashboard. (3015 partly answer this with their visual editor.)
- **State lives in the blackboard.** Because BTs are stateless control flow, all shared data sits in a separate key-value store that many nodes touch. That store is a real coupling surface, and it is the place bugs hide.
- **The memory-sequence gotcha.** A naive Sequence re-ticks from its first child each cycle. You usually want a *memory* variant so completed steps do not re-run on the next tick.
- **It does not plan.** A BT is a hand-authored reactive policy, not a planner. It picks *what to pursue*; it does not *compute* a safe path the way Part 1's A\* and state graph do. Its correctness is emergent from the tree's structure, not analyzable the way a graph's all-pairs paths are. This is exactly why the clean stack puts a BT on top of a graph, not in place of it.

### When a BT beats an FSM, and when it is over-engineering

A BT earns its keep when the decision logic is deeply nested and reactive — many priorities that interrupt each other, where an FSM would need an "interrupt" edge from every state to every higher-priority behavior. It scales linearly: add a node, not edges to and from everything. It is over-engineering when the robot has a handful of states with clear linear transitions — there the FSM's single nameable current state is an asset, not a limitation, and the fuzziness of "which leaves are running" is pure cost. With explicit BTs at roughly one team in the corpus and command groups universal, the honest read is that most teams should keep using command groups for routines and an FSM for state, and reach for a reactive top-level tree only when opportunistic, preempting play is the actual problem.

---

## Where this leaves the coordination ladder

Across [chapter 22](22-coordination-state-machines.md) and this chapter the full ladder is now in view:

```
command composition  →  wanted/current FSM  →  centralized RobotManager FSM
        →  state graph (BFS/Dijkstra)  →  C-space A*        (mechanism layer)
        →  behavior tree as reactive brain                  (strategy layer)
```

Each rung is a refactor motivated by a problem the rung below could not absorb: hand-coded transitions get N²-tangled, so you make them data and search them; the decision logic itself gets too tangled for a switch, so you tick a tree. The mechanisms change every game; the ladder does not.

This is the last chapter of Part II. Across these chapters the architecture appeared as a stack of named seams — the [control path](15-control-path.md), the [hardware abstraction line](16-hardware-abstraction.md), [motor interfaces](17-motor-interfaces.md), [subsystem archetypes](18-subsystem-archetypes.md), the [drivetrain](19-the-drivetrain-subsystem.md), the [world model](20-the-world-model.md), [vision](21-vision-systems.md), and coordination ([state machines](22-coordination-state-machines.md), then graphs and trees here). Each was treated as its own kind of thing with its own rules.

[Part III — The League Architecture](../part-3/) argues they are not separate kinds of thing. It presents the unifying model in which every component — a motor, a subsystem, the superstructure, the whole robot — is one recursive shape repeated at different scales. The IO seam, the state seam, and the coordination seam you have been reading as nine distinct chapters turn out to be the same three joints, applied again and again. Read on there.
