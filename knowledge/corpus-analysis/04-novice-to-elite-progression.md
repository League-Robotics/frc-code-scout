# From Novice to Elite: A Multi-Season FRC Software Progression

*A staged plan for taking a team from basic WPILib to elite-level robot software over four to five seasons — sequencing the architectural techniques from the FRC code catalog (Parts I–III) against the team-organization and training changes that make them stick.*

---

## The principle that governs everything

What separates the elite teams in the corpus from everyone else is **not** that they know the fanciest pattern. It is three habits that make every pattern learnable:

1. **They simulate** — so they can write and verify code without the robot.
2. **They review each other's code** — so quality survives a bad night and a graduating senior.
3. **They retain knowledge across classes** — so year 4 is not year 1 again with new students.

The architecture is the *vehicle* for teaching those habits, not the goal. Teach AdvantageKit's IO layer to a team that doesn't review code and you get cargo-cult ceremony. So every phase below pairs an **engineering leap** with a **team-process leap** — and the process is the one that actually compounds.

A second rule governs the whole arc:

> **You rewrite in the offseason, never during build season.**

Each architectural leap is a radical change to the codebase. The only safe time to make it is May–December, practicing on *last year's* game where you already know what "working" looks like. During the six-week build, you ship what you already understand. A team that tries to learn the IO layer in February loses the regional.

A third rule:

> **Sequence by pain, not by prestige.**

Each rung must be motivated by a problem the team has actually hit. Adopt a pattern early because elite teams have it, and you drown in boilerplate you have no use for. The IO layer only makes sense once "we can't get robot time" is a felt pain; the state machine only makes sense once mechanisms start fighting each other.

---

## Phase 1 — Foundation (Season 1): a robot that reliably works

**Goal:** not good code — a robot that drives, runs one or two mechanisms, and completes a simple autonomous, written in clean command-based WPILib. Resist every urge to be clever.

**Teach:**

- Subsystems and commands as the two nouns of WPILib; one subsystem per mechanism.
- A single `Constants` file so no magic numbers hide inside logic.
- Closed-loop basics: an encoder and a WPILib `PIDController`. The core lesson is **"drive until the sensor says stop, not until the timer says stop"** — the open-loop-to-closed-loop leap. It is the single highest-value concept and the same one the Botball/FLL/WRO corpus converged on independently.
- Use a **vendored swerve library** (YAGSL or the CTRE swerve generator) so the team gets a modern drivetrain without building the abstraction themselves. They earn the right to understand it later. Regional teams like 4915 and 2877 do exactly this.

**Team move:** introduce **git and a single shared repo from day one**, even if commits are messy — the habit matters more than the hygiene. One mentor or veteran student is "software lead" and does all merging.

**Exit criterion:** the robot completes a 15-second autonomous with no human contact, and the code is on GitHub.

---

## Phase 2 — Simulation and structure (Offseason 1 → Season 2): write code without the robot

This is the phase that quietly creates an elite team. The motivating pain is universal: **there is one robot and ten programmers, and it's on the cart getting its swerve rebuilt.**

**The leap — the IO layer.** Split each subsystem into an interface (`ElevatorIO`) with a real implementation and a simulation implementation. Now the whole subsystem runs on a laptop. This is the AdvantageKit pattern, but you do **not** have to adopt all of AdvantageKit to teach it — the idea is *dependency inversion*, a genuine CS concept they will use forever.

- Study: **5712 (Hemlock)**, whose entire purpose is a forkable IO-layer swerve template; **9015** as a clean regional example.
- Add **lightweight logging** here — DogLog or WPILib Epilogue, one-line telemetry. **Not** full AdvantageKit replay yet; that is ceremony they have not earned. See **3847** and **581** for DogLog in use.

**Team move:**

- Turn on **pull-request review.** Nobody merges their own code; the software lead reviews every PR.
- Write a one-page **onboarding doc**: how to clone, build, deploy, and run the sim.
- Begin **pair-programming** rookies with veterans.

**The rewrite this offseason:** re-architect last year's robot behind IO interfaces.

**Exit criterion:** a new student can pull the repo and run the robot in simulation on their own laptop in under fifteen minutes, and every line that ships went through a second pair of eyes.

---

## Phase 3 — Coordination and verification (Season 3): intent vs. execution, and proof

The robot now has enough mechanisms that they fight each other, and "what is the robot doing right now" becomes genuinely hard. That pain motivates two leaps.

**Leap 1 — the wanted/current state machine plus a superstructure.** Each mechanism holds a *requested* state and an *actual* state; a single superstructure object coordinates them. Callers request a goal; they do not poke motors. This is the cleanest decoupling in the whole catalog.

- Teach the **centralized** version first — 581's single `RobotManager` is the most readable — before the **distributed** per-subsystem version (2910). One state machine is easier to reason about than fifteen.

**Leap 2 — unit tests.** This is the payoff the IO layer was always promising: because a subsystem runs in sim, you can drive it to completion on CI and assert on the result. Almost no FRC team does this; it is a defining elite marker.

- Study: **1155 (SciBorgs)** — runs real commands to completion in simulation and asserts on the outcome.
- Add the **null-object IO** (`NoElevator`) so the robot runs with a mechanism unplugged.
- Upgrade logging to **full AdvantageKit with replay** now — they finally have the discipline to debug a match from deterministic log replay rather than guessing.

**Team move:**

- **Subsystem ownership** — each student owns a subsystem's code and reviews changes to it.
- Build a real **preseason rookie curriculum.** You are now teaching Phases 1–2 to new members every September; that is a course, not an afterthought. This is the first year the team's knowledge clearly outlives any one student.

**Exit criterion:** CI runs unit tests on every PR, and the team has debugged at least one competition problem from replayed logs.

---

## Phase 4 — Optimization and the team library (Season 4): become a codebase, not a project

The mechanics are solid; now you optimize and consolidate.

**Separate the three path concerns explicitly:**

- **PathPlanner** — human-authored, waypoint-style paths.
- **Choreo** — machine-optimized, time-optimal trajectories for when tenths of a second decide matches.
- **Repulsor / potential-field planning** — driving to a pose while dodging obstacles on the fly. **3476** is the densest example; **4481** close behind.

A beginner conflates all three; the corpus pulls them apart, and so should the team.

**The deeper move — extract a team library.** Pull the generic subsystem bases, the IO scaffolding, and the controllers into reusable code the team carries season to season. This is what **254** and **1678** have, and it is the structural signature of a *program* rather than a team.

**Optional — a second language.** Introduce Kotlin on a side project. Seeing the same IO layer in Java and Kotlin (**3636**, **4099**) makes vivid which lines are *design* and which are just Java ceremony — a real software-engineering lesson with a robot as the motivation.

**Team move:**

- **Students run code review, not mentors.**
- Written coding standards live in the repo.
- Rookies are taught by second-years. *If the team can survive its best programmer graduating, you have made it.*

**Exit criterion:** a documented team library reused from one season to the next, and a review/onboarding process that runs without mentor intervention.

---

## Phase 5 — The frontier (Season 5+, only if it earns its keep)

The most sophisticated versions live here, but the honest note is that **a clean Phase 4 codebase is already elite.** Most powerhouse teams are a polished version of wanted/current-FSM + superstructure + replay, not something more exotic. Reach further only when the decision logic genuinely outgrows a switch statement.

- **State graph** — search over legal states (**6328**'s JGraphT approach).
- **Behavior tree** — a leaf/decorator/blackboard runtime with a visual editor (**3015**). The game-AI answer to deeply nested, reactive decision logic.

Both are the "transitions got too complex for an FSM" tool; pick by taste.

- **Capstone — multi-process message passing** (**971**'s C++/Rust with a FlatBuffers contract). For teams that want process isolation and a custom autonomy stack. A deliberate, rare choice — not a natural endpoint.

---

## The ladder in one view

| Phase / Season | Engineering leap | Motivating pain | Study | Team-process leap |
|---|---|---|---|---|
| **1** | Command-based + closed loop; vendored swerve | "It barely drives" | kit / YAGSL | git; one software lead |
| **2** | IO layer + simulation + lightweight logging | "Can't test — no robot time" | 5712, 9015, 3847 | PR review; onboarding doc; pairing |
| **3** | Wanted/current FSM + superstructure; unit tests; replay | "Mechanisms fight; can't debug" | 581, 2910, 1155 | subsystem ownership; rookie curriculum |
| **4** | Choreo + repulsor planning; extract team library; 2nd language | "Need speed; rewriting the same code yearly" | 3476, 4481, 254, 3636 | students run review; written standards |
| **5+** | State graph / behavior tree; (capstone) message passing | "Transition logic outgrew the FSM" | 6328, 3015, 971 | process is self-sustaining |

---

## The risk to manage

The temptation to skip ahead. A team that adopts AdvantageKit's IO layer in Phase 1 because elite teams have it will drown in boilerplate it has no use for — the pattern only makes sense once simulation is the felt need. Likewise, a behavior tree adopted before the team has hit the limits of a state machine is complexity for its own sake.

Every rung must be motivated by a pain the team has actually hit. Sequence by pain, not by prestige — and remember that the three habits (simulate, review, retain) are what carry a team across the graduation cliff that kills most programs around year 3.
