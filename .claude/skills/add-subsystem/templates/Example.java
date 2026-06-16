// TEMPLATE — the subsystem. Holds ONE ExampleIO, owns the controller, one create() selection point.
// Imports NO vendor type and NO sibling subsystem (so it compiles as its own library).
package frc.robot.subsystems.example;

import edu.wpi.first.math.controller.ElevatorFeedforward; // ARCHETYPE: ElevatorFeedforward | ArmFeedforward | SimpleMotorFeedforward
import edu.wpi.first.math.controller.ProfiledPIDController;
import edu.wpi.first.math.trajectory.TrapezoidProfile;
import edu.wpi.first.wpilibj.RobotBase;
import edu.wpi.first.wpilibj2.command.Command;
import edu.wpi.first.wpilibj2.command.SubsystemBase;

public class Example extends SubsystemBase implements AutoCloseable {
  private final ExampleIO io;

  private final ProfiledPIDController pid =
      new ProfiledPIDController(
          ExampleConstants.kP, 0, ExampleConstants.kD,
          new TrapezoidProfile.Constraints(ExampleConstants.MAX_VELOCITY, ExampleConstants.MAX_ACCEL));

  // ARCHETYPE: ArmFeedforward (gravity tracks cos θ) for rotational; SimpleMotorFeedforward (no kG) for velocity.
  private final ElevatorFeedforward ff =
      new ElevatorFeedforward(ExampleConstants.kS, ExampleConstants.kG, ExampleConstants.kV);

  public Example(ExampleIO io) {
    this.io = io;
  }

  /** The single selection point: real hardware on the robot, physics sim everywhere else. */
  public static Example create() {
    return new Example(RobotBase.isReal() ? new ExampleIOTalonFX() : new ExampleIOSim());
  }

  /** Drive to a setpoint and hold. The control loop lives ABOVE the IO line, shared by Real and Sim. */
  public Command goTo(double goal) {
    return run(() -> {
          double feedback = pid.calculate(io.position(), goal);
          double feedforward = ff.calculate(pid.getSetpoint().velocity);
          io.setVoltage(feedback + feedforward);
        })
        .finallyDo(() -> io.setVoltage(0));
  }

  public boolean atGoal() {
    return pid.atGoal();
  }

  public double position() {
    return io.position();
  }

  @Override
  public void close() throws Exception {
    io.close();
  }
}
