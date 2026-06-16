# Logging & Telemetry in FRC Robot Code

> A companion to [`elite-architecture.md`](elite-architecture.md) §4 and the
> [subsystem series](subsystems/00-anatomy-of-a-subsystem.md). Logging is settled **at the IO seam**:
> the `XxxIOInputs` struct you already built is the single artifact every logging stack consumes
> (rubric D5). That's why the AdvantageKit-vs-DogLog choice can be *deferred* — and why it's swappable.
>
> *Code is quoted to study the technique, not to copy.*

---

## 1. What it is, and the question it answers

"When the robot misbehaves on the field — between two qualifier matches, with no laptop attached —
**how do we know why?**" Logging is the answer: a structured, recorded stream of what the code saw and
what it decided. The bar isn't "print some numbers"; it's "reconstruct the failure afterward." That
reconstruction is impossible with `println` and trivial with a logged inputs struct — which is the
whole reason the IO seam captures every hardware reading in one place.

Adoption is the most lopsided in the corpus: **AdvantageKit in 26 teams**, Epilogue in 7, DogLog in 2,
URCL in 5. Logging is the one advanced practice that has gone near-universal among serious teams.

## 2. The spectrum (the D5 ladder)

| D5 | Stack | What it is | Cost |
|---|---|---|---|
| 0 | `System.out.println` | gone the instant the robot disconnects; no history | — |
| 1 | `SmartDashboard.put*` | live values, scattered through subsystems, **not recorded** | low |
| 2 | **DogLog / Epilogue** | structured lightweight logging to a WPILOG file + NT | low |
| 3 | **AdvantageKit** | `@AutoLog` inputs + `Logger.processInputs`, full-match logging | higher (IO discipline) |
| 4 | replay + diagnostics | log replay actually exercised; self-check `FaultReporter` | highest |

The jump that matters is L1 → L2: from *live-only* dashboard values to a **recorded** log you can open
after the match. Everything above L2 is about coverage and replay fidelity.

## 3. The key idea — log the inputs struct at the seam

The "fourth decision" of the architecture (`elite-architecture.md` §4) is made once, at the IO boundary:
each `XxxIO` fills an `XxxIOInputs` struct every cycle, and **that struct is what gets logged.** Because
the log is taken at the moment the code reads hardware, it's a faithful record of what the code saw —
the precondition for deterministic replay. Both logging stacks consume the same struct, which is what
keeps them swappable:

```java
@AutoLog                                    // the one artifact both stacks log
public static class FlywheelIOInputs {
  public double velocityRadPerSec = 0.0;
  public double appliedVolts = 0.0;
  public double[] currentAmps = new double[] {};
}
```
*5712 Hemlock — `2024-Eos/.../flywheel/FlywheelIO.java` (6328 AdvantageKit template)*

## 4. How-to, per stack

### 4.1 AdvantageKit (the replay stack)
`@AutoLog` generates an `XxxIOInputsAutoLogged`; the subsystem calls `Logger.processInputs` each cycle
(which logs *and*, in replay, overwrites the inputs from the log); computed values use `@AutoLogOutput`:

*5712 Hemlock — `2024-Eos/.../flywheel/Flywheel.java`*
```java
private final FlywheelIOInputsAutoLogged inputs = new FlywheelIOInputsAutoLogged();
@Override public void periodic() {
  io.updateInputs(inputs);
  Logger.processInputs("Flywheel", inputs);     // ◀ log the inputs (and replay them)
}
@AutoLogOutput public double getVelocityRPM() { /* a computed output, auto-logged */ }
```
The robot wires the backend once (`extends LoggedRobot`, data receivers per run mode, `Logger.start()`
— see [`simulation.md`](simulation.md) §2.2). On a real robot it writes a WPILOG to a USB stick; that
file is what you replay.

### 4.2 Epilogue (lightweight, annotation-driven)
WPILib's built-in annotation logger: mark a class `@Logged` and its fields are reflected to the log each
loop; `@NotLogged` excludes the noisy/expensive ones. No inputs-struct ceremony:

*1155 SciBorgs — `Reefscape-2025/.../elevator/Elevator.java`*
```java
@Logged
public class Elevator extends SubsystemBase {
  @Logged private final ProfiledPIDController pid = ...;
  @NotLogged private final ElevatorVisualizer setpoint = ...;   // skip this one
  @Logged public double position() { return hardware.position(); }
}
```

### 4.3 DogLog (the one-line imperative stack)
DogLog is the low-ceremony option: a static call logs a value to WPILOG + NT in one line, with no IO
interface required — `DogLog.log("Elevator/Height", height)`. It's used by 581 and 3847 (Spectrum) as a
deliberate counter-movement to AdvantageKit's plumbing: telemetry now, replay never.

## 5. AdvantageScope — the lens on all of it

Whatever stack writes the log, **AdvantageScope** reads it: line plots, a 3D field, mechanism
visualizations, and log scrubbing to step through a match. It's the viewer for live NT *and* recorded
WPILOG *and* replays. Commit its layout `.json` files to the repo so the whole team opens the same views
— a cheap habit that turns a log into an investigation tool.

## 6. The trade-off — this is a real engineering decision

| | AdvantageKit | DogLog / Epilogue |
|---|---|---|
| Logs the inputs struct | yes, via `@AutoLog` | yes (`@Logged` / `DogLog.log`) |
| **Deterministic replay** | **yes** — re-runs your code on the log | no |
| Setup cost | higher: run-mode plumbing, strict IO discipline | low |
| Best when | you'll debug matches off-robot; top-tier | you want telemetry fast, replay not yet worth it |

The recommendation from the build spec: build the **inputs-struct IO** now (you need it regardless),
start on **DogLog/Epilogue** for speed, and migrate to **AdvantageKit** when the team is ready to invest
in replay — because the seam is the struct, that migration touches the logging facade and `Robot.java`,
not the subsystems. The choice is genuinely "is replay fidelity worth the ceremony," not a default.

## 7. Checklist — is your logging real?

- [ ] No `println` debugging in committed code; no logic depending on `SmartDashboard` values.
- [ ] Every subsystem's hardware readings are captured in an `XxxIOInputs` struct (logged at the seam).
- [ ] One logging stack chosen deliberately (DogLog/Epilogue for speed, AdvantageKit for replay) —
      and applied across **all** subsystems, not one out of ten.
- [ ] Computed outputs (setpoints, state) are logged too (`@AutoLogOutput` / `@Logged` getter), not just inputs.
- [ ] AdvantageScope layouts committed to the repo.
- [ ] (L4) replay actually exercised on a real match log, and/or a fault/self-check reporter feeds the dashboard.
