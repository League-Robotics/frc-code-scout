---
title: Appendix E — The minimal worked example
weight: 5
---

**This is the whole book, once, in the smallest robot that still has all the layers.** Two wheels,
one color sensor, one job: *drive forward until the sensor sees the red line, then stop.* That is
enough to need a hardware abstraction layer, two subsystems, a planner, a configuration object, and
commands — and every one of them is the same four-part block from
[ch. 25](../part-3/25-portable-component-model.md):

> **`Config`** in once · **`Command_in`** each tick · **`State`** out each tick · **`Command_out`**
> returned, never pushed — advanced by one pure `update(Command_in, Observations)`.

[Ch. 25](../part-3/25-portable-component-model.md) worked the contract for a single elevator;
[ch. 26](../part-3/26-portable-motor-interface.md)–[28](../part-3/28-robotstate-superstructure-blocks.md)
worked it at one altitude at a time. This appendix stacks three altitudes into one running (well,
readable) robot, so you can watch a command descend the tree and state climb back up. It is
*illustrative of the contract, not a finished library* — real code carries more fields, more status,
and the lifecycle.

## The cast, by fill-pattern

The fill-pattern *is* the taxonomy ([ch. 25](../part-3/25-portable-component-model.md)): which
channels a block populates tells you what it is.

| Block | Layer | `Config` | `Command_in` | `State` | `Command_out` |
|---|---|:--:|---|---|---|
| `MotorIO` (×2) | HAL leaf | CAN id, inversion | `MotorCommand` (volts) | `MotorState` | — (it *is* the metal) |
| `ColorSensorIO` | HAL leaf | I²C port | — | `ColorSensorState` (raw counts) | — |
| `Drive` | subsystem | gearing, wheel radius, gains | `DriveCommand` (m/s) | `DriveState` | 2× `MotorCommand` |
| `ColorSense` | subsystem | target color, tolerance | — *(a sensor block)* | `ColorSenseState` (meaning) | — |
| `Superstructure` | executive | seek speed | `Goal` (driver intent) | `PlannerState` (mode, ready) | 1× `DriveCommand` |

Read the rows and the recursion from [ch. 28](../part-3/28-robotstate-superstructure-blocks.md) is
visible: the planner and the drive are *the same kind of block* — all four channels filled — differing
only in whether `Command_out` feeds subsystems or motors. `ColorSense` fills neither command channel:
that emptiness is what makes it a sensor, not a controller. This robot is deliberately too small to
need a `RobotState` — with one drivebase and one sensor there is nothing to fuse — but when vision or
odometry consumers arrive, the estimator block of
[ch. 28](../part-3/28-robotstate-superstructure-blocks.md) drops in beside these without touching them.

```d2
direction: down
DRV: "Driver — A button"
SUP: "Superstructure (planner block)\nupdate(Goal, obs) → DriveCommand"
DR: "Drive (subsystem block)\nupdate(DriveCommand, obs) → 2× MotorCommand"
CS: "ColorSense (sensor block)\nupdate(obs) → ColorSenseState"
LM: "MotorIO left"
RM: "MotorIO right"
CIO: "ColorSensorIO"
DRV -> SUP: "Goal (Command_in)"
SUP -> DR: "DriveCommand (Command_out)"
DR -> LM: "MotorCommand"
DR -> RM: "MotorCommand"
LM -> DR: "MotorState (observations)" { style.stroke-dash: 4 }
RM -> DR: "MotorState (observations)" { style.stroke-dash: 4 }
CIO -> CS: "raw color (observations)" { style.stroke-dash: 4 }
CS -> SUP: "ColorSenseState (state up)" { style.stroke-dash: 4 }
DR -> SUP: "DriveState (state up)" { style.stroke-dash: 4 }
```

On disk it is the quartet-per-subsystem layout of [ch. 3](../part-1/03-the-io-seam.md), plus one pure
block file per level:

```text
frc/robot/
  Constants.java                 // every Config POD, filled in ONE place
  RobotContainer.java            // run-mode selection + button → goal bindings
  superstructure/
    Superstructure.java          //   shell: WPILib subsystem, wiring layer
    PlannerBlock.java            //   pure: the guarded transition function
    Goal.java  PlannerConfig.java  PlannerState.java  PlannerObs.java  PlannerTick.java
  subsystems/
    drive/
      Drive.java                 //   shell
      DriveBlock.java            //   pure
      DriveConfig.java  DriveCommand.java  DriveState.java  DriveObs.java  DriveTick.java
    colorsense/
      ColorSense.java            //   shell
      ColorSenseBlock.java       //   pure
      ColorSenseConfig.java  ColorSenseState.java  ColorSenseObs.java
  hal/
    MotorIO.java  MotorCommand.java  MotorState.java
    MotorIOSparkMax.java         // the ONLY files that import a vendor SDK
    MotorIOSim.java
    ColorSensorIO.java  ColorSensorState.java
    ColorSensorIORevV3.java
    ColorSensorIOSim.java
```

## Layer 1 — the hardware abstraction layer (leaf IO)

The leaf is where the model touches metal ([ch. 26](../part-3/26-portable-motor-interface.md)). Each
device gets a POD pair — its `Command_in` and its `State`, the state-space `u`/`x` — and an `…IO`
interface that is nothing but the impure shell around them. Units are SI throughout (rad, m, V, A).

```java
// hal/MotorState.java — the leaf's State channel: what the motor is measurably doing (x)
public record MotorState(
    double positionRad, double velocityRadS,
    double appliedVolts, double currentAmps,
    boolean connected) {}

// hal/MotorCommand.java — the leaf's Command_in (u); this robot only ever needs voltage mode
public record MotorCommand(double volts) {
  public static MotorCommand neutral() { return new MotorCommand(0.0); }
}

// hal/MotorIO.java — the downward edge of the leaf block: read samples in, apply pushes out
public interface MotorIO {
  MotorState read();               // once per tick, into a POD
  void apply(MotorCommand cmd);    // once per tick, out to metal
}
```

A sensor leaf is the same shape with the command half *deleted* — no `apply`, because nothing
commands a sensor:

```java
// hal/ColorSensorState.java — raw device truth: normalized color counts + proximity
public record ColorSensorState(
    double red, double green, double blue,
    int proximity, boolean connected) {}

// hal/ColorSensorIO.java — a pure source: State out, nothing in
public interface ColorSensorIO {
  ColorSensorState read();
}
```

The implementations are the only files in the robot allowed to import a vendor SDK, and they are
named by device, not `…Real` ([ch. 3](../part-1/03-the-io-seam.md)) — the name documents the vendor
at the seam:

```java
// hal/MotorIOSparkMax.java — com.revrobotics lives HERE and nowhere above
public class MotorIOSparkMax implements MotorIO {
  private final SparkMax motor;
  private final RelativeEncoder encoder;

  public MotorIOSparkMax(int canId, boolean inverted) {
    motor = new SparkMax(canId, MotorType.kBrushless);
    motor.configure(new SparkMaxConfig().inverted(inverted),
        ResetMode.kResetSafeParameters, PersistMode.kPersistParameters);
    encoder = motor.getEncoder();
  }

  @Override public MotorState read() {
    return new MotorState(
        Units.rotationsToRadians(encoder.getPosition()),
        Units.rotationsPerMinuteToRadiansPerSecond(encoder.getVelocity()),
        motor.getAppliedOutput() * motor.getBusVoltage(),
        motor.getOutputCurrent(),
        !motor.getFaults().can);
  }

  @Override public void apply(MotorCommand cmd) { motor.setVoltage(cmd.volts()); }
}

// hal/ColorSensorIORevV3.java
public class ColorSensorIORevV3 implements ColorSensorIO {
  private final ColorSensorV3 sensor = new ColorSensorV3(I2C.Port.kOnboard);

  @Override public ColorSensorState read() {
    var c = sensor.getColor();
    return new ColorSensorState(c.red, c.green, c.blue,
        sensor.getProximity(), sensor.isConnected());
  }
}
```

And the sim implementations — WPILib only — are just another `…IO`, which is why the sim *is* the
mock every test uses:

```java
// hal/MotorIOSim.java — a physics model behind the same interface
public class MotorIOSim implements MotorIO {
  private final DCMotorSim sim = new DCMotorSim(
      LinearSystemId.createDCMotorSystem(DCMotor.getNEO(1), 0.004, Constants.DRIVE.gearRatio()),
      DCMotor.getNEO(1));
  private double volts = 0.0;

  @Override public MotorState read() {
    sim.setInputVoltage(volts);
    sim.update(0.020);
    return new MotorState(sim.getAngularPositionRad(), sim.getAngularVelocityRadPerSec(),
        volts, sim.getCurrentDrawAmps(), true);
  }

  @Override public void apply(MotorCommand cmd) { volts = cmd.volts(); }
}

// hal/ColorSensorIOSim.java — a settable fake: a test (or a sim script) decides what the robot sees
public class ColorSensorIOSim implements ColorSensorIO {
  private ColorSensorState next = new ColorSensorState(0.25, 0.5, 0.25, 0, true);
  public void set(ColorSensorState s) { next = s; }
  @Override public ColorSensorState read() { return next; }
}
```

## Layer 2 — the subsystems

A subsystem is two files that must never be confused: a **pure block** (the four PODs and the
`update`) and a **thin impure shell** (a WPILib `Subsystem` whose `periodic()` does exactly
`read → update → apply`). The block computes; the shell touches the world.

### Drive — a controller block over two motor leaves

First the four channels plus the observations and the tick, each its own POD:

```java
// subsystems/drive/DriveConfig.java — identity + calibration; set once (§Config, ch. 25)
public record DriveConfig(
    int leftCanId, int rightCanId,
    double gearRatio, double wheelRadiusM,
    double kP, double kV,            // ONE velocity loop, above the IO line (Decision A, ch. 3)
    double maxSpeedMps) {}

// subsystems/drive/DriveCommand.java — Command_in: intent in field units. Volts never appear here.
public record DriveCommand(double speedMps) {
  public static DriveCommand stop() { return new DriveCommand(0.0); }
}

// subsystems/drive/DriveState.java — State = estimate + status (ch. 25)
public record DriveState(
    double distanceM, double speedMps,     // estimate
    boolean atGoal, boolean connected) {   // status
  public static DriveState initial() { return new DriveState(0, 0, false, false); }
}

// subsystems/drive/DriveObs.java — Observations: the children's State + the tick's time.
// The timestamp is data, delivered like any other fact — no block ever reads a clock.
public record DriveObs(double timestampS, MotorState left, MotorState right) {}

// subsystems/drive/DriveTick.java — what update RETURNS: State′ and Command_out
public record DriveTick(DriveState state, MotorCommand left, MotorCommand right) {}
```

Then the pure step. No hardware handle, no clock, no scheduler — feedforward plus proportional
feedback, written once, shared by real and sim because the loop is above the IO line:

```java
// subsystems/drive/DriveBlock.java
public class DriveBlock {
  private final DriveConfig cfg;

  public DriveBlock(DriveConfig cfg) { this.cfg = cfg; }

  public DriveTick update(DriveCommand cmd, DriveObs obs) {
    double distanceM = (toMeters(obs.left().positionRad())
                      + toMeters(obs.right().positionRad())) / 2.0;
    double speedMps  = (toMps(obs.left().velocityRadS())
                      + toMps(obs.right().velocityRadS())) / 2.0;

    double target = Math.max(-cfg.maxSpeedMps(), Math.min(cfg.maxSpeedMps(), cmd.speedMps()));
    double volts  = cfg.kV() * target + cfg.kP() * (target - speedMps);

    var state = new DriveState(distanceM, speedMps,
        Math.abs(target - speedMps) < 0.05,
        obs.left().connected() && obs.right().connected());
    return new DriveTick(state,                       // emission is the return value —
        new MotorCommand(volts), new MotorCommand(volts));  // update never touches a MotorIO
  }

  private double toMeters(double rad) { return rad / cfg.gearRatio() * cfg.wheelRadiusM(); }
  private double toMps(double radS)   { return radS / cfg.gearRatio() * cfg.wheelRadiusM(); }
}
```

And the shell — the only impure code, three lines of wiring plus logging:

```java
// subsystems/drive/Drive.java
public class Drive extends SubsystemBase {
  private final DriveBlock block;
  private final MotorIO left, right;                  // vendor types live below this line
  private DriveCommand cmd = DriveCommand.stop();
  private DriveState state = DriveState.initial();

  public Drive(DriveConfig cfg, MotorIO left, MotorIO right) {
    this.block = new DriveBlock(cfg);
    this.left = left;
    this.right = right;
  }

  public void accept(DriveCommand c) { cmd = c; }     // Command_in — the wiring layer calls this
  public DriveState state() { return state; }         // State — flows up to whoever observes it

  @Override public void periodic() {
    var obs  = new DriveObs(Timer.getFPGATimestamp(), left.read(), right.read()); // 1. read
    var tick = block.update(cmd, obs);                                            // 2. pure step
    left.apply(tick.left());                                                      // 3. actuate
    right.apply(tick.right());
    state = tick.state();
    // 4. log cmd, obs, tick — all PODs, so the log IS the replay input (ch. 29)
  }
}
```

### ColorSense — a sensor block over one sensor leaf

The sensor subsystem exists to convert *device truth* (raw color counts) into *robot meaning* ("that
is the line we stop at"). Its command channels are empty — `update` takes only observations and
returns only state — which per the fill-pattern table makes it a sensor block, the same shape
`RobotState` would have ([ch. 28](../part-3/28-robotstate-superstructure-blocks.md)):

```java
// subsystems/colorsense/ColorSenseConfig.java — what color we hunt, and how sure we must be
public record ColorSenseConfig(
    double targetRed, double targetGreen, double targetBlue,
    double matchTolerance) {}

// subsystems/colorsense/ColorSenseState.java — meaning, not counts: estimate + status
public record ColorSenseState(double matchError, boolean onTarget, boolean connected) {
  public static ColorSenseState initial() { return new ColorSenseState(1.0, false, false); }
}

// subsystems/colorsense/ColorSenseObs.java
public record ColorSenseObs(double timestampS, ColorSensorState raw) {}

// subsystems/colorsense/ColorSenseBlock.java — no Command_in, no Command_out: update(obs) only
public class ColorSenseBlock {
  private final ColorSenseConfig cfg;

  public ColorSenseBlock(ColorSenseConfig cfg) { this.cfg = cfg; }

  public ColorSenseState update(ColorSenseObs obs) {
    double err = Math.abs(obs.raw().red()   - cfg.targetRed())
               + Math.abs(obs.raw().green() - cfg.targetGreen())
               + Math.abs(obs.raw().blue()  - cfg.targetBlue());
    boolean onTarget = obs.raw().connected() && err < cfg.matchTolerance();
    return new ColorSenseState(err, onTarget, obs.raw().connected());
  }
}

// subsystems/colorsense/ColorSense.java — the shell; note there is nothing to apply
public class ColorSense extends SubsystemBase {
  private final ColorSenseBlock block;
  private final ColorSensorIO io;
  private ColorSenseState state = ColorSenseState.initial();

  public ColorSense(ColorSenseConfig cfg, ColorSensorIO io) {
    this.block = new ColorSenseBlock(cfg);
    this.io = io;
  }

  public ColorSenseState state() { return state; }

  @Override public void periodic() {
    state = block.update(new ColorSenseObs(Timer.getFPGATimestamp(), io.read()));
    // log obs + state
  }
}
```

## Layer 3 — the superstructure (the planner)

The executive is the same four-channel block one altitude up
([ch. 28](../part-3/28-robotstate-superstructure-blocks.md)): its `Command_in` is a robot-wide
`Goal`, its `Observations` are its children's `State`, its `Command_out` is a per-subsystem command,
and its `update` **is** the guarded transition function of
[ch. 5](../part-1/05-the-coordination-seam.md) — every mode change and every safety rule in one
function, so there is exactly one place to read when the robot does something surprising.

```java
// superstructure/Goal.java — Command_in at the top of the tree: driver intent, nothing lower
public enum Goal { IDLE, SEEK_LINE }

// superstructure/PlannerConfig.java
public record PlannerConfig(double seekSpeedMps) {}

// superstructure/PlannerState.java — at this altitude status IS the primary output (ch. 25)
public record PlannerState(Goal goal, Mode mode, boolean ready) {
  public enum Mode { IDLE, SEEKING, HOLDING }
  public static PlannerState initial() { return new PlannerState(Goal.IDLE, Mode.IDLE, false); }
}

// superstructure/PlannerObs.java — the planner sees BLOCK state, never devices: no volts, no counts
public record PlannerObs(double timestampS, DriveState drive, ColorSenseState color) {}

// superstructure/PlannerTick.java — one outgoing edge: the drive. The sensor gets no command.
public record PlannerTick(PlannerState state, DriveCommand driveCmd) {}
```

```java
// superstructure/PlannerBlock.java — the pure planner
public class PlannerBlock {
  private final PlannerConfig cfg;
  private PlannerState.Mode mode = PlannerState.Mode.IDLE;  // internal memory (ch. 25), not State

  public PlannerBlock(PlannerConfig cfg) { this.cfg = cfg; }

  public PlannerTick update(Goal goal, PlannerObs obs) {
    mode = switch (mode) {                          // ALL transitions pass through this switch
      case IDLE    -> goal == Goal.SEEK_LINE ? PlannerState.Mode.SEEKING : PlannerState.Mode.IDLE;
      case SEEKING -> goal == Goal.IDLE        ? PlannerState.Mode.IDLE
                    : obs.color().onTarget()   ? PlannerState.Mode.HOLDING  // the sensor ends the seek
                    : PlannerState.Mode.SEEKING;
      case HOLDING -> goal == Goal.SEEK_LINE ? PlannerState.Mode.HOLDING : PlannerState.Mode.IDLE;
    };

    // The interlock, in the one legal place: never drive blind. If the sensor block reports
    // unhealthy, the seek is vetoed regardless of what the driver requested.
    boolean safeToDrive = obs.color().connected();
    var driveCmd = (mode == PlannerState.Mode.SEEKING && safeToDrive)
        ? new DriveCommand(cfg.seekSpeedMps())
        : DriveCommand.stop();

    return new PlannerTick(
        new PlannerState(goal, mode, mode == PlannerState.Mode.HOLDING),
        driveCmd);                                   // returned, never pushed
  }
}
```

The planner's shell is where the two coupling rules meet without contradiction: the *block* holds no
reference to any child (it returns its commands), while the *shell* — which is part of the outer
wiring layer — routes `Command_out` to the child's `Command_in`:

```java
// superstructure/Superstructure.java
public class Superstructure extends SubsystemBase {
  private final PlannerBlock block;
  private final Drive drive;              // shells, never blocks — the pure planner can't see these
  private final ColorSense colorSense;
  private Goal goal = Goal.IDLE;
  private PlannerState state = PlannerState.initial();

  public Superstructure(PlannerConfig cfg, Drive drive, ColorSense colorSense) {
    this.block = new PlannerBlock(cfg);
    this.drive = drive;
    this.colorSense = colorSense;
  }

  // Intent enters the tree as a WPILib Command — a button binds to a GOAL, never to a motor.
  public Command requestGoal(Goal g) { return runOnce(() -> goal = g); }
  public PlannerState state() { return state; }

  @Override public void periodic() {
    var obs  = new PlannerObs(Timer.getFPGATimestamp(),
        drive.state(), colorSense.state());          // state up: children's last-published State
    var tick = block.update(goal, obs);
    drive.accept(tick.driveCmd());                   // command down: Command_out → child Command_in
    state = tick.state();
    // log goal, obs, tick
  }
}
```

One honest scheduling note: `drive.state()` is the state the drive published on its own last
`periodic()`, so state climbs the tree with one tick of transport delay — exactly as signals settle
through a block diagram. It is deterministic, it is logged, and at 50 Hz it is invisible; do not
"fix" it by reaching inside the child.

## The configuration object

Every `Config` POD is *defined* next to its block and *filled* in exactly one file. Numbers live
here and nowhere else — a CAN id in a subsystem file is a smell:

```java
// Constants.java
public final class Constants {
  public enum Mode { REAL, SIM }
  public static final Mode MODE = RobotBase.isReal() ? Mode.REAL : Mode.SIM;

  public static final DriveConfig DRIVE = new DriveConfig(
      1, 2,          // CAN ids: left, right
      8.46,          // gear ratio
      0.0762,        // wheel radius, m (3 in)
      0.5, 2.3,      // kP (V per m/s of error), kV (V per m/s)
      3.0);          // max speed, m/s

  public static final ColorSenseConfig COLOR = new ColorSenseConfig(
      0.55, 0.32, 0.13,   // red field tape, normalized RGB
      0.12);              // match tolerance

  public static final PlannerConfig PLANNER = new PlannerConfig(1.0); // seek at 1 m/s
}
```

The boundary test from [ch. 25](../part-3/25-portable-component-model.md) applies to every field: if
it changes every loop it is a `Command`; if it identifies or calibrates the block across a session it
is `Config`. Nothing in this file changes during a match.

## Commands and the wiring layer

`RobotContainer` is the outer wiring layer: it owns the **selection point** (the only code that
knows which implementation backs each seam, keyed off run mode — [ch. 3](../part-1/03-the-io-seam.md))
and the **bindings** (buttons carry intent; no binding ever names a motor or a voltage):

```java
// RobotContainer.java
public class RobotContainer {
  private final Drive drive;
  private final ColorSense colorSense;
  private final Superstructure superstructure;
  private final CommandXboxController controller = new CommandXboxController(0);

  public RobotContainer() {
    switch (Constants.MODE) {                        // the selection point
      case REAL -> {
        drive = new Drive(Constants.DRIVE,
            new MotorIOSparkMax(Constants.DRIVE.leftCanId(), false),
            new MotorIOSparkMax(Constants.DRIVE.rightCanId(), true));
        colorSense = new ColorSense(Constants.COLOR, new ColorSensorIORevV3());
      }
      case SIM -> {
        drive = new Drive(Constants.DRIVE, new MotorIOSim(), new MotorIOSim());
        colorSense = new ColorSense(Constants.COLOR, new ColorSensorIOSim());
      }
    }
    superstructure = new Superstructure(Constants.PLANNER, drive, colorSense);

    // Commands: the driver expresses INTENT. The planner owns execution.
    controller.a().onTrue(superstructure.requestGoal(Goal.SEEK_LINE));
    controller.b().onTrue(superstructure.requestGoal(Goal.IDLE));
  }

  // The same goal is an autonomous routine for free — intent is reusable (ch. 5):
  public Command autoSeekLine() {
    return superstructure.requestGoal(Goal.SEEK_LINE)
        .andThen(Commands.waitUntil(() -> superstructure.state().ready()));
  }
}
```

Follow one press of the A button through the tree: the binding sets a `Goal` (intent); next tick the
planner's pure `update` turns `SEEK_LINE` into a `DriveCommand` of 1.0 m/s (plan); the drive's pure
`update` turns 1.0 m/s into ~2.8 V of feedforward-plus-feedback (control); the `MotorIO` turns volts
into a vendor call (metal). Meanwhile raw color counts climb the other way, becoming `onTarget = true`
at the sensor block and a `SEEKING → HOLDING` transition at the planner, which zeroes the
`DriveCommand` on the way back down. Four layers, and no layer speaks a vocabulary that belongs to
another.

## The payoff — testing the plan with PODs

Because every `update` is a pure function of PODs, the interesting behavior of this robot — *does it
actually stop on the line? does it refuse to drive with a dead sensor?* — is testable with no
scheduler, no HAL bootstrap, and no hardware. Construct observations by hand and assert on the tick:

```java
class PlannerBlockTest {
  private PlannerObs obs(double t, ColorSenseState color) {
    return new PlannerObs(t, new DriveState(0, 0, false, true), color);
  }
  private static final ColorSenseState OFF_LINE  = new ColorSenseState(0.9, false, true);
  private static final ColorSenseState ON_LINE   = new ColorSenseState(0.05, true, true);
  private static final ColorSenseState DEAD      = new ColorSenseState(1.0, false, false);

  @Test
  void seekDrivesUntilLineThenHolds() {
    var block = new PlannerBlock(Constants.PLANNER);

    var seeking = block.update(Goal.SEEK_LINE, obs(0.00, OFF_LINE));
    assertEquals(1.0, seeking.driveCmd().speedMps());        // seeking: commanded at seek speed

    var holding = block.update(Goal.SEEK_LINE, obs(0.02, ON_LINE));
    assertEquals(0.0, holding.driveCmd().speedMps());        // line seen: the plan halts the drive
    assertTrue(holding.state().ready());
  }

  @Test
  void deadSensorVetoesTheSeek() {
    var block = new PlannerBlock(Constants.PLANNER);
    var tick = block.update(Goal.SEEK_LINE, obs(0.00, DEAD));
    assertEquals(0.0, tick.driveCmd().speedMps());           // the interlock, provably enforced
  }
}
```

The same trick works one layer down (`DriveBlock`: feed a `DriveObs`, assert on volts) and one layer
up in sim (bind the `ColorSensorIOSim`, run the whole robot, script the line appearing). And because
the shells log exactly the PODs the blocks consume and return, the match log *is* a replay input
([ch. 29](../part-3/29-telemetry-replay-tests.md)) — the same `update` functions re-run over recorded
`Command_in` + `Observations` reproduce the match decision-for-decision.

## Checklist — what the example just demonstrated

- **Four channels at every altitude** — `Config` / `Command_in` / `State` / `Command_out`, as PODs,
  for the motor, the sensor, both subsystems, and the planner; the fill-pattern classified each.
- **One pure `update` per block** — emission as the return value, never `child.set…` from inside a
  block; the shells (and only the shells) touch hardware and route commands.
- **No clock reads inside `update`** — every timestamp arrived inside an `Obs` POD.
- **Vendor confinement** — `com.revrobotics` appears in `MotorIOSparkMax` and `ColorSensorIORevV3`
  and nowhere else; swap to TalonFX by writing one new leaf file.
- **Config is a channel, filled once** — every number in `Constants`, defined beside its block.
- **Commands are the edges** — a button binds to a `Goal`; the planner's `Command_out` is the
  drive's `Command_in`; the drive's `Command_out` is the motors'. No layer skips a level.
- **The interlock lives in one function** — the dead-sensor veto is in `PlannerBlock.update` and is
  unit-tested in four lines.

If you can find these seven properties in your own robot — whatever the mechanisms — the
architecture is intact.
