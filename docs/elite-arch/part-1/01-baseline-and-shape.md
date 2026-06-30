---
title: 1. The baseline and the shape
weight: 1
---
Every WPILib team starts from the same place. The Elite Architecture is best understood not as a
thing teams build from scratch but as a specific set of additions to that shared starting point — so
this chapter names the starting point, then names the two lenses the rest of Part I reads the
architecture through. A reader who finishes it knows *what* the architecture is made of and *how the
next seven chapters look at it.*

## The starting point: two nouns

WPILib hands every team the **command-based framework**, which splits robot code into two kinds of
thing:

- **Subsystems** are the mechanisms the robot *has* — a drivetrain, an elevator, a claw. Each is a
  class that owns its hardware (the motor and sensor objects) and exposes methods. The scheduler
  guarantees only one command uses a subsystem at a time, so two pieces of code never fight over the
  same motor.
- **Commands** are the things the robot *does* — drive to a pose, raise the elevator, run a scoring
  sequence. They *require* one or more subsystems and compose into sequential and parallel groups.

`RobotContainer` is the wiring root: it constructs the subsystems, binds them to controller buttons,
and selects the autonomous routine. This is real modularity — but it is shallow, and the shape of its
coupling is the entire plot of the rest of the book.

```d2
direction: down
OI: "RobotContainer
(button bindings, auto select)"
CMD: "Commands
(things the robot does)"
SUB: "Subsystems
(things the robot has)"
HW: "Motor & sensor objects
(TalonFX, PhotonCamera, ...)"
OI -> CMD
CMD -> SUB: calls subsystem methods
SUB -> HW: holds concrete devices
SUB.style.fill: "#1f3a5a"
SUB.style.font-color: "#ffffff"
HW.style.fill: "#5a1f1f"
HW.style.font-color: "#ffffff"
```

Two joints carry all the coupling. A command holds a *concrete* subsystem reference; a subsystem
holds *concrete* motor objects. Almost everything elite teams do is insert a planned boundary at one
of those two joints — and the corpus does it in a consistent direction. **Below the line** (between
subsystem and devices) teams insert an interface that makes a real motor, a simulated motor, and a
replayed motor interchangeable. **Above the line** (between intent and the subsystems) they insert a
coordinator and a shared world model, so a button requests a *goal* rather than poking motors, and
decisions read from one fused estimate.

## Modularity is a ladder, not a binary

The most useful framing from the survey is that decoupling is not on or off. A program climbs: the
command/subsystem split WPILib hands you, then an IO layer below it, then a coordinating state machine
or graph above it, then a library/robot separation that survives across seasons, and — for the few
who need it — message-passing process isolation. The rungs are not adopted in lockstep: a team can
have a clean IO layer and no coordinator, or strong logging bolted onto baseline command code. That
unevenness is why the architecture is worth seeing from several angles before judging any one team
against it. (How to score where a program sits on these rungs is the subject of the
[How We Developed This](../appendices/how-we-developed-this/) appendix.)

Naming the baseline as the zero is not a way to disparage it. Baseline command-based is *correct*, and
for most rungs of most seasons it is enough to win regional matches. The point of fixing it as the
reference is to make the additions legible: every later chapter is a specific, motivated answer to a
specific pain the baseline leaves open.

## Two ways to see the architecture

The same architecture rewards two complementary readings, and Part I gives you both.

The first lens is **positive space — the views.** It asks *where the parts are*: which subsystems
exist and how they relate, the libraries they stack on, how data flows on each 20 ms tick, and what
physical hardware they run on. This is the classic [4+1 view model](02-five-views.md), and it is where
Part I starts, because you orient faster by seeing the whole board than by being handed one piece at a
time.

The second lens is **negative space — the seams.** It asks about *the joints between the parts*: the
three planned boundaries — [IO](03-the-io-seam.md), [state](04-the-state-seam.md), and
[coordination](05-the-coordination-seam.md) — that a team cuts once so that later capability plugs in
instead of forcing a rewrite. The views show you the rooms; the seams show you the load-bearing walls.

These two lenses carry the organizing principle of the whole architecture, which is worth stating once
up front: **build the seams, defer the payoffs.** Cut the boundaries early and each advanced
capability — simulation, tests, replay, vision fusion, smart coordination — becomes an *addition at a
known point* rather than a rewrite. That is why a team can grow from a working regional robot to a
top-tier program without the offseason rewrites that sink most teams.

The next chapter draws the board: the architecture in five views.
