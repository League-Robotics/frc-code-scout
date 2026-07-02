---
title: 3. The novice-to-elite maturity ladder
weight: 3
---
The architecture is a destination; this chapter is the route. A program climbs to it over four or
five seasons, and the climb is governed by three rules that matter more than any pattern.

## The principle that governs everything

What separates the elite teams in the corpus is **not** that they know the fanciest pattern. It is
three habits that make every pattern learnable:

1. **They simulate** — so they can write and verify code without the robot.
2. **They review each other's code** — so quality survives a bad night and a graduating senior.
3. **They retain knowledge across classes** — so year 4 is not year 1 again with new students.

The architecture is the *vehicle* for teaching those habits, not the goal. Teach the IO layer to a
team that doesn't review code and you get cargo-cult ceremony. So every phase below pairs an
**engineering leap** with a **team-process leap**, and the process is the one that compounds.

Two rules govern the whole arc. First: **you rewrite in the offseason, never during build season.**
Each architectural leap is a radical change; the only safe time is May–December, practicing on last
year's game where you already know what "working" looks like. A team that tries to learn the IO layer
in February loses the regional. You can watch this rule play out in one team's four-year git log in
[the Patribots, four years](../../scoring/35-the-patribots-four-years.md), whose
elite-track rebuild landed in an offseason, not a build season. Second: **sequence by pain, not by prestige.** Each rung must be
motivated by a problem the team has actually hit. Adopt a pattern early because elite teams have it
and you drown in boilerplate you have no use for.

## The five phases

| Phase / Season | Engineering leap | Motivating pain | Team-process leap |
|---|---|---|---|
| **1** | Command-based + closed loop; vendored swerve | "It barely drives" | git; one software lead |
| **2** | IO layer + simulation + lightweight logging | "Can't test — no robot time" | PR review; onboarding doc; pairing |
| **3** | Wanted/current FSM + superstructure; unit tests; replay | "Mechanisms fight; can't debug" | subsystem ownership; rookie curriculum |
| **4** | Choreo + repulsor planning; extract team library; 2nd language | "Need speed; rewriting the same code yearly" | students run review; written standards |
| **5+** | State graph / behavior tree; (capstone) message passing | "Transition logic outgrew the FSM" | process is self-sustaining |

**Phase 1 — a robot that reliably works.** Not good code — a robot that drives, runs a mechanism or
two, and completes a simple autonomous in clean command-based WPILib. The core lesson is the
open-loop-to-closed-loop leap: *drive until the sensor says stop, not until the timer says stop.* Use
a vendored swerve library so the team gets a modern drivetrain without building the abstraction they
haven't earned yet.

**Phase 2 — write code without the robot.** This is the phase that quietly creates an elite team. The
universal pain: one robot, ten programmers, and it's on the cart getting its swerve rebuilt. The leap
is the IO layer — dependency inversion, a real CS concept — so the whole subsystem runs on a laptop.
Add lightweight logging (DogLog/Epilogue), not full replay; that's ceremony they haven't earned. The
process leap matters more: nobody merges their own code.

**Phase 3 — intent vs execution, and proof.** Mechanisms now fight, and "what is the robot doing"
gets hard. Two leaps: a wanted/current state machine with a superstructure (teach the centralized
version first — it's more readable), and unit tests, the payoff the IO layer was always promising.
This is the first year the team's knowledge clearly outlives any one student.

**Phase 4 — become a codebase, not a project.** Optimize and consolidate: separate the three path
concerns (PathPlanner, Choreo, repulsor planning), and extract a team library carried season to
season — the structural signature of a *program* rather than a team. *If the team can survive its best
programmer graduating, you have made it.*

**Phase 5 — the frontier, only if it earns its keep.** The honest note: a clean Phase 4 codebase is
already elite. Most powerhouse teams are a polished FSM-plus-superstructure-plus-replay, not something
exotic. Reach for a state graph or behavior tree only when the decision logic genuinely outgrows a
switch statement.

## The risk to manage

The temptation is to skip ahead — adopt AdvantageKit's IO layer in Phase 1 because elite teams have
it, and drown in boilerplate with no felt need behind it. Every rung must be motivated by a pain the
team has actually hit. The three habits — simulate, review, retain — are what carry a team across the
graduation cliff that kills most programs around year 3. Whether any of this actually correlates with
winning is the question [the next chapter](04-what-it-predicts.md) tests.
