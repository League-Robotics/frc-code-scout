---
name: setup-simulation
description: Wire physics simulation into a WPILib robot so the code runs on a laptop — a REAL/SIM/REPLAY run mode, the create() selection that swaps each subsystem's *IOSim, WPILib physics models (and optionally maple-sim), and AdvantageScope as the viewer. Use to enable running/driving the robot without hardware, or to develop before the robot is built ("set up simulation", "run the robot in sim", "add maple-sim").
---

# Set up simulation

Run the *actual* robot code with hardware replaced by a model. Because every subsystem holds an
`XxxIO`, sim is just a different implementation — swap `XxxIOSim` and the whole robot runs on a
laptop. Full detail (run modes, the HAL sim, sim time, environments, replay) is in
**`knowledge/build-spec/simulation.md`** (bundled).

## Steps
1. **Run-mode selection.** Ensure one place picks Real vs. Sim. At the subsystem level it's
   `create()` → `RobotBase.isReal() ? new XxxIO<device>() : new XxxIOSim()`. At the robot level (if
   using AdvantageKit) branch the data receivers by `Constants.Mode {REAL, SIM, REPLAY}` — see
   `simulation.md` §2.2 and `setup-logging`.
2. **Fill the `*IOSim` impls** with the matching WPILib physics model and **measured** constants:
   `ElevatorSim` / `SingleJointedArmSim` / `FlywheelSim` / `DCMotorSim` (per the subsystem's
   archetype). `add-subsystem` generates these; a setpoint-echoing stub is D3 level 1, real physics
   is level 2. Treat sim as a *separate robot with its own tuning* (same code path, different gains).
3. **Whole-robot fidelity (optional, D3 L3).** For the drivetrain, add **maple-sim**
   (`org.ironmaple` — `SimulatedArena` + `SwerveDriveSimulation`) so the sim models real dynamics and
   game-piece interactions instead of four independent motors.
4. **The viewer.** Use **AdvantageScope** (3D field, mechanism poses, log scrubbing) and the WPILib
   Sim GUI (joysticks, device outputs). Commit AdvantageScope layouts.
5. **Replay (capstone, D3 L4).** Once logging is AdvantageKit and the program is single-threaded and
   deterministic, `REPLAY` mode re-runs a recorded match through the unchanged code (see
   `setup-logging`).

## Verify
- `./gradlew simulateJava` (or the IDE "Simulate Robot") launches; the robot drives in the Sim GUI /
  AdvantageScope with no hardware.
- A subsystem commanded to a setpoint actually converges in sim (the controller has to work, not just
  echo) — the same proof a unit test gives (`setup-testing`).
