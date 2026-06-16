// TEMPLATE — mock below (the Sim IO), test above (the subsystem). Rename Example.
// Needs the test harness from `setup-testing` (HAL bootstrap + deterministic fastForward).
package frc.robot.subsystems.example;

import static org.junit.jupiter.api.Assertions.assertEquals;
// import static frc.robot.lib.UnitTestingUtil.*;   // setupTests, run, fastForward, reset

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

public class ExampleTest {
  private Example example;

  @BeforeEach
  void setup() {
    // setupTests();                    // boot the simulated HAL + sim time
    example = new Example(new ExampleIOSim()); // <-- the mock is just another ExampleIO
  }

  @AfterEach
  void teardown() throws Exception {
    // reset(example);                  // cancel commands + close the subsystem
    example.close();
  }

  @ParameterizedTest
  @ValueSource(doubles = {0.1, 0.5, 1.0})
  void reachesSetpoint(double target) {
    // run(example.goTo(target));       // schedule the command
    // fastForward();                   // step CommandScheduler + sim time deterministically
    assertEquals(target, example.position(), 0.02);
  }
}
