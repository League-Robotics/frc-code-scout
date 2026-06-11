# Rubric evidence — `Reefscape2025`

Mechanical candidates from ast-grep + filesystem. **Confirm every level by opening the cited files.**

| Dim | Candidate | AST hits | Key filesystem signal |
|---|---|---|---|
| D1 Architecture | **3** | 29 | 29 IO/inputs decls |
| D2 Coordination | **3** | 4 | 4 state/coord decls |
| D3 Simulation | **2** | 3 | sim hits 3 |
| D4 Testing | **0** | 0 | test files 0, CI-test 0 |
| D5 Logging | **3** | 18 | AdvKit vendordep=yes |
| D6 Auto/Path | **3** | 3 | PP paths 252, traj/chor 0 |
| D7 Vision | **3** | 3 | 3 vision hits |
| D8 Sustain | **3** | 0 | README 115L, CI 1, spotless 0 |

**Heuristic Σ (floor): 20/32** — candidates only; confirm before reporting.

## Evidence (open these)


### D1 Architecture
- `src/main/java/frc/robot/subsystems/vision/VisionIOLimelight.java:14` — d1-io-inputs-method — `public void updateInputs(VisionIOInputs inputs) {`
- `src/main/java/frc/robot/subsystems/vision/VisionIO.java:7` — d1-io-interface — `public interface VisionIO {`
- `src/main/java/frc/robot/subsystems/vision/VisionIO.java:21` — d1-io-inputs-method — `public default void updateInputs(VisionIOInputs inputs) {}`
- `src/main/java/frc/robot/subsystems/superstructure/climb/ClimbIONeo.java:27` — d1-io-inputs-method — `public void updateInputs(ClimbIOInputs inputs) {`
- `src/main/java/frc/robot/subsystems/superstructure/elevator/ElevatorIO.java:7` — d1-io-interface — `public interface ElevatorIO {`
- `src/main/java/frc/robot/subsystems/superstructure/elevator/ElevatorIO.java:28` — d1-io-inputs-method — `public default void updateInputs(ElevatorIOInputs inputs) {}`
- `src/main/java/frc/robot/subsystems/superstructure/climb/ClimbIO.java:20` — d1-io-inputs-method — `public default void updateInputs(ClimbIOInputs inputs) {}`
- `src/main/java/frc/robot/subsystems/superstructure/climb/ClimbIO.java:7` — d1-io-interface — `public interface ClimbIO {`
- `src/main/java/frc/robot/subsystems/superstructure/elevator/ElevatorIOKraken.java:37` — d1-io-inputs-method — `@Override`
- `src/main/java/frc/robot/subsystems/superstructure/climb/ClimbIOKraken.java:32` — d1-io-inputs-method — `@Override`
- `src/main/java/frc/robot/subsystems/superstructure/elevator/ElevatorIONeo.java:33` — d1-io-inputs-method — `@Override`
- `src/main/java/frc/robot/subsystems/superstructure/claw/algae/AlgaeClawIOKraken.java:24` — d1-io-inputs-method — `@Override`

### D2 Coordination
- `src/main/java/frc/robot/subsystems/superstructure/Superstructure.java:33` — d2-superstructure-class — `public class Superstructure {`
- `src/main/java/frc/robot/subsystems/superstructure/Superstructure.java:210` — d2-state-enum — `public enum ArmState {`
- `src/main/java/frc/robot/subsystems/superstructure/Superstructure.java:263` — d2-state-enum — `public enum ClimbState {`
- `src/main/java/frc/robot/subsystems/superstructure/Superstructure.java:279` — d2-state-enum — `public enum ClawState {`

### D3 Simulation
- `src/main/java/frc/robot/Robot.java:206` — d3-sim-periodic — `@Override`
- `src/main/java/frc/robot/util/hardware/rev/Neo.java:253` — d3-mechanism-sim — `new DCMotorSim(`
- `src/main/java/frc/robot/util/hardware/phoenix/Kraken.java:875` — d3-mechanism-sim — `new DCMotorSim(`

### D5 Logging
- `src/main/java/frc/robot/util/auto/LocalADStarAK.java:32` — d5-process-inputs — `Logger.processInputs("LocalADStarAK", io)`
- `src/main/java/frc/robot/util/auto/LocalADStarAK.java:50` — d5-process-inputs — `Logger.processInputs("LocalADStarAK", io)`
- `src/main/java/frc/robot/RobotContainer.java:143` — d5-smartdashboard — `SmartDashboard.putData(field2d)`
- `src/main/java/frc/robot/subsystems/vision/Vision.java:92` — d5-process-inputs — `Logger.processInputs("SubsystemInputs/Vision/Camera" + i, inputs[i])`
- `src/main/java/frc/robot/subsystems/vision/VisionIO.java:9` — d5-autolog — `@AutoLog`
- `src/main/java/frc/robot/subsystems/superstructure/elevator/ElevatorIO.java:9` — d5-autolog — `@AutoLog`
- `src/main/java/frc/robot/subsystems/superstructure/climb/Climb.java:40` — d5-process-inputs — `Logger.processInputs("SubsystemInputs/Climb", inputs)`
- `src/main/java/frc/robot/subsystems/superstructure/climb/ClimbIO.java:9` — d5-autolog — `@AutoLog`
- `src/main/java/frc/robot/subsystems/superstructure/claw/algae/AlgaeClaw.java:44` — d5-process-inputs — `Logger.processInputs("SubsystemInputs/AlgaeClaw", inputs)`
- `src/main/java/frc/robot/subsystems/superstructure/elevator/Elevator.java:67` — d5-process-inputs — `Logger.processInputs("SubsystemInputs/Elevator", inputs)`
- `src/main/java/frc/robot/subsystems/superstructure/claw/coral/CoralClaw.java:48` — d5-process-inputs — `Logger.processInputs("SubsystemInputs/CoralClaw", inputs)`
- `src/main/java/frc/robot/subsystems/superstructure/claw/ClawIO.java:7` — d5-autolog — `@AutoLog`

### D6 Auto/Path
- `src/main/java/frc/robot/util/auto/PathPlannerStorage.java:277` — d6-autobuilder — `AutoBuilder.buildAuto(autoName)`
- `src/main/java/frc/robot/util/auto/Alignment.java:507` — d6-pathfinding — `AutoBuilder.pathfindToPose(pos.get(), AutoConstants.prepReefConstraint`
- `src/main/java/frc/robot/subsystems/drive/Swerve.java:191` — d6-autobuilder — `AutoBuilder.configure(`

### D7 Vision
- `src/main/java/frc/robot/subsystems/vision/Vision.java:156` — d7-add-vision — `poseEstimator.addVisionMeasurement(inputs[i].robotPose, inputs[i].time`
- `src/main/java/frc/robot/subsystems/vision/Vision.java:154` — d7-stddev — `poseEstimator.setVisionMeasurementStdDevs(VecBuilder.fill(xyStds, xySt`
- `src/main/java/frc/robot/subsystems/drive/Swerve.java:130` — d7-pose-estimator — `new SwerveDrivePoseEstimator(`
