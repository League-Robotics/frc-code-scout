---
title: Appendix D — Reviewing for the seams
weight: 4
---

**A code review is the last gate that keeps the architecture honest.** Every other chapter in this book describes how to *build* the three seams — [the IO seam](../part-1/03-the-io-seam.md), the state seam, and [the coordination seam](../part-1/05-the-coordination-seam.md). This appendix is the canonical, enforceable guide for *protecting* them one pull request at a time. It is written for both human reviewers and review agents, and it prioritizes the violations that quietly erode testability, simulation fidelity, replay/debuggability, and long-term maintainability — the exact dividends the seams were built to earn.

The core rule that governs everything below is the same rule that governs scoring:

> **Review what is *used*, not what is *present*.**

A file or class name is not evidence. A vendordep in the build file is not adoption. A `Superstructure` class is not a coordination seam unless it actually coordinates transitions with guards. Open the cited files, read the call graph, and confirm the seam does the work its name claims.

---

## The review contract

A review protects five invariants. A change passes only if the code still preserves all of them. See [hardware abstraction and the IO line](../part-2/16-hardware-abstraction.md) and [cross-cutting practices](../part-1/07-cross-cutting-practices.md) for the full definitions.

1. **The IO seam is intact.** Subsystem logic is separated from hardware through `XxxIO` plus `XxxIOInputs`.
2. **The state seam is intact.** One `RobotState` owns fused world state; all other code *reads* state from it.
3. **The coordination seam is intact.** One `Superstructure` (or equivalent) owns cross-subsystem goal transitions and guards.
4. **Vendor confinement is intact.** Vendor SDK types stay *below* the IO line — only inside `XxxIO<device>` and `XxxIOSim`.
5. **Deferred dividends stay possible.** Nothing blocks the later payoffs: D3 simulation, D4 tests, D5 logging/replay, D6/D7 growth.

Any change that weakens a seam to make short-term coding easier is **architectural debt, not simplification** — and should be named as such in the review.

---

## Severity levels

Use one consistent severity vocabulary across every review so findings are comparable from PR to PR.

| Level | Name | Meaning |
| --- | --- | --- |
| **S0** | Blocker | Breaks an architectural invariant, or makes safe operation unverifiable. |
| **S1** | High | Preserves runtime behavior today, but creates a near-term test / sim / replay dead end. |
| **S2** | Medium | Local design smell that increases coupling or hides intent. |
| **S3** | Low | Readability or consistency issue with low structural risk. |

**Default to S0/S1 whenever a change crosses seams incorrectly.** A seam violation that "works on the robot" is still a blocker.

---

## The ten principles

Each principle lists what to **enforce**, the **red flags** that signal a violation, and the **evidence of correctness** that clears it.

### P1 — Enforce strict seam boundaries

**Enforce**
- Subsystems depend on the `XxxIO` contract, not concrete hardware classes.
- `RobotState` and `Superstructure` are hardware-agnostic logic layers.

**Red flags**
- A subsystem imports `com.ctre`, `com.revrobotics`, or `org.photonvision` directly.
- `RobotState` imports hardware, camera, or subsystem *implementation* classes.
- The `Superstructure` sets motor outputs directly.

**Evidence of correctness**
- Vendor imports exist only in `XxxIO<device>` and `XxxIOSim`.
- The subsystem constructor accepts an interface (`XxxIO`), not a vendor object.

### P2 — Reject leaky interfaces

**Enforce**
- IO interfaces expose robot-domain intent and measured state, not vendor mechanics.
- Interfaces are sufficient for *both* REAL and SIM implementations.

**Red flags**
- An interface exposes vendor-specific handles or configuration objects.
- Interface methods mirror the vendor API surface with no subsystem intent.
- A missing `updateInputs(inputs)` call, or an incomplete inputs struct that hides critical state.

**Evidence of correctness**
- The interface can be implemented by both a hardware class and a physics-sim class.
- The inputs struct includes every value needed for control, logging, and diagnostics.

### P3 — Protect abstraction direction

**Enforce**
- High-level policy depends on abstractions; low-level details depend on hardware.
- Control decisions flow in one direction: **goal → coordinator → subsystem → IO → device.**

**Red flags**
- Commands bypass subsystem APIs and write hardware directly.
- Subsystems call into coordinator decisions (a reverse dependency).
- "Utility" helpers become hidden cross-layer service locators.

**Evidence of correctness**
- The call graph follows one direction, from intent to actuation.
- Cross-subsystem logic is centralized in the `Superstructure`, not scattered across mechanisms.

### P4 — Keep coordination centralized and guarded

**Enforce**
- One transition function owns cross-subsystem sequencing and interlocks.
- The goal-request API separates *intent* from *execution*.

**Red flags**
- The `Superstructure` exists only as a container with jog methods.
- Interlock logic is duplicated across multiple commands or subsystems.
- Goals are represented as ad-hoc booleans spread through the code.

**Evidence of correctness**
- The coordinator exposes `requestGoal(...)` or an equivalent command API.
- Guarded transitions are explicit and testable.

### P5 — Preserve testability as a first-class requirement

**Enforce**
- New subsystem behavior remains testable with `XxxIOSim`.
- Important safety transitions have at least one command-level test path.

**Red flags**
- New logic requires real hardware to execute at all.
- Static singletons or hidden globals prevent constructing isolated units.
- There is no deterministic time-stepping path for tests.

**Evidence of correctness**
- The subsystem can be constructed with sim IO in a unit test.
- Tests assert *behavior*, not merely the absence of exceptions.

### P6 — Preserve the simulation-fidelity path

**Enforce**
- Code supports SIM mode without alternate logic branches that change behavior semantics.
- Physics-sim attachment points remain inside the `IOSim` implementations.

**Red flags**
- SIM mode bypasses normal subsystem logic with special shortcuts.
- Mechanism state is fabricated in the subsystem's `periodic()` instead of in IO sim.
- Time or sensor updates are tied to wall-clock assumptions.

**Evidence of correctness**
- The *same* subsystem code path runs in REAL and SIM; only the IO implementation differs.
- Sim classes own model update and sensor synthesis.

### P7 — Preserve the logging and replay contract

**Enforce**
- Inputs are logged at the seam, immediately after `updateInputs`.
- Logged data is enough to reconstruct decisions offline.

**Red flags**
- Only setpoints are logged, not measured inputs.
- Logging is sparse — present in only a subset of subsystems.
- Replay mode would require subsystem rewrites.

**Evidence of correctness**
- Structured per-subsystem inputs logging is present consistently.
- Coordinator and state outputs are also logged where they are needed for diagnosis.

### P8 — Optimize for future change, not current convenience

**Enforce**
- Changes reduce or hold coupling; they do not add hidden integration points.
- New mechanism code follows the quartet pattern: `XxxIO`, `XxxIO<device>`, `XxxIOSim`, subsystem.

**Red flags**
- A quick fix adds a direct reference to a sibling subsystem.
- A new mechanism skips the IO seam "for now."
- Copy-paste patterns repeat where a shared abstraction is due — by the third use.

**Evidence of correctness**
- The subsystem package could be lifted into a library with minimal changes.
- New code extends existing seam patterns rather than inventing side paths.

### P9 — Prefer explicit contracts over implicit behavior

**Enforce**
- Preconditions, safety guards, and control modes are explicit in the API and state.
- Tuning and config values are centralized and named by domain meaning.

**Red flags**
- Magic thresholds spread across commands.
- Hidden mode switching via mutable globals.
- "Do everything" methods whose behavior is controlled by call-order side effects.

**Evidence of correctness**
- APIs express intent (`setGoal`, `requestGoal`, `atGoal`) and measurable state.
- Constants and config are grouped by subsystem and purpose.

### P10 — Treat architecture regressions as functional regressions

**Enforce**
- Reviewers block seam violations *even when robot behavior appears unchanged.*

**Red flags**
- "Works on the robot" used as justification for bypassing abstractions.
- "Will refactor later" attached to vendor leaks and cross-layer coupling.

**Evidence of correctness**
- The PR discussion covers seam impact and test/sim impact — not only on-field behavior.

---

## Agent-facing review workflow (deterministic pass)

Run this exact sequence for **each subsystem touched by the PR.**

1. **Map touched seams.** Identify whether the PR changes the IO seam, state seam, coordination seam, or several at once.
2. **Check vendor confinement.** Search the changed files for vendor imports appearing above IO implementations.
3. **Check interface shape.** Confirm the IO contract still supports REAL + SIM with no vendor leakage.
4. **Check dependency direction.** Verify no new *upward* dependency from a subsystem to coordinator/state policy.
5. **Check the test path.** Confirm the code can still be instantiated in sim-backed tests.
6. **Check the sim path.** Confirm there is no SIM-only behavior fork that bypasses subsystem logic.
7. **Check the logging path.** Confirm inputs and key decisions remain observable.
8. **Classify findings.** Assign each an S0–S3 severity and explain the seam impact.

> If any of steps 2–7 fails, mark it as an **architectural finding even if the runtime behavior is currently correct.**

---

## Human-facing quick checklist

Use these six questions in a live review conversation.

- Can I swap a motor vendor in this subsystem **without touching subsystem logic**?
- Can I run this changed behavior in **SIM without robot hardware**?
- Can I write a **deterministic test** for this behavior with the existing seams?
- Can I understand **why a failure happened from logs alone**?
- Is there **one obvious place** where cross-subsystem safety rules live?
- Did this PR **reduce** coupling, or just **hide** it?

If any answer is "no," investigate before approval.

---

## Non-negotiable anti-patterns (auto-fail)

These fail the review automatically unless they are justified *and* remediated:

1. Vendor types imported above IO implementations.
2. Commands or coordinators writing actuator outputs directly.
3. A "Superstructure" with no real transition/guard model.
4. Subsystem logic that cannot execute with `IOSim`.
5. New mechanism code that skips the IO seam by design.
6. A logging strategy that cannot reconstruct what the code saw.

Any temporary exception must ship with a **dated remediation plan in the PR.**

---

## Finding output format

Report every finding in this exact shape so agent and human reviews stay aligned and comparable across PRs.

- **Severity:** S0 / S1 / S2 / S3
- **Principle:** P#
- **Location:** file and symbol
- **What leaked or coupled:** one sentence
- **Why it matters:** one sentence, tied to test / sim / replay / safety / future change
- **Minimum fix:** the smallest structural correction that restores seam integrity
