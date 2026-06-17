# Coordination as Graph Search — State Graphs and A* Over Configuration Space

*Sketch / reminder, not a full build-out. The good idea: model the superstructure as a **graph of states**
and **search** for the safe transition path, instead of hand-coding every from→to sequence. At the far end,
run **A\*** over a discretized **configuration space** to plan to arbitrary configs the way you already
pathfind the drivetrain across the field.*

> **Status:** established but **uncommon in FRC**, standard in robotics at large. Not novel — this is the
> `alternatives/` bar (sound, uncommon, situational), not an invention. The eventual full doc should pick a
> rung (below) and build it out.

## The idea in one paragraph

Hand-coded coordination is an N² problem: for every (from-state → to-state) pair you write the ordered,
interlock-safe sequence by hand, and get them subtly wrong. Model it as a graph instead — **nodes = states,
edges = legal single moves, an edge existing only if that move is collision-free** — and you declare the
safety rules *once, locally*, then let a shortest-path search compose any from→to into a globally safe
sequence. The interlocks stop being scattered `if` checks and become **edge existence**. That representation
is the prize; the search algorithm is a detail set by graph size.

## The rungs (climb only as far as collision complexity forces)

1. **Flat enum FSM** — `Stow/Intake/Score` + a few guards. Correct for a 3-state robot with no self-collision
   coupling. The default; not this doc.
2. **Named-state graph + precomputed shortest path** *(established in elite FRC, uncommon)*. ~10–30 hand-named
   states; BFS/Dijkstra computes all-pairs paths **once at startup** → O(1), deterministic runtime lookup.
   **A\* buys nothing at this scale** — its heuristic only saves node expansions. This is the tractable,
   provably-safe sweet spot; start here.
3. **Discretized C-space + online A\*** *(standard in general robotics, rare in FRC)*. Grid the joint space
   (elevator × arm × wrist), edges = collision-free micro-moves, A\* with an admissible heuristic
   (config-space distance ÷ max joint speed) plans a smooth safe path **at runtime**. Buys **arbitrary**
   target configs (not just named states) and **dynamic** collision geometry (a held game piece changes
   which edges exist → replan). Costs: bounded runtime in the 20 ms loop, heuristic design, a defined
   no-path fallback.

## Why it's a good idea

- **Provable safety / verifiable coordination.** A graph can be exhaustively tested where hand-coded
  transitions cannot: assert every (from, to) path is collision-free and terminates, that the graph is
  connected (or unreachable states are intentional), that no edge violates an interlock. Same
  "materialize-the-structure-then-test-it" payoff as the plant (`02-physical-plant-simulation.md`).
- **Kills the N² hand-coding** and moves interlocks to one local place (edge construction).
- **Clean replanning/interruptibility** — you're always at a node or on an edge, so a new goal just means
  "finish the current edge (or safe-stop), replan from the next node."

## The framing that makes A* click

You already A\*-pathfind the **drivetrain**: PathPlanner's `pathfindToPose` is `LocalADStar` (Anytime
Dynamic A\*) routing the chassis around field obstacles in real time (**35 corpus teams**). Rung 3 is the
*same algorithm in a different space* — search `(elevatorHeight, armAngle, wristAngle)` in configuration
space, where "obstacles" are self-collision regions, instead of `(x, y, θ)` on the field.

## Corpus reality check (`data/code-index.duckdb`)

- `Superstructure` coordinator: **28** teams · state-machine/`RobotManager` FSM: **17** · named-state enums: **34**.
- Explicit state-graph/transition types: **~5** (190, 254, 2910, 3476, 5026).
- Genuine A\*-over-the-superstructure: effectively **254 alone** (`AStarSolver`, `AStarMap`, `cachedAStar`,
  a state graph). **Dijkstra: 0** (at small graph sizes people hardcode or BFS).
- A\*-family for the **drivetrain** (PathPlanner ADStar): **35** — the technique is proven and familiar; this
  idea just points it at the superstructure.

## Design hinges (decide when building out)

- **Edge cost = time-to-execute** → search finds the *fastest* safe sequence, not fewest steps.
- **A\* heuristic must be admissible** or you lose optimality.
- **Precompute for small graphs; bound-and-cache online A\* for large ones** (254 literally has `cachedAStar`).
- **Define the no-path fallback** (hold, or route to a known-safe state) — a blocked/disconnected graph is a
  real runtime state.

## When not to

A few states with no real self-collision coupling → a flat enum FSM is correct. The graph pays off with many
states, *real* interlocks, a desire for provable safety, or a need for arbitrary (non-named) target configs.

## Pointers

- **Reference implementation:** 254's released code in the corpus — `frc_team_repos/254-cheesy-poofs/…`
  (`AStarSolver.java`, `AStarMap`, `cachedAStar`, the state graph). The corpus's one full instance.
- **Drivetrain analogue:** PathPlanner `pathfindToPose` / `LocalADStar` (Anytime Dynamic A\*).
- **Theory:** configuration-space motion planning (Lozano-Pérez); discrete grid + A\* for low-DOF, sampling
  planners (RRT/PRM) for high-DOF. General-robotics stacks: MoveIt / OMPL.
- **The seam this extends:** `../build-spec/subsystems/08-superstructure.md` (coordination seam, "where
  interlocks live, … eventually a state graph") and rubric **D2** (coordination & decision logic).

## Open question for the full write-up

Which rung to center on — **named-state graph** (paved, deterministic, provably safe, A\* optional) or
**C-space A\*** (arbitrary configs, dynamic obstacles, borrowed from general robotics)? They share the
"coordination = graph search" spine but diverge hard on cost and capability.
