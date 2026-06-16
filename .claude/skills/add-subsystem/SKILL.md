---
name: add-subsystem
description: Add one mechanism subsystem to a WPILib robot project as a full IO quartet (XxxIO + Inputs, XxxIO<device>, XxxIOSim, the subsystem, Constants) plus a sim-backed unit test, following the matching control-archetype build guide. Use to add an elevator, arm, pivot, wrist, shooter, flywheel, intake, indexer, claw, vision, etc. ("add an elevator subsystem", "create an arm with an IO layer", "stamp out a shooter").
---

# Add a subsystem (the IO quartet)

Generate one mechanism as a clean IO seam so it can be **simulated, unit-tested, and lifted out as a
library** — and so a tool/motor swap is one file. Templates live in `templates/` beside this skill;
the canonical patterns and real exemplars live in `knowledge/build-spec/subsystems/` (bundled).

## Collect first
- **Mechanism name** (e.g. `Elevator`, `Arm`, `Shooter`, `Intake`, `Vision`).
- **Archetype** — pick by motion (this picks the sim model, the contract, and the doc):

  | Archetype | Mechanisms | Sim model | Read |
  |---|---|---|---|
  | linear position | elevator, climber | `ElevatorSim` | `subsystems/01-linear-position.md` |
  | rotational position | arm, pivot, wrist, turret | `SingleJointedArmSim` | `subsystems/02-rotational-position.md` |
  | velocity | shooter, flywheel | `FlywheelSim` | `subsystems/03-velocity.md` |
  | roller + sensor | intake, indexer, feeder, claw | `DCMotorSim` + beam-break | `subsystems/04-roller-gamepiece.md` |
  | sensor-only | vision | (no actuation) | `subsystems/05-vision-sensor.md` |

- **Vendor** for the real impl (CTRE Phoenix 6 / REVLib), motor count, gearing/mass/MOI (for the sim).

## Steps
1. **Read the archetype doc** — its §3 (the contract), §4 (the real quartet), §6.1 (the test). Match
   its naming and the loop-above vs loop-below choice (default **loop above** for things you
   simulate: interface is `setVoltage` + getters, the subsystem owns the PID+feedforward).
2. **Copy the templates** from `templates/` and rename `Example`→`<Name>`, `example`→`<name>` into the
   project's `subsystems/<name>/` package:
   - `<Name>IO.java` — interface + `<Name>IOInputs`. **No vendor imports.**
   - `<Name>IO<Device>.java` — e.g. `<Name>IOTalonFX` — the ONLY file importing `com.ctre`/`com.revrobotics`.
   - `<Name>IOSim.java` — wrap the archetype's WPILib sim model with the real constants.
   - `<Name>.java` — the subsystem: holds one `<Name>IO`, runs the controller, `create()` selection point.
   - `<Name>Constants.java` — gains, gearing, limits, ports.
   - `<Name>Test.java` — `new <Name>(new <Name>IOSim())`, command a setpoint, assert it's reached.
3. **Adapt to the archetype** (the only real differences):
   - feedforward: `ElevatorFeedforward` (linear) · `ArmFeedforward(angle)` (rotational, gravity tracks
     cos θ) · `SimpleMotorFeedforward` (velocity, no gravity).
   - rotational reads an **absolute encoder**; velocity controls **speed** with an "at speed" tolerance;
     roller exposes a **fakeable game-piece sensor** as an inputs field; vision has **no `setVoltage`**
     and feeds `RobotState.addVisionObservation` (read `05-vision-sensor.md` — its template differs).
4. **Wire it in** — construct it in `RobotContainer` via `<Name>.create()`; if a coordinator exists,
   expose a `setGoal`/`setState` the `Superstructure` can call (never command its motor from above).
5. **Verify** — `./gradlew test` runs the new test in sim; grep the package for `com.ctre`/
   `com.revrobotics` and confirm they appear **only** in `<Name>IO<Device>.java`.

## Checklist (from the archetype doc §7)
- [ ] `<Name>IO` has the contract for its archetype and **no vendor type**.
- [ ] `<Name>IOSim` wraps the right WPILib sim with measured constants (so the test is meaningful).
- [ ] `<Name>IO<Device>` is the only file importing the vendor SDK.
- [ ] The subsystem holds one `<Name>IO`, picked at one `create()` point.
- [ ] A test builds the subsystem on the Sim impl, commands a setpoint, asserts it's reached.
- [ ] The package imports no sibling subsystem (it would compile as its own module).
