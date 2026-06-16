---
name: setup-logging
description: Wire a structured logging facade into a WPILib robot — AdvantageKit (with deterministic match replay) or the lightweight DogLog/Epilogue — built on the IO inputs-struct so the choice stays swappable. Use to add telemetry/logging, enable log replay, or replace println/SmartDashboard debugging ("set up logging", "add AdvantageKit", "enable replay", "log every subsystem").
---

# Set up logging

Answer "when the robot misbehaves on the field, how do we know why?" with a recorded log, not
`println`. The spectrum, trade-offs, and exact APIs are in **`knowledge/build-spec/logging.md`**
(bundled). The key idea: log the **`XxxIOInputs` struct** at the IO seam — both stacks consume it, so
the decision is deferrable and reversible.

## Choose the stack (logging.md §6)
- **DogLog / Epilogue** — low ceremony, telemetry now, **no replay**. Good default to start.
- **AdvantageKit** — `@AutoLog` inputs + `Logger.processInputs`, full-match WPILOG, **deterministic
  replay**. Higher setup cost (run-mode plumbing + IO discipline). Choose when you'll debug matches
  off-robot.

## AdvantageKit wiring
1. Add the AdvantageKit vendordep; make `Robot extends LoggedRobot`.
2. In `robotInit`, branch data receivers by run mode and start the logger:
   - `REAL` → `WPILOGWriter()` (USB) + `NT4Publisher()`
   - `SIM` → `NT4Publisher()`
   - `REPLAY` → `setUseTiming(false)`, `setReplaySource(new WPILOGReader(findReplayLog()))`,
     `WPILOGWriter(addPathSuffix(log,"_sim"))`
   - then `Logger.start();`  (see `simulation.md` §2.2 for the run-mode switch)
3. Annotate each `XxxIOInputs` with `@AutoLog`; in the subsystem's `periodic()` call
   `io.updateInputs(inputs); Logger.processInputs("Xxx", inputs);`. Log computed outputs with
   `@AutoLogOutput`.
4. **Coverage, not presence** — apply it across *all* subsystems, not one out of ten (rubric D5).

## DogLog / Epilogue wiring
- DogLog: one line where you have a value — `DogLog.log("Xxx/Height", height);`. No IO interface needed.
- Epilogue: mark a subsystem `@Logged` (and noisy fields `@NotLogged`); fields are logged each loop.

## Always
- Add **AdvantageScope** and commit its layout `.json` to the repo so the team opens the same views.
- Remove `System.out.println` debugging and any logic that depends on a `SmartDashboard` value.

## Verify
- Every mechanism's inputs are visible in AdvantageScope (live in SIM, on a USB log on the robot).
- (AdvantageKit) replay a SIM log through `REPLAY` mode and confirm the code re-runs deterministically.
