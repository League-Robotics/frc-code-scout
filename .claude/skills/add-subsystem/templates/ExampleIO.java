// TEMPLATE — rename Example -> <YourMechanism>, example -> <yourmechanism>.
// Loop-ABOVE style (the subsystem owns the controller). This file imports NO vendor SDK.
package frc.robot.subsystems.example;

/** Hardware contract for the {@link Example} subsystem. */
public interface ExampleIO extends AutoCloseable {

  /** Run the motor at the given volts. The subsystem computes this from PID + feedforward. */
  void setVoltage(double volts);

  /** Mechanism position. Units: meters (linear archetype) or radians (rotational). */
  double position();

  /** Mechanism velocity (per second). */
  double velocity();

  /** Stop output. */
  default void stop() {
    setVoltage(0);
  }

  @Override
  default void close() {}

  // VELOCITY archetype: replace position()/velocity() control with
  //   void setVelocity(double radPerSec, double ffVolts);   // closed-loop on the motor
  // and keep velocity() as the reading. See knowledge/build-spec/subsystems/03-velocity.md.
  //
  // SENSOR-ONLY (vision): there is NO setVoltage. The contract is updateInputs(observations)
  // feeding RobotState.addVisionObservation. See subsystems/05-vision-sensor.md (different template).
}
