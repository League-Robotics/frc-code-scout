# Simulating FRC Robot Code

> A companion to [`elite-architecture.md`](elite-architecture.md) and the
> [subsystem series](subsystems/00-anatomy-of-a-subsystem.md). Simulation is the **first dividend of
> the IO seam** (rubric D3): because the hardware sits behind `XxxIO`, you swap an `XxxIOSim` and the
> whole robot runs on a laptop. It is also the substrate every test runs on ([`testing.md`](testing.md)).
>
> *Code is quoted to study the technique, not to copy.*

---

## 1. What it is, and why it's worth the trouble

Simulation runs your *actual* robot code with the physical robot replaced by a model. The payoff
scales with the model's fidelity: a stub that echoes setpoints proves the code doesn't crash; a real
physics model can **surprise you** — reveal that a mechanism overshoots, an auto path clips a wall, or
a controller is unstable — before the robot exists. That gap, "the code runs without a robot" vs. "the
simulation could catch a real bug," is the D3 ladder (level 1 → level 3). The whole thing is possible
only because of the IO seam: the subsystem holds an `XxxIO`, and sim is just a different implementation
of it.

## 2. How it works — three mechanisms

### 2.1 The WPILib HAL is simulatable
At the bottom sits the **WPILib HAL** (`edu.wpi.first.hal`) — the layer between WPILib and the roboRIO.
On a desktop it's replaced by a *simulated* HAL, so `DriverStation`, `Timer`, encoders, and digital IO
all work with no FPGA. This is what makes a robot program *runnable* off-robot at all. It does **not**
simulate vendor devices (a `TalonFX` on CAN) — that's what §3 is for.

### 2.2 The run mode selects the implementations
Exactly one place chooses Real vs. Sim, keyed off the run mode. At the subsystem level it's the
`create()` factory (`Robot.isReal() ? new RealElevator() : new SimElevator()`, see
[`01-linear-position`](subsystems/01-linear-position.md) §4.4). At the robot level, AdvantageKit teams
branch the logging/replay plumbing the same way:

*2910 Jack in the Bot — `2025CompetitionRobot-Public/.../Robot.java`*
```java
public class Robot extends LoggedRobot {
  @Override public void robotInit() {
    switch (Constants.currentMode) {
      case REAL   -> { Logger.addDataReceiver(new WPILOGWriter());      // log to USB
                       Logger.addDataReceiver(new NT4Publisher()); }
      case SIM    -> Logger.addDataReceiver(new NT4Publisher());        // log to NetworkTables
      case REPLAY -> { setUseTiming(false);                              // run as fast as possible
                       String log = LogFileUtil.findReplayLog();
                       Logger.setReplaySource(new WPILOGReader(log));    // feed a recorded match
                       Logger.addDataReceiver(new WPILOGWriter(addSuffix(log, "_sim"))); }
    }
    Logger.start();
  }
}
```
`Constants.currentMode` is `REAL` on the robot, `SIM` on a desktop (detected via `RobotBase.isReal()`),
and `REPLAY` when re-running a log (§5).

### 2.3 Sim time is controlled
In a unit test you step time yourself (`SimHooks.stepTiming(0.02)` — see [`testing.md`](testing.md)
§4), so a "4-second" test runs instantly and deterministically. In the interactive sim GUI, time runs
real-time and you drive with a keyboard/controller. Either way, the IO `Sim` impl advances its physics
model by that dt each cycle (`sim.update(dt)`).

## 3. The environments — what backs an `XxxIOSim`

| Environment | What it models | Use it for | Seen in |
|---|---|---|---|
| **WPILib physics sims** (`ElevatorSim`, `SingleJointedArmSim`, `FlywheelSim`, `DCMotorSim`) | one mechanism: motor + gearbox + load + gravity | every subsystem's `Sim` impl — the default | every subsystem doc |
| **Phoenix 6 `TalonFXSimState`** | the *motor controller* simulating itself (feed battery V, get sensor readings) | high-fidelity sim of CTRE closed-loop control | 3476 `IntakeIOSim` |
| **maple-sim** (`org.ironmaple`) | **whole-drivetrain rigid-body physics** — wheel slip, momentum, game-piece collisions on a `SimulatedArena` | sim that surprises you (drivetrain dynamics, intaking) | 3647, 1114 |
| **AdvantageScope** | viewer: 3D field, mechanism poses, log scrubbing | *seeing* any of the above; commit layouts to the repo | logging teams |
| **WPILib Sim GUI** | joysticks, device outputs, field widget | manual driving, quick checks | all |

The WPILib per-mechanism sims are the building blocks (a `SimElevator` wraps an `ElevatorSim`). The
controller-self-sim (`TalonFXSimState`) and **maple-sim** are the high-fidelity steps:

*3647 Millennium Falcons — `2025-Reefscape.../Util/sim/MapleSimSwerveDrivetrain.java`*
```java
import org.ironmaple.simulation.SimulatedArena;
import org.ironmaple.simulation.drivesims.SwerveDriveSimulation;
// ...
public final SwerveDriveSimulation mapleSimDrive = new SwerveDriveSimulation(simulationConfig, new Pose2d());
SimulatedArena.overrideSimulationTimings(simPeriod, 1);
```
maple-sim simulates the *robot in the field* — the drivetrain's real dynamics and game-piece
interactions — rather than four independent motor models. It's the rung past hand-written `SimIO`
([`06-swerve-drivetrain`](subsystems/06-swerve-drivetrain.md) §5).

## 4. How you use it

- **Develop before the robot exists.** Drive an auto in sim in January, weeks before the bot is
  built — the IO seam means the code you write now runs unchanged on hardware later.
- **Treat sim as a separate robot.** The corpus mindset (quoted in
  [`03-velocity`](subsystems/03-velocity.md) §4.4): *"the physics simulator is treated as a separate
  robot with different tuning."* Real and Sim are two implementations behind one contract, each with
  its own gains; the *code path* is identical, which is what makes sim trustworthy.
- **Climb the fidelity ladder deliberately** (this is the D3 progression):

  | D3 | Fidelity | What you get |
  |---|---|---|
  | 1 | `simulationPeriodic` stub echoing setpoints | "it runs without a robot" |
  | 2 | WPILib mechanism sims in the `IOSim` | the controller actually has to converge |
  | 3 | whole-robot dynamics (maple-sim) + vision sim | the sim can surprise you |
  | 4 | deterministic **replay** of a real match (§5) | re-run the actual robot on actual data |

## 5. Log replay — the top of the ladder

The `REPLAY` mode in §2.2 is simulation's killer application: feed a **recorded match log** back
through your *unchanged* code and watch what it decided, frame by frame — add new logged fields to
inspect decisions that weren't logged live. The prerequisites are exactly the IO seam plus discipline:
every hardware reading must cross the IO line into an inputs struct that gets logged (so it can be
replayed), and the program must be **single-threaded and deterministic** (no un-isolated randomness, no
threads) so the re-run matches. This is an AdvantageKit feature — see [`logging.md`](logging.md). The
corpus finding is blunt: building the IO seam is common, but **one** team in the survey actually ships a
replay variant. It is the rarest, highest-value dividend, and the foundation already paid for it.

## 6. Checklist — is your simulation real?

- [ ] A run-mode selection (`Robot.isReal()` / `Constants.currentMode`) picks `XxxIOSim` at one place.
- [ ] Each subsystem's `XxxIOSim` wraps a real WPILib physics model with **measured** constants (mass,
      MOI, gearing) — not a setpoint echo.
- [ ] Sim time is stepped (`SimHooks` in tests; real-time in the GUI), and the model advances by dt.
- [ ] AdvantageScope layouts are committed so anyone can *see* the sim/telemetry.
- [ ] (Stretch) maple-sim for whole-drivetrain physics; (capstone) `REPLAY` mode wired and used.
- [ ] The same code path runs in REAL and SIM — only constants/implementations differ.
