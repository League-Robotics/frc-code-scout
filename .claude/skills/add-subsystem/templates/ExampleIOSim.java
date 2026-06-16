// TEMPLATE — wrap the WPILib physics model for YOUR archetype. Rename Example. WPILib imports ONLY.
// This file is the entire reason the subsystem is testable on a laptop.
package frc.robot.subsystems.example;

import edu.wpi.first.math.system.plant.DCMotor;
// ARCHETYPE — pick one:
import edu.wpi.first.wpilibj.simulation.ElevatorSim; // linear
// import edu.wpi.first.wpilibj.simulation.SingleJointedArmSim; // rotational
// import edu.wpi.first.wpilibj.simulation.FlywheelSim;          // velocity
// import edu.wpi.first.wpilibj.simulation.DCMotorSim;           // roller

public class ExampleIOSim implements ExampleIO {
  // Construct the matching sim with MEASURED constants — a guessed mass/MOI makes the test flaky.
  private final ElevatorSim sim =
      new ElevatorSim(
          DCMotor.getKrakenX60(1),
          ExampleConstants.GEARING,
          ExampleConstants.MASS_KG,
          ExampleConstants.DRUM_RADIUS_M,
          ExampleConstants.MIN_HEIGHT_M,
          ExampleConstants.MAX_HEIGHT_M,
          true, // simulate gravity
          ExampleConstants.MIN_HEIGHT_M);

  @Override
  public void setVoltage(double volts) {
    sim.setInputVoltage(volts);
    sim.update(0.02); // advance the physics one robot tick
  }

  @Override
  public double position() {
    return sim.getPositionMeters();
  }

  @Override
  public double velocity() {
    return sim.getVelocityMetersPerSecond();
  }
}
