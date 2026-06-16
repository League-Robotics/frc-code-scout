// TEMPLATE — the ONE place a vendor SDK is allowed. Rename Example; swap TalonFX for your device.
// If you see com.ctre / com.revrobotics anywhere ABOVE the IO line, the seam has leaked.
package frc.robot.subsystems.example;

import static edu.wpi.first.units.Units.Radians;

import com.ctre.phoenix6.configs.TalonFXConfiguration;
import com.ctre.phoenix6.hardware.TalonFX;
import com.ctre.phoenix6.signals.NeutralModeValue;

public class ExampleIOTalonFX implements ExampleIO {
  private final TalonFX motor = new TalonFX(ExampleConstants.MOTOR_ID);

  public ExampleIOTalonFX() {
    var cfg = new TalonFXConfiguration();
    cfg.MotorOutput.NeutralMode = NeutralModeValue.Brake;
    cfg.CurrentLimits.SupplyCurrentLimit = ExampleConstants.CURRENT_LIMIT;
    cfg.Feedback.SensorToMechanismRatio = ExampleConstants.GEARING;
    motor.getConfigurator().apply(cfg);
    // ROTATIONAL: fuse an absolute encoder here (FeedbackSensorSource = RemoteCANcoder).
  }

  @Override
  public void setVoltage(double volts) {
    motor.setVoltage(volts);
  }

  @Override
  public double position() {
    return motor.getPosition().getValue().in(Radians); // convert to your mechanism units (m or rad)
  }

  @Override
  public double velocity() {
    return motor.getVelocity().getValueAsDouble();
  }

  @Override
  public void close() {
    motor.close();
  }
}
