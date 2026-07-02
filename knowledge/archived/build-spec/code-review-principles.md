# Code Review Principles for Elite Architecture

> Companion to `elite-architecture.md`, `testing.md`, `simulation.md`, and `logging.md`.
> Purpose: give reviewers (human and agent) a single, enforceable guide for finding structural problems early.

This guide is for architecture-first code review. It prioritizes violations that reduce testability, simulation fidelity, replay/debugability, and long-term maintainability.

The core rule is unchanged:

**Score and review what is used, not what is present.**

A file or class name is not evidence. A vendordep is not adoption. A `Superstructure` class is not a coordination seam unless it actually coordinates transitions.

---

## 1. Review contract (what this review is trying to protect)

A review passes only if the code preserves these invariants:

1. **IO seam is intact:** subsystem logic is separated from hardware through `XxxIO` plus `XxxIOInputs`.
2. **State seam is intact:** one `RobotState` owns fused world state; other code reads state from it.
3. **Coordination seam is intact:** one `Superstructure` (or equivalent) owns cross-subsystem goal transitions and guards.
4. **Vendor confinement is intact:** vendor SDK types stay below the IO line (`XxxIO<device>` / `XxxIOSim`).
5. **Deferred dividends stay possible:** nothing blocks D3 sim, D4 tests, D5 logging/replay, D6/D7 growth.

Any change that weakens one seam to make short-term coding easier should be treated as architectural debt, not simplification.

---

## 2. Severity levels for findings

Use consistent severity language in reviews.

- **S0 Blocker:** breaks an architectural invariant or makes safe operation unverifiable.
- **S1 High:** preserves runtime behavior today but creates a near-term test/sim/replay dead end.
- **S2 Medium:** local design smell that increases coupling or hides intent.
- **S3 Low:** readability or consistency issue with low structural risk.

Default to S0/S1 when a change crosses seams incorrectly.

---

## 3. Principles to enforce in every review

Each principle includes: what to enforce, red flags, and acceptable evidence.

### P1. Enforce strict seam boundaries

**Enforce**
- Subsystems depend on `XxxIO` contract, not concrete hardware classes.
- `RobotState` and `Superstructure` are hardware-agnostic logic layers.

**Red flags**
- Subsystem imports `com.ctre`, `com.revrobotics`, `org.photonvision` directly.
- `RobotState` imports hardware, camera, or subsystem implementation classes.
- Superstructure sets motor outputs directly.

**Evidence of correctness**
- Vendor imports exist only in `XxxIO<device>` and `XxxIOSim`.
- Subsystem constructor accepts an interface (`XxxIO`), not a vendor object.

### P2. Reject leaky interfaces

**Enforce**
- IO interfaces expose robot-domain intent and measured state, not vendor mechanics.
- Interfaces are sufficient for both REAL and SIM implementations.

**Red flags**
- Interface exposes vendor-specific handles or configuration objects.
- Interface methods mirror vendor API surface without subsystem intent.
- Missing `updateInputs(inputs)` or incomplete inputs struct that hides critical state.

**Evidence of correctness**
- Interface can be implemented by both a hardware class and physics sim class.
- Inputs struct includes the values needed for control, logging, and diagnostics.

### P3. Protect abstraction direction

**Enforce**
- High-level policy depends on abstractions; low-level details depend on hardware.
- Control decisions flow: goal -> coordinator -> subsystem -> IO -> device.

**Red flags**
- Commands bypass subsystem APIs and write hardware directly.
- Subsystems call into coordinator decisions (reverse dependency).
- Utility helpers become hidden cross-layer service locators.

**Evidence of correctness**
- Call graph follows one direction from intent to actuation.
- Cross-subsystem logic is centralized in Superstructure, not spread across mechanisms.

### P4. Keep coordination centralized and guarded

**Enforce**
- One transition function owns cross-subsystem sequencing and interlocks.
- Goal request API separates intent from execution.

**Red flags**
- "Superstructure" exists only as a container with jog methods.
- Interlock logic duplicated in multiple commands or subsystems.
- Goals are represented as ad-hoc booleans spread through code.

**Evidence of correctness**
- Coordinator exposes `requestGoal(...)` or equivalent command API.
- Guarded transitions are explicit and testable.

### P5. Preserve testability as a first-class requirement

**Enforce**
- New subsystem behavior remains testable with `XxxIOSim`.
- Important safety transitions have at least one command-level test path.

**Red flags**
- New logic requires real hardware to execute at all.
- Static singletons or hidden globals prevent constructing isolated units.
- No deterministic time stepping path for tests.

**Evidence of correctness**
- Subsystem can be constructed with sim IO in unit tests.
- Tests assert behavior, not only absence of exceptions.

### P6. Preserve simulation fidelity path

**Enforce**
- Code supports SIM mode without alternate logic branches that change behavior semantics.
- Physics sim attachment points remain inside IOSim implementations.

**Red flags**
- SIM mode bypasses normal subsystem logic with special shortcuts.
- Mechanism state is fabricated in subsystem periodic instead of IO sim.
- Time or sensor updates are tied to wall-clock assumptions.

**Evidence of correctness**
- Same subsystem code path runs in REAL and SIM; only IO implementation differs.
- Sim classes own model update and sensor synthesis.

### P7. Preserve logging and replay contract

**Enforce**
- Inputs are logged at the seam, immediately after `updateInputs`.
- Logged data is enough to reconstruct decisions offline.

**Red flags**
- Logging only setpoints, not measured inputs.
- Sparse logging in only a subset of subsystems.
- Replay mode would require subsystem rewrites.

**Evidence of correctness**
- Structured per-subsystem inputs logging is present consistently.
- Coordinator/state outputs are also logged where needed for diagnosis.

### P8. Optimize for future change, not current convenience

**Enforce**
- Changes reduce or hold coupling; they do not add hidden integration points.
- New mechanism code follows the quartet pattern (`XxxIO`, `XxxIO<device>`, `XxxIOSim`, subsystem).

**Red flags**
- Quick fixes add direct references to sibling subsystems.
- New mechanism skips IO seam "for now".
- Repeated copy-paste patterns that should become shared abstractions after the third use.

**Evidence of correctness**
- Subsystem package can be lifted as a library with minimal changes.
- New code extends existing seam patterns rather than inventing side paths.

### P9. Prefer explicit contracts over implicit behavior

**Enforce**
- Preconditions, safety guards, and control modes are explicit in API and state.
- Tuning/config values are centralized and named by domain meaning.

**Red flags**
- Magic thresholds spread across commands.
- Hidden mode switching via mutable globals.
- "Do everything" methods with behavior controlled by call order side effects.

**Evidence of correctness**
- APIs express intent (`setGoal`, `requestGoal`, `atGoal`) and measurable state.
- Constants/config are grouped by subsystem and purpose.

### P10. Treat architecture regressions as functional regressions

**Enforce**
- Reviewers should block seam violations even when robot behavior appears unchanged.

**Red flags**
- "Works on robot" used as justification for bypassing abstractions.
- "Will refactor later" for vendor leaks and cross-layer coupling.

**Evidence of correctness**
- PR discussion includes seam impact and test/sim impact, not only on-field behavior.

---

## 4. Agent-facing review workflow (deterministic pass)

Use this sequence for each subsystem touched by a PR.

1. **Map touched seams:** identify whether PR changes IO seam, state seam, coordination seam, or multiple.
2. **Check vendor confinement:** search changed files for vendor imports above IO implementations.
3. **Check interface shape:** confirm IO contract still supports REAL + SIM without vendor leakage.
4. **Check dependency direction:** verify no new upward dependency from subsystem to coordinator/state policy.
5. **Check test path:** confirm code can still be instantiated in sim-backed tests.
6. **Check sim path:** confirm no SIM-only behavior fork that bypasses subsystem logic.
7. **Check logging path:** confirm inputs and key decisions remain observable.
8. **Classify findings:** assign S0-S3 severity and explain seam impact.

If steps 2-7 fail, mark as architectural finding even if runtime behavior is currently correct.

---

## 5. Human-facing quick checklist

Use this in live review conversations.

- Can I swap a motor vendor in this subsystem without touching subsystem logic?
- Can I run this changed behavior in SIM without robot hardware?
- Can I write a deterministic test for this behavior with existing seams?
- Can I understand why a failure happened from logs alone?
- Is there one obvious place where cross-subsystem safety rules live?
- Did this PR reduce coupling, or just hide coupling?

If any answer is "no", investigate before approval.

---

## 6. Non-negotiable anti-patterns (auto-fail unless justified and remediated)

1. Vendor types imported above IO implementations.
2. Commands or coordinators writing actuator outputs directly.
3. "Superstructure" without a real transition/guard model.
4. Subsystem logic that cannot execute with IOSim.
5. New mechanism code skipping IO seam by design.
6. Logging strategy that cannot reconstruct what the code saw.

Any temporary exception must include a dated remediation plan in the PR.

---

## 7. Output format for review findings

For each finding, report in this shape:

- **Severity:** S0/S1/S2/S3
- **Principle:** P#
- **Location:** file and symbol
- **What leaked or coupled:** one sentence
- **Why it matters:** one sentence tied to test/sim/replay/safety/future change
- **Minimum fix:** smallest structural correction that restores seam integrity

This keeps agent and human reviews aligned and comparable across PRs.
