---
title: 9. Cross-cutting practices
weight: 9
---
Three practices separate engineering culture from cargo cult, and all three are **dividends of the IO
seam** ([ch. 5](05-the-io-seam.md)) rather than independent features. Build the seam and they become
available; the work is collecting them. This chapter is what they are and why teams leave most of them
on the floor. The harnesses and code are [Part II ch. 9 territory](../part-2/) — here, the shape.

## Simulation (D3)

Simulation runs your *actual* robot code with the physical robot replaced by a model. Because the
subsystem holds an `XxxIO`, the sim is just a different implementation of it — `XxxIOSim` — selected
at the one run-mode branch. The value scales with fidelity, and that scale is the D3 ladder:

| D3 | Fidelity | What you get |
|---|---|---|
| 1 | `simulationPeriodic` stub echoing setpoints | "it runs without a robot" |
| 2 | WPILib mechanism sims (`ElevatorSim`, `FlywheelSim`…) in the `IOSim` | the controller actually has to converge |
| 3 | whole-robot dynamics (maple-sim) + vision sim | the sim can surprise you |
| 4 | deterministic replay of a real match | re-run the actual robot on actual data |

The threshold that matters is level 2: a sim that echoes setpoints only proves the code doesn't crash;
a sim with real physics constants (measured mass, MOI, gearing) makes the controller earn its
convergence and can reveal an overshoot or an unstable loop before the robot exists. The corpus
mindset is to treat sim as a *separate robot with its own tuning* — same code path, different
constants — which is exactly what makes it trustworthy.

## Testing (D4)

A test constructs part of the robot, drives it, and asserts what it did. The defining FRC fact:
almost no one does it. D4 is the rarest, most discriminating marker in the corpus — most teams score
0 — and it barely correlates with winning ([ch. 11](11-what-it-predicts.md)). That is the point.
Tests don't put points on the board; they are the clearest signal of software-engineering culture and
the thing that lets a program move fast without breaking itself.

The reason it's rare is that it has a prerequisite — the IO seam — and the reason it's *possible* is
that you already built it. The key idea: **the `XxxIO` interface and its `XxxIOSim` are the test
double.** No Mockito, no mocking framework — to test a subsystem you hand it the sim implementation;
to test a command or the superstructure, you build the subsystems on sim one level down. The
highest-value test is the interlock test: build several subsystems in sim, request a dangerous goal,
and assert the safe ordering held — the failure that physically breaks robots, caught on a laptop.

## Logging (D5)

"When the robot misbehaves between two qualifier matches, with no laptop attached, how do we know
why?" Logging is the answer, and the bar is not "print some numbers" — it's "reconstruct the failure
afterward." That reconstruction is impossible with `println` and trivial with a logged inputs struct,
which is why the seam captures every hardware reading in one place.

| D5 | Stack | What it is |
|---|---|---|
| 0–1 | `println` / `SmartDashboard` | live-only, not recorded |
| 2 | DogLog / Epilogue | structured logging to a recorded file + NetworkTables |
| 3 | AdvantageKit | `@AutoLog` inputs + `Logger.processInputs` across every subsystem |
| 4 | replay + diagnostics | log replay exercised; self-check fault reporting |

Logging is the one advanced practice that has gone near-universal among serious teams — AdvantageKit
appears in 26 corpus teams, with Epilogue, DogLog, and URCL trailing. The jump that matters is level
1 → 2: from live-only dashboard values to a *recorded* log you can open after the match. And the
decision between stacks is real, not a default — AdvantageKit buys deterministic replay at the cost of
run-mode plumbing and strict IO discipline; DogLog buys telemetry now and skips replay. Because both
consume the same `Inputs` struct, the choice is deferrable and the migration touches `Robot.java`, not
the subsystems.

## The dividend almost no one collects

The three practices chain: filling `IOSim` (an afternoon) unlocks both unit tests and — once a
`REPLAY` run mode is wired — deterministic replay of a real match through unchanged code. The corpus
finding is blunt: the IO seam exists in 24 teams, every one of them has the inputs struct replay
consumes, and about **one** team actually ships a replay variant. The foundation already paid for the
dividend; collecting it is the clearest marker of real software culture, and the subject of
[ch. 12](12-foundation-first.md).
