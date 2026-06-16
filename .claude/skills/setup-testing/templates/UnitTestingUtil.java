// TEMPLATE — the WPILib unit-test harness. Place in your test-support package (e.g. frc.robot.lib).
// Boots a simulated HAL and steps sim time deterministically so subsystem tests run with no hardware.
package frc.robot.lib;

import static edu.wpi.first.units.Units.Seconds;

import edu.wpi.first.hal.AllianceStationID;
import edu.wpi.first.hal.HAL;
import edu.wpi.first.units.measure.Time;
import edu.wpi.first.wpilibj.simulation.DriverStationSim;
import edu.wpi.first.wpilibj.simulation.SimHooks;
import edu.wpi.first.wpilibj2.command.Command;
import edu.wpi.first.wpilibj2.command.CommandScheduler;

public final class UnitTestingUtil {
  public static final Time TICK = Seconds.of(0.02);

  private UnitTestingUtil() {}

  /** Boot the simulated HAL + DriverStation. Call in @BeforeEach. */
  public static void setupTests() {
    assert HAL.initialize(500, 0);
    DriverStationSim.resetData();
    DriverStationSim.setAllianceStationId(AllianceStationID.Blue1);
    DriverStationSim.setEnabled(true);
    DriverStationSim.setTest(true);
    DriverStationSim.notifyNewData();
    SimHooks.restartTiming();
  }

  /** Cancel all commands and close the given subsystems. Call in @AfterEach. */
  public static void reset(AutoCloseable... subsystems) throws Exception {
    CommandScheduler.getInstance().unregisterAllSubsystems();
    CommandScheduler.getInstance().cancelAll();
    for (AutoCloseable s : subsystems) s.close();
  }

  /** Step the scheduler AND sim time together — deterministic fast-forward, not wall-clock. */
  public static void fastForward(int ticks) {
    for (int i = 0; i < ticks; i++) {
      CommandScheduler.getInstance().run();
      SimHooks.stepTiming(TICK.in(Seconds));
    }
  }

  public static void fastForward(Time time) {
    fastForward((int) (time.in(Seconds) / TICK.in(Seconds)));
  }

  /** Default fast-forward: 4 seconds. */
  public static void fastForward() {
    fastForward(Seconds.of(4));
  }

  /** Schedule a command and advance one tick. */
  public static void run(Command command) {
    command.schedule();
    fastForward(1);
  }

  /** Schedule a command and run until it finishes (careful: an endless command loops forever). */
  public static void runToCompletion(Command command) {
    command.schedule();
    fastForward(1);
    while (command.isScheduled()) fastForward(1);
  }
}
