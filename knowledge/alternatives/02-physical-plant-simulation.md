# The Physical Plant — a True-State World Model for Testable Simulation

*Materialize the robot's **true** state as a first-class object — the dual of `RobotState`. `RobotState`
holds the **degraded estimate** the code reconstructs from sensors; the plant holds the **ground truth**
the sensors are a lossy view of. Breaking the plant out — and making its truth **settable** — is what lets
you test simulation in pieces, each in isolation.*

## The goal: break simulation into independently testable parts

The build spec puts simulation inside each `XxxIOSim` — a small plant tangled together with the device
bridge, one per subsystem. That works, but the physics, the sensor model, and the estimator end up welded
together and hard to exercise in isolation. This document develops the alternative: **pull the true
physical state out into one object — the plant — so that the dynamics, the sensors, and the estimator
become three separable models you can test apart**, at a fidelity you dial per test.

> **Naming caution.** `build-spec/subsystems/07-robotstate.md` calls `RobotState` "the world model." That is
> the *estimated* world — what the robot believes. Here, **"world model" / "plant" means the *true* world**
> — what is physically real. They are duals (§1). In this document "plant" / "true state" means ground
> truth; `RobotState` means the estimate.

> **Corpus reality check** (`data/code-index.duckdb`). The *estimate* half is mainstream: a `RobotState`
> class in 26 teams. The *truth* half is emerging exactly where physics force it: per-device WPILib plants
> (`ElevatorSim`, `FlywheelSim`, …) in 40 teams, the CTRE sim bridge (`getSimState`) in 27, **maple-sim**
> (a central true-state world: `SimulatedArena` + `SwerveDriveSimulation`) in 16, and **PhotonVision sim**
> (a sensor that observes the true pose with error) in 29. So most elite codebases already have *both*
> halves — a `RobotState` estimate and scattered plants — but **nobody names the duality or makes the plant
> a first-class, settable, independently-testable object.** That is the contribution here.

## 1. The duality: estimate vs. truth

Control theory's plant/observer split, stated for a robot:

```
        commands
           │
           ▼
   ┌───────────────┐     observe + noise/latency/dropout      ┌──────────────┐
   │  PLANT        │ ──────────────────────────────────────▶  │  RobotState  │
   │  (true state) │          (the sensors)                    │  (estimate)  │
   └───────────────┘                                           └──────────────┘
     ground truth:                                              degraded belief:
     true pose, true elevator height,                           fused pose, what the
     true game-piece positions, momentum                        code thinks is true
```

- **`RobotState`** owns the robot's *best estimate* — pose from the pose estimator, game-piece flags, a
  time-interpolated buffer. Fed by observations; read by control and decisions.
- **The plant** owns the *ground truth* — every mechanism's true position/velocity, the true chassis pose,
  true game-piece state, momentum. It is an **extended `RobotState`**: a superset, because it must carry
  everything physics integrates, including internal states `RobotState` never tracks.
- **The sensors are the lossy channel** between them: `RobotState ≈ estimate( noise( observe( plant ) ) )`.

The asymmetry that makes this worth building: **on the real robot the plant exists only physically — there
is no code object for it, you only ever have `RobotState`.** In simulation you *materialize* the plant, so
now you hold both truth and estimate at once and can measure the gap. **Estimation error becomes an
assertable quantity** — impossible to test on real hardware.

### Compare them with an adapter, not a shared interface

Don't force `RobotState` to wear the plant's interface or vice versa — `RobotState` earns its own shape
(covariance, interpolation buffer, game state) and the plant earns its own. The common ground is a thin
read view of *only the quantities you compare*, produced from either side by an **adapter**:

```java
interface WorldView {              // a handful of easy values: pose, heights, flags
    Pose2d  pose();
    double  elevatorHeight();
    boolean hasGamePiece();
}
WorldView truth    = PlantView.of(plant);          // adapt truth
WorldView estimate = RobotStateView.of(robotState); // adapt estimate
assertClose(truth, estimate, TOL);                 // estimation error, field by field — one line
```

Neither type is coupled to the other; an adapter bridges them. The comparison surface is small and easy
(poses and scalars), so the adapters are trivial.

## 2. A simulator is three separable models

Untangle the simulator into the three functions normally welded inside `XxxIOSim`:

1. **Dynamics (the plant):** `trueState' = f(trueState, commands, dt)` — pure physics. Knows nothing about
   sensors or robot code.
2. **Observation (the sensors):** `reading = h(trueState) + error` — maps truth to what a device reports,
   with noise, latency, quantization, dropout. Knows nothing about dynamics.
3. **Estimator (`RobotState`):** `estimate = g(readings)` — recovers state from noisy observations.

Welded together you can only test the whole loop. Split apart, each is a small unit with a clean contract.

## 3. Isolation = settable truth (not a shattered plant)

The key to testing a piece alone is that **the plant's true state has two ways in, not one:**

```java
plant.update(dt);                 // EVOLVE: integrate commands → truth moves (the full-loop path)
plant.setTruePose(somewhere);     // SET:    assign truth directly, skipping dynamics
```

So to test the **vision observation model** you do *not* drive the robot there — you *declare* the true pose
and read the camera:

```java
world.setTruePose(knownPose);                                   // no drivetrain, no driving
assertClose(simVision.read().pose(), knownPose, CAM_TOL);       // does the camera report the truth?
```

The sim only needs the robot's *commands* when the thing under test is the part that consumes them
(drivetrain dynamics, control tuning). Testing a downstream sensor, you cut the chain and inject the truth
it observes. **"Test in pieces" doesn't mean the plant is physically shattered into independent objects — it
means any slice of truth can be *set* rather than derived.**

(Structurally the plant is still best **federated** — central for genuinely coupled truth like chassis pose
/ field / game pieces, per-mechanism plants for independent mechanisms — so independent plants stay
individually runnable. But federation is a locality choice; *settable truth* is the isolation mechanism.)

## 4. Fidelity is a dial — the "perfect robot" is its zero setting

Think of simulation fidelity as a dial whose base setting is an **ideal robot**: zero tracking error,
sensors report exact truth. Two things make this precise:

- **Perfect ≠ instant.** The ideal robot still *integrates motion over time*, so motion still takes time —
  two mechanisms move concurrently, the camera sees you mid-travel, an auto path unfolds over seconds.
  "Perfect" zeroes the *error* terms; it does not skip time.
- **Error is a layer you switch on** over the ideal base: a *dynamics-error* layer (motor lag, friction)
  and an *observation-error* layer (noise, latency, dropout). Which layers you enable is set by what you're
  testing:

| Testing… | dynamics error | sensor error | command at |
|---|---|---|---|
| coordination / auto logic | off | off | setpoints (ideal plant) |
| control tuning (overshoot?) | **on** | off | voltage (dynamic plant) |
| estimator robustness (reject a bad tag?) | off | **on** | setpoints |

Your "reduced-complexity perfect robot" isn't a different simulator — it's this same plant with all the
error layers off. Fidelity becomes a *per-test setting*, which is exactly what serves "test the pieces
independently."

## 5. Command altitude decides how much plant you build

What the plant ultimately integrates is **velocity → position**. You choose what feeds that integration,
and the choice is the same `setpoint`-vs-`volts` fork as the device seam:

- Feed it a velocity **derived from voltage through a motor model** → **dynamic plant**. Needs a controller
  upstream (§6). Realistic; tests control.
- Feed it the **commanded** velocity/setpoint **directly** → **kinematic plant**. No voltage, no motor
  model, no controller in the loop — true position just tracks the command at the profiled rate. This *is*
  the perfect robot, and it makes the control-duplication question (§6) vanish because there is no control
  law in that path at all. The cost is the assumption: it tests logic, not dynamics.

The higher your command abstraction, the more trivially-perfect your plant can be.

## 6. The control law lives on exactly one side of the seam (so it's never duplicated)

The chain is `setpoint → [control law] → voltage → [motor model] → torque → ∫ → velocity → ∫ → position`.
Everything from *voltage* rightward is the plant (sim-only, nothing to duplicate). The piece at risk of
duplication is the **control law**. Where it lives decides everything:

- **Case A — control on the device** (command setpoints; Motion Magic / REV closed loop). The controller
  runs in motor firmware, not your code — and **the vendor sim runs that same controller for you**:
  `setControl(new MotionMagicVoltage(x))` in sim, then `simState.getMotorVoltage()` returns the voltage the
  *simulated firmware controller* computed. You never wrote setpoint→voltage and you don't rewrite it in
  sim. Only the plant is yours. Zero control duplication.
- **Case B — control on the RIO** (command volts; a WPILib `PIDController` in the subsystem). The controller
  is your code, *above* the IO line, so it runs in the same subsystem path in both modes. Sim swaps only
  what's below the line (real motor ↔ plant). One place.
- **The trap (the only way to get two copies):** command setpoints in real mode (no controller in your
  code — it's on-device) and then *hand-roll a PID inside `SimIO`* to manufacture a voltage for the plant.
  That controller has no real-mode counterpart and won't match the on-device tuning. Don't straddle: lean on
  the vendor sim (A), or move control onto the RIO (B). The decision is forced by *whether the vendor
  simulates the controller well enough.*

The capability interface (`01-capability-typed-devices.md`) pins the controller to one side and makes the
sim just another implementation:

```java
// Controller AT/BELOW the interface — your code never contains a setpoint→voltage line:
interface PositionMotor { void setPosition(double rad); }
class TalonFXPositionMotor implements PositionMotor { /* real: Motion Magic on-device */ }
class DynamicSimPositionMotor implements PositionMotor { /* vendor-simulated controller + plant */ }
class KinematicSimPositionMotor implements PositionMotor { /* integrate toward x — the perfect robot */ }
```

What you might write twice is a **plant at two fidelities** (kinematic vs. dynamic) — two *plants*, not two
*controllers*. That's the fidelity dial on purpose, not accidental duplication.

## 7. The plant wears the IO layer's interface in parallel

The sim's job is to fill the **same inputs the real IO fills**, so the code above the line can't tell which
world it's in. Real IO fills the inputs struct from device registers; sim IO fills it from the plant (±
whatever error layers are on). Same surface, two sources. This is why the plant and the existing
inputs/logging contract are one artifact seen from two sides, not a competing third mechanism — and it is
what makes the real↔sim swap a single object:

```java
static Hardware create(RobotMode mode, RobotConfig cfg) {
    return switch (mode) {
        case REAL   -> new RealHardware(cfg);                 // the real world IS the plant
        case SIM    -> new SimHardware(cfg, new PhysicsWorld(cfg));
        case REPLAY -> new ReplayHardware(cfg);               // log-fed; no physics (see costs)
    };
}
```

## 8. What the split unlocks — testing each piece alone

| Test | What you instantiate | What you assert |
|---|---|---|
| **Plant / dynamics** | one plant only | drive a voltage (or command); reaches target, respects limits, energy sane. No robot code, no sensors. |
| **Observation model** | a sim sensor + a *set* `PhysicsWorld` | set known truth → sensor returns truth ± characterized error; verify latency, dropout, an injected outlier. No dynamics. |
| **Estimator (`RobotState`)** | `RobotState` + observations from known truth | estimate converges within tolerance; a bad measurement is *rejected*. **Estimate-vs-truth via the adapter — impossible on a real robot.** |
| **Subsystem control** | one subsystem + its plant | commands reach setpoint and hold; no field, no vision. |
| **Whole-robot integration** | full `PhysicsWorld` + all sims + an auto routine | final true pose within tolerance of the plan. |

Each row is a different *subset* of the three models at a chosen fidelity — independently runnable.

## 9. Guardrails

1. **Plant ≠ `RobotState`.** Separate objects; truth vs. estimate. Compare via an adapter; never read the
   plant *as if* it were the estimate (that hides every sensor bug).
2. **No estimate leaks into truth.** The plant integrates commands and physics only; never read back
   anything `RobotState` computed, or sim becomes circular and flatters the estimator.
3. **Truth is settable.** Every quantity a downstream test needs to fix must be directly settable, so a
   sensor/estimator test can inject truth instead of driving to it.
4. **Control law on exactly one side of the seam.** On-device (vendor-simulated) or on-RIO (shared) — never
   the real loop on-device and a hand-rolled loop in `SimIO`.
5. **Observation models hold the error, not the plant.** Noise/latency/dropout live in the sensor sim, so
   estimator tests script the observation, not the physics.
6. **Federate by physical coupling; one ordered tick at fixed dt.** Central only for coupled truth;
   read commands → integrate plant → publish observations. maple-sim's `simulationPeriodic()` is this.
7. **The plant is owned by the simulated `Hardware`**, not an ambient singleton subsystems reach into.

## 10. When to use it — and when not

**Reach for it when:** you want to **test estimation** against ground truth; you have **coupled physics**
(vision that must see the true pose, game-piece/field interaction) where per-IO sim can't fabricate a
measurement; or you want each simulation layer to be a unit test, not just a drive-around demo.

**Don't, when:** your mechanisms are independent and you only need "does the elevator reach height in sim"
— a plain `ElevatorIOSim` is less machinery; or you won't write the tests the decomposition enables (the
split only pays off if you exercise the pieces).

## 11. Honest costs

- **Sim is only as good as the plant.** A materialized truth model can quietly diverge from the real robot
  (friction, backlash, CG shift). Green sim tests are necessary, not sufficient; document the plant's
  assumptions.
- **Command-altitude trade.** *Setpoints (Case A):* least code you own — vendor does control and its sim —
  but realism is hostage to the vendor sim, and a fast perfect-robot needs a *second* (kinematic) plant
  impl. *Volts (Case B):* one controller that runs everywhere and a trivial perfect-vs-real plant swap, but
  you own the tuning and forfeit on-device features (Motion Magic, FOC) unless you replicate them.
  **Recommendation:** command setpoints by default (keep your repo controller-free), drop to volts +
  RIO-control only on the mechanisms where you actually need to watch and tune the loop.
- **You maintain a parallel model.** Every mechanism added needs its plant + observation model kept in sync.
- **Orthogonal to replay.** This buys *physics simulation* and *estimation testing*, not AdvantageKit
  deterministic *log replay* (re-running a real match from logged inputs). Replay is the logging
  inputs-struct seam; keep it if you want both. `REPLAY` feeds logged inputs and needs no plant.

## Bottom line

`RobotState` is half of a pair — the degraded estimate the code reconstructs from sensors. Its missing dual
is the **plant**: a first-class object holding the *true* state the sensors are a lossy view of. Materialize
it, make its truth **settable**, give it a **fidelity dial** whose zero is your perfect robot, and keep the
control law on **one side of the seam** so nothing is duplicated. The simulator then splits into three
testable models — dynamics, observation, estimator — and because the plant wears the IO interface in
parallel and lives in the simulated `Hardware`, the whole real↔sim swap stays a single object. You can test
the plant with no robot code, a sensor against scripted truth, and your estimator against ground truth —
each in isolation, which is the entire reason to break simulation out this way.

## See also

- `01-capability-typed-devices.md` — the device seam and hardware object that *owns* the plant; the
  setpoint-vs-volts command altitude that decides kinematic vs. dynamic.
- `../build-spec/subsystems/07-robotstate.md` — the *estimate* half of the duality (the state seam, D7).
- `../build-spec/simulation.md` — the default per-IO sim, run modes, and replay this is an alternative to.
- Production precedent: **maple-sim** (`SimulatedArena` / `SwerveDriveSimulation` — a central true-state
  world, 16 corpus teams; 3647 Millennium Falcons locally) and **PhotonVision** `VisionSystemSim` (a sensor
  observing the true pose with error, 29 teams).
