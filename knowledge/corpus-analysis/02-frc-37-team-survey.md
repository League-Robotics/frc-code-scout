Inside Competition Robot Code: FRC

**Inside Competition Robot Code: FRC**

**How top FRC teams structure their software — the patterns that recur across 37 codebases**

*A consolidated teardown of three surveys (37 teams, four languages, six coordination paradigms): from the WPILib command-based baseline, through the IO layer and state graph, to behavior trees, trajectory optimization, and a custom message-passing robotics OS — and the teaching ladder that falls out of them.*

**Contents**

# Bottom line

FRC software has converged on a small number of architectural ideas, and the best teams differ mainly in how aggressively they push decoupling past the boundary WPILib hands them. WPILib gives every team the same starting point — the command-based framework, which splits robot code into subsystems (things the robot has) and commands (things the robot does). That split is real modularity, but it is shallow: a command still talks directly to subsystem methods, and a subsystem still talks directly to motor objects. The interesting work in elite codebases is the extra layers they insert above and below that line.

Three things stand out once the full sample is in view:

- **The IO layer is the ambient default, and it is language-independent.** Popularized by Team 6328 (Mechanical Advantage) through AdvantageKit, it inserts a hardware-abstraction interface between a subsystem and its physical motors and sensors — so a real motor, a simulated motor, and an empty replay motor are interchangeable implementations. What began as a powerhouse signature now appears in mid-tier regional codebases as a matter of course, and shows up reached three different ways in Java, Kotlin, and C++. That triple-language convergence is the strongest evidence in the whole project that the principle is real and the syntax is incidental.

- **Coordination is where teams actually diverge, and there are now six paradigms.** Command composition, the wanted/current finite-state machine, the centralized RobotManager FSM, the state graph with path search, the behavior tree (borrowed wholesale from game AI), and 971's inter-process message bus. The newest and most interesting is the behavior tree: Team 3015 ship a complete unit-tested behavior-tree runtime with a visual editor and run their robot on it.

- **The teams worth imitating treat non-motion concerns as architecture.** Testability (SciBorgs' 14 JUnit suites running real commands in sim; Ranger's 37 test files), kinematic safety (1678's dedicated MotionPlanner), log replay (6328), physics simulation (maple-sim), and operational diagnostics (3061's fault reporter) are elevated to first-class design concerns rather than handled with print statements. These are the rungs above “it works on the field.”

The single most complete decoupling belongs to **Team 971 (Spartan Robotics)**, who abandon command-based entirely for a custom C++/Rust robotics operating system (AOS) where each subsystem is a separate process communicating over typed message channels. Their decoupling is at the process and message boundary, not the class boundary — the cleanest separation of concerns in FRC, at the cost of enormous infrastructure.

**Recommended framing:** modularity in FRC is a ladder, not a binary. A program grows from the command/subsystem split, to the IO layer, to a coordinating state machine or graph, to library/robot separation, and — for the few who need it — to message-passing process isolation. A student who can see those rungs in real code understands FRC architecture better than one who has only memorized the WPILib tutorial.

# The baseline everyone starts from: command-based

Every WPILib team inherits the same two-layer decomposition, so it is the reference point for judging what each team adds.

- **Subsystems** represent physical mechanisms (a drivetrain, an elevator, a claw). Each is a class extending SubsystemBase, owns its hardware, and exposes methods. The scheduler guarantees only one command uses a subsystem at a time, which prevents two pieces of code from fighting over the same motor.

- **Commands** represent actions over time (drive to a pose, raise the elevator, run a scoring sequence). They “require” one or more subsystems and are composed into sequences and parallel groups.

- **RobotContainer** is the wiring root: it constructs the subsystems, binds them to controller buttons, and selects the autonomous routine. WPILib now explicitly recommends subsystems be private fields here rather than global singletons — a deliberate move toward encapsulation.

This is genuine modularity, but the coupling that remains is the whole story of the rest of this document: a command holds a concrete subsystem reference, and a subsystem holds concrete motor objects. Decoupling either of those joints is what separates the surveyed teams from the tutorial.

# The corpus: thirty-seven teams

The teams were gathered across three sweeps. The first five were chosen to span the architectural range and define the canonical reference for each pattern. The next six stressed the edges the first left thin — the explicit FSM camp, non-Java languages, and the practices that sit beside architecture (testing, kinematic safety, diagnostics). The final twenty-six broadened the sample toward regional, non-powerhouse teams specifically to test whether the patterns were elite signatures or genuine convergence. They turned out to be convergence.

Unless noted, every repo is a 2025 “Reefscape” or 2024 “Crescendo” season codebase, cloned and read in full. The master list at the end of this document carries every URL.

## The five-team reference set (Survey I)

| **Team** | **Language** | **Framework** | **Why it****'****s in the set** |
| --- | --- | --- | --- |
| 6328 Mechanical Advantage | Java | WPILib + AdvantageKit | The origin of the IO-layer pattern; graph-based superstructure state machine. The most influential software team in FRC. |
| 254 | Java | WPILib + AdvantageKit | The “library-grade” codebase: generic parameterized subsystem base classes, command factories, A* superstructure solver. Heavily copied. |
| 971 Spartan Robotics | C++ / Rust | Custom (AOS) | The architectural outlier. No command-based; a message-passing robotics OS with process-isolated subsystems. The control-theory reference. |
| 3061 Huskie Robotics | Java | WPILib + AdvantageKit | Publishes a reusable swerve library (3061-lib); openly composes patterns borrowed from 254, 6328, and 3015 (self-check fault reporting). |
| 190 | Java | WPILib + AdvantageKit | Strong idiomatic AdvantageKit code with an unusual multi-robot-variant structure (several complete robots sharing one codebase). |

## The six-team edge set (Survey II)

| **Team** | **Language** | **Paradigm** | **Why it****'****s in this set** |
| --- | --- | --- | --- |
| 2910 | Java | Command-based + explicit FSM | The famous “no-commands” team, now hybrid. The reference implementation of the wanted/current state-machine pattern. |
| 1678 | Java | Command-based + factories | Citrus Circuits. Generic subsystem bases like 254, plus a dedicated MotionPlanner for collision-free arm/elevator motion. |
| 3636 | Kotlin | Command-based + AdvantageKit | The same 6328 IO pattern in Kotlin: type-safe units, object singletons, data-carrying enums. The language-ergonomics case. |
| 4504 | Python | MagicBot (components + FSM) | RobotPy/MagicBot: dependency injection by declaration and framework-level state machines. The Python paradigm. |
| 1155 | Java | Command-based | SciBorgs. The testing case: 14 JUnit suites running commands in sim. Clean Real/Sim/No-op IO naming and a vector-field path planner. |
| 2706 | Java | Command-based + AdvantageKit | PhantomCatz. A strong regional team independently converging on every 6328 pattern, plus the explicit null-object IO (“IONull”). The convergence case. |

## The twenty-six-team breadth set (Survey III)

Chosen to broaden the sample: more languages, more regional teams to test convergence, and several teams picked for one practice each does unusually well.

| **Team** | **Name** | **Lang** | **Framework signals** | **Why it****'****s in this set** |
| --- | --- | --- | --- | --- |
| 3015 | Ranger Robotics | J/K/C++ | AdvantageKit, Choreo, behavior-tree lib | Behavior-tree framework + visual editor; 37 unit-test files; polyglot |
| 581 | Blazing Bulldogs | Java | DogLog, PathPlanner | Single centralized RobotManager FSM; lightweight logging instead of IO layer |
| 4481 | Team Rembrandts | Java | AdvantageKit, Choreo | 32 IO files incl. Real / Replay / IdealSimulated variants; replay-first |
| 3476 | Code Orange | Java | AdvantageKit, Choreo | Repulsor-field planning + superstructure states exposed as auto actions |
| 4099 | The Falcons | Kotlin | AdvantageKit, Choreo | Request-based superstructure in Kotlin — reinforces 3636's ergonomics case |
| 33 | Killer Bees | Java | Phoenix, Old+New Commands | 254-lineage SubsystemManager + state-machine unit tests (2020 “Buzz26”) |
| 2767 | Stryke Force | Java | AdvantageKit replay, thirdcoast | Replay vendordeps + their own thirdcoast library; heavy telemetry |
| 1538 | The Holy Cows | C++ | CowLib, Choreo | Modern C++ command-based with homegrown CowLib + C++ unit tests |
| 2056 | OP Robotics | C++ | OPRLib | Explicit C++ IO layer — IO pattern crossing languages |
| 1114 | Simbotics | Java | AdvantageKit, maple-sim | Physics simulation (maple-sim) — the rung past hand-written SimIO |
| 2877 | LigerBots | Java | YAGSL, maple-sim, Choreo | Library-heavy: YAGSL swerve + physics sim + Redux/Thrifty |
| 4915 | Spartronics | Java | YAGSL, maple-sim | YAGSL + physics sim; a templated mid-tier build |
| 3847 | Spectrum | Java | DogLog, PathPlanner | DogLog logging; clean command-factory style |
| 5712 | Hemlock Gray Matter | Java | AdvantageKit | Widely-forked AdvantageKit swerve template (2024) |
| 5026 | Iron Panthers | Java | AdvantageKit, PathPlanner | IO layer + superstructure coordinator |
| 1257 | Parallel Universe | Java | AdvantageKit, PathPlanner | IO layer; Phoenix5+6 mixed bus |
| 1741 | Red Alert | Java | AdvantageKit, Choreo | Logging-dense (98 @AutoLog) AdvantageKit build |
| 9015 | Questionable Eng. | Java | AdvantageKit, PathPlanner | Clean IO-layer regional build |
| 6995 | NOMAD | Java/Python | Choreo, PathPlanner | Choreo-heavy autonomous; PhotonVision |
| 868 | TechHOUNDS | Java | Choreo, URCL | Library-based build; URCL motor logging |
| 95 | The Grasshoppers | Java | Choreo, PathPlanner | Choreo + PathPlanner regional convergence |
| 2412 | Robototes | Java | Choreo, PathPlanner | Both planners; PhotonVision |
| 3128 | Aluminum Narwhals | Java/Python | PathPlanner | Python tooling alongside Java robot code |
| 4607 | C.I.S Robotics | Java | Choreo, PathPlanner | Compact command-based reference |
| 7028 | Binary Battalion | Java | PathPlanner, grapple | LaserCAN sensors; command-based |
| 5190 | Green Hope Falcons | Java | PathPlanner | Compact 2025 build |

# Architecture by repository

The deep dives below are grouped by the idea each team is the clearest example of. Not every one of the 37 gets a teardown — the regional convergence teams are covered collectively under “Convergence” — but every architectural move in the pattern catalog traces back to one of these.

## 6328 Mechanical Advantage — the IO layer, defined

**Directory shape.** A flat subsystems/ package, each subsystem in its own folder, plus a small set of root classes: Robot, RobotContainer, RobotState, Constants, FieldConstants. Mechanisms that move together (elevator + dispenser) are grouped under a superstructure/ parent.

**The defining move.** Each subsystem is split into three or four files. For the elevator:

elevator/

  ElevatorIO.java          // interface: the contract

  ElevatorIOTalonFX.java   // real hardware implementation

  ElevatorIOSim.java       // physics-sim implementation

  Elevator.java            // subsystem logic, hardware-agnostic

The ElevatorIO interface declares an updateInputs(inputs) method plus output methods like runPosition(positionRad, feedforward). The inputs are a plain data record annotated @AutoLog, which AdvantageKit serializes to the log every cycle. The subsystem class never names a motor type; it holds an ElevatorIO reference and reads from a logged inputs object.

**Why this is the pattern that won.** Three payoffs fall out of one interface:

- **Simulation is free.** Swap ElevatorIOTalonFX for ElevatorIOSim by changing one constant; all subsystem logic runs unchanged on a laptop.

- **Log replay.** Because every hardware input crosses the IO boundary and is logged, an entire match can be replayed through the real code afterward — feeding logged sensor values back in and watching what the code decided. This is AdvantageKit's headline feature and the reason inputs are isolated so strictly.

- **Hardware swaps are local.** Moving from one motor controller to another, or supporting a practice robot with different electronics, touches only an IO file.

**Coordination layer.** Above the subsystems sits Superstructure, which 6328 models as a literal directed graph of states using the JGraphT library. States (STOW, CORAL_INTAKE, L4_CORAL…) are graph vertices; the commands that move between them are edges. To reach a target state the code runs a graph search and executes the edge commands along the path. The transition logic is data (a graph), not a tangle of if-statements.

**Constraint worth teaching.** The replay guarantee forces the entire robot program to be single-threaded and deterministic. It is a clean example of an architectural invariant (determinism) dictating a coding rule (no threads, no un-isolated randomness).

## 254 — the same idea, abstracted one level higher

**Directory shape.** Code is split into com.team254.lib.* (reusable, season-independent) and com.team254.frc2025.* (this year's robot). The library half is a deliberate, maintained asset — drivers, a swerve stack, a vendored copy of PathPlanner, and generic subsystem bases.

**The defining move.** Where 6328 writes a hand-rolled IO interface per subsystem, 254 generalizes it into a single parameterized base class:

class ServoMotorSubsystem<

      T extends MotorInputsAutoLogged,

      U extends MotorIO>

    extends SubsystemBase { ... }

A concrete mechanism becomes a thin subclass plus a ServoMotorSubsystemConfig object holding gains, gear ratios, and limits. There is one MotorIO interface and one TalonFXIO / SimTalonFXIO pair shared across every position-controlled mechanism. This is the IO layer plus the template-method / generic-base pattern: maximum code reuse, at the cost of a steeper learning curve and heavier generics.

**Command factories.** Instead of a folder full of command classes, 254 uses *Factory classes whose static methods return configured Command objects assembled from WPILib's composition helpers. Action definitions live in one readable place and are composed functionally.

**Coordination layer.** Like 6328, 254 treats the superstructure as a graph problem — but names it outright with an AStarSolver and a SuperstructureStateMachine, alongside a CoralStateTracker for game-piece state. Two of the strongest teams in FRC independently arriving at “superstructure = shortest path through a state graph” is the clearest convergence in the survey.

**RobotState.** A dedicated RobotState class owns the robot's pose estimate and game-piece knowledge, fed by odometry and vision through time-interpolating buffers — a pattern both 254 and 6328 share and both name identically.

## 971 Spartan Robotics — decoupling at the process boundary

**Directory shape.** A multi-year monorepo. aos/ is a general robotics middleware (“Autonomous Operating System”). frc971/control_loops/ is a reusable controls library. Each season gets its own top-level folder (y2023/, y2024/, y2025/…). Built with Bazel, not GradleRIO.

**The defining move.** 971 does not use subsystems-and-commands at all. A robot is a set of independent processes — wpilib_interface, superstructure, joystick_reader, localizer, autonomous — that communicate only by passing typed messages over AOS channels. There are no shared objects between them; the coupling is a published message contract built on a single template:

template <class GoalType, class PositionType,

          class StatusType, class OutputType>

class ControlLoop { ... };

- **Goal** — what we want (e.g. an ElevatorGoal enum: SCORE_L1…SCORE_L4, CLIMB).

- **Position** — sensor readings coming in from hardware.

- **Output** — motor commands going out to hardware.

- **Status** — what the loop is doing, published for everyone else to read.

These are defined in .fbs (FlatBuffer) schema files — a strongly-typed, versioned, language-neutral contract, the same discipline a professional distributed system uses.

**What this buys, and what it costs.** Because processes are isolated, a crash in one subsystem cannot corrupt another, components can be tested in total isolation by replaying recorded message streams, and the controls code is plain math with no hardware entanglement — which is why control_loops/ can contain genuine control theory (DARE and DLQR solvers, continuous-to-discrete conversion, state-feedback and Kalman-style observers) rare elsewhere in FRC. The cost is a large custom infrastructure realistically out of reach for a team without dedicated software mentors.

## 3061 Huskie Robotics — composition and self-diagnosis

**Directory shape.** A frc/lib/ vs frc/robot/ split mirroring 254's. The revealing detail is inside the lib folder: packages named team3061, team254, team6328, and team3015. Huskie openly vendors and attributes patterns from other teams — a real picture of how FRC architecture actually propagates.

**The pattern worth stealing.** From Team 3015 they incorporate a self-check / fault-reporting framework: a singleton FaultReporter to which each hardware device registers, that polls for faults on a timer and publishes per-subsystem health (OK / WARNING / ERROR) to the dashboard, plus on-demand “system check” commands that exercise a mechanism and report what failed. This is an operational-reliability concern most teams handle by ad-hoc print statements; 3061 treats hardware health as a first-class subsystem of its own. They also publish their drivetrain as a reusable, hardware-abstracted swerve library (3061-lib).

## 190 — multi-robot variants as a first-class concern

**Directory shape.** Standard AdvantageKit IO-layer subsystems, with one unusual organizing principle: the subsystems/ folder contains a shared/ package and several complete robot variants side by side — v0_Whiplash, v1_StackUp, v2_Redundancy, v3_Poot. Common mechanisms live in shared/; variant-specific superstructures and manipulators live in their own version folders.

**Why it matters.** Most teams represent “practice bot vs competition bot vs next iteration” with a runtime constant or a branch. 190 represents it in the package structure, so multiple robot configurations coexist and share code through the shared/ layer. It is the IO layer's hardware-swap benefit scaled up from “swap a motor” to “swap an entire robot,” and a clean example of using directory structure itself as an architectural tool.

## 2910 Jack in the Bot — the wanted/current state machine

**The reversal worth noting.** 2910 is the team most cited for running finite state machines instead of the command scheduler. Their 2025 code is a hybrid: subsystems do extend SubsystemBase and use an IO layer (ShoulderIO / ShoulderIOTalonFX), but behavior is driven by explicit state machines rather than scheduled commands. “FSM vs command-based” is a false binary; the strongest version uses command-based for resource arbitration and an FSM for decision logic.

**The pattern, stated precisely.** Every subsystem and the superstructure follow the same two-enum shape:

enum WantedState  { IDLE, HOME, INTAKE, SCORE_L4, ... }   // requested

enum SystemState  { IDLING, HOMING_WRIST, ... }           // actual

 

private SystemState handleStateTransitions() {

    switch (wantedState) {

        case HOME: ... return SystemState.HOMING_SHOULDER;

        ...

    }

}

// each periodic(): currentState = handleStateTransitions(); applyStates();

**Why this decouples cleanly.** A caller sets wantedState and walks away. It never knows what sequence of physical steps the subsystem must run to honor the request, and it cannot put the mechanism into an illegal configuration because only the transition function writes SystemState. The superstructure does the same at the next level up. It is the same intent-vs-execution split that 971 gets from its Goal/Status messages, achieved here inside one process with two enums.

## 1678 Citrus Circuits — kinematic safety as its own layer

**Familiar bones.** 1678 (now Java, having moved off their historical C/C++) looks structurally like 254: a frc/lib/bases package of generic subsystem base classes, a shared frc/lib/io with MotorIO / MotorIOTalonFX / MotorIOTalonFXSim, and beam-break and vision IO behind interfaces with sim variants.

**The distinctive layer.** Where most teams fold collision-avoidance into their state graph, 1678 pull it out into a separate MotionPlanner. The elevator and pivot can physically crash into each other, so moving between two safe poses is not a straight line through configuration space. The MotionPlanner owns that geometry — including a tellingly-named UnsafePivotAndElevatorSynchronousToPositionMotionMagic command that coordinates the two axes so they arrive together without colliding. Separating “where we want to be” (the superstructure's state) from “what path through space is safe to get there” (the planner) is a cleaner decomposition than burying both in one state machine.

## 3636 — the same patterns, with Kotlin doing the safety work

**Identical architecture, different language.** 3636 use AdvantageKit's IO pattern exactly as 6328 defines it: an ElevatorIO interface, ElevatorIOReal / ElevatorIOSim implementations, an @Logged inputs class, and a when (Robot.model) expression to pick the implementation. What changes is what the language enforces for free.

- **Type-safe units.** Inputs are declared as var leftHeight = 0.meters and IO methods take Distance, Voltage, AngularVelocity. A height and a voltage are different types; mixing them is a compile error, not a runtime mystery. This eliminates an entire category of FRC bug (unit confusion) at the type level.

- **Singletons for free.** A subsystem is declared object Elevator : Subsystem — Kotlin's object keyword makes it a guaranteed singleton with no boilerplate, the thing Java teams hand-roll with private constructors and getInstance().

- **Data-carrying enums.** Setpoints are an enum class Position(val height: Distance) — each state literally carries its target as typed data, the same idea as 6328's state-data records but built into the enum.

3636 (joined by 4099's Request-based superstructure in Survey III) is the proof that the architecture is language-independent and that a more expressive language pays for itself in eliminated bug classes. Showing the same elevator IO in Java and Kotlin makes visible which lines are the design and which are Java ceremony.

## 4504 — Python's MagicBot: the framework provides the decoupling

RobotPy lets teams write robot code in Python; MagicBot is its opinionated framework, a deliberate alternative to command-based. 4504's code is a clean example of its two signature ideas.

- **Dependency injection by declaration.** In robot.py you declare components as typed class attributes — launcher: Launcher, vision: Vision — and MagicBot instantiates them, resolves their interdependencies, and injects them automatically. No RobotContainer manually wiring objects together; the framework owns construction. Same dependency-inversion goal the Java teams reach with IO interfaces, handled by the framework instead of by hand.

- **Component vs controller split, with a built-in FSM.** Each mechanism is two files: a dumb launcher.py (just hardware and setters) and a launcherController.py subclassing MagicBot's StateMachine with @state-decorated methods and next_state() transitions. This is 2910's wanted/current pattern, except the state-machine machinery is provided by the framework rather than written out as switch statements.

## 1155 SciBorgs — testability as the design goal

**The IO pattern, clearly named.** SciBorgs use descriptive implementation names that read better than the usual IOTalonFX convention: ElevatorIO interface with RealElevator, SimElevator, and NoElevator implementations. NoElevator is the null-object pattern — a do-nothing implementation so the robot can run with a mechanism disabled or absent. Subsystems are constructed through a static Elevator.create() factory that returns the right implementation for the current environment.

**The thing almost no one else does.** They ship a src/test/java tree with 14 JUnit 5 suites — ElevatorTest, ArmTest, SwerveTest, AlignTest, and more — that construct sim-backed subsystems, run actual commands to completion in simulation (runToCompletion(...)), and assertEquals on the resulting state. Robot code verified on CI before it ever reaches a robot is rare in FRC, and it is the IO layer's ultimate payoff: because create() can return a SimElevator, the whole subsystem is testable without hardware. (Ranger Robotics' 37 test files in Survey III more than double this — the dividend is being collected at scale.)

## 2706 PhantomCatz — the convergence case

**Why include a regional team among powerhouses.** Because 2706 is the control group. Without copying any single team wholesale, they independently arrive at the entire 6328 toolkit: per-subsystem IO interfaces, a CatzSuperstructure singleton coordinating mechanisms, AdvantageKit logging throughout, and PathPlanner-based autonomous. When strong-but-not-elite teams reinvent the same structure on their own, that is evidence the pattern is a genuine attractor, not a fashion propagated by one famous team.

**Their one refinement.** They add a fourth IO implementation, ElevatorIONull — the null-object pattern made explicit alongside Real and Sim, so a subsystem with disconnected hardware degrades to a safe no-op instead of crashing. They also keep a TeleopPosSelector holding the driver's current scoring intent, decoupling UI state from robot state.

## 3015 Ranger Robotics — the behavior tree as a coordination paradigm

3015 is the standout of the breadth survey. Where every other team coordinates mechanisms with commands, a state machine, or a state graph, 3015 built a behavior-tree runtime — the coordination model from game AI and robotics middleware — and run their robot on it. The Kotlin source under lib/behaviorTree/ has the textbook node taxonomy:

- **Leaf nodes:** CommandRunner (run a WPILib command as a tree leaf), Wait, SetVariable, ClearVariable — the actions.

- **Decorator nodes:** ConditionDecorator, InfiniteLoop, Loop, LoopUntilSuccess, ForceFailure, IsVarSet — control-flow wrappers that modify a child's result.

- **A blackboard:** shared named variables that nodes read and write — the tree's working memory.

Each node returns Success / Failure / Running every tick, exactly as a behavior tree should, and the whole library is unit-tested. 3015 even ship a separate visual behavior_tree_editor app to author the trees. A behavior tree is the natural answer to the question a state machine eventually raises — “what happens when the transitions themselves get complicated?” — and it transfers directly to robotics and games beyond FRC.

## 581 Blazing Bulldogs — the centralized RobotManager FSM

Where the wanted/current pattern (2910, MagicBot) distributes the state machine — one per subsystem plus a superstructure on top — 581 demonstrate the opposite pole: a single RobotManager holds the entire robot's state machine and drives a set of deliberately “dumb” subsystems that only expose setters. Mechanism behavior lives in one place; subsystems own no decision logic. Their LifecycleSubsystemManager and per-subsystem *State enums make the scheme explicit. This is a genuine architectural fork: distributed FSMs localize each mechanism's logic but require careful coordination; the centralized FSM makes whole-robot states trivial to reason about but concentrates all complexity in one file. (581 also vendor DogLog in-tree as their lightweight-logging stance.)

## 2056 OP Robotics & 1538 The Holy Cows — the IO layer in C++

971 decoupled hardware in C++ through an inter-process message contract. This set shows the other way: OP Robotics (2056) keep an explicit IO/ directory of hardware-interface classes inside a single process — the direct C++ analog of the AdvantageKit Java pattern. The Holy Cows (1538) take a parallel route: a homegrown CowLib with NetworkTable serializers and, notably, C++ unit tests under src/test/cpp. Dependency inversion reached independently in Java, Kotlin, and C++ — and in C++ by two different mechanisms — is the cleanest possible demonstration that the principle is language-independent and the syntax is not.

## Convergence and the simulation dividend across the breadth set

The regional teams of Survey III are most valuable in aggregate. Four things the earlier surveys called signatures of strong teams are now near-universal across this broader, less-elite sample:

- **The per-subsystem IO layer is the default.** Ten of the Java/Kotlin teams here carry explicit *IO interfaces with Real/Sim implementations; Rembrandts (4481) alone has 32, including first-class ReplayVisionIO and IdealSimulatedSwerveModuleIO variants — treating deterministic re-simulation of a real match as a primary workflow.

- **Command-based is the substrate; the FSM rides on top.** Every Java/Kotlin team uses the WPILib command scheduler for resource arbitration, then layers decision logic above it — confirming “scheduler for arbitration, state machine for intent” as settled consensus.

- **The superstructure coordinator is standard.** A single object that fans a requested robot-wide state out to subsystems appears in 33, 3476, 4099, 5026 and others. Code Orange (3476) even expose superstructure states as autonomous actions (SetSuperstructureState, WaitForSuperstructureState), marrying 254's action-based autonomous to the wanted/current pattern.

- **Vision is assumed.** PhotonVision pose estimation appears in 17 of 26 breadth-set repos, almost always behind an IO interface with a replay/sim variant. AprilTag localization is no longer optional infrastructure.

Two refinements deepen the IO layer's payoff. Physics simulation — Simbotics (1114), LigerBots (2877), and Spartronics (4915) adopt maple-sim, which simulates the actual dynamics of swerve drivetrains and game-piece interaction — is the rung above the hand-written SimIO of the earlier surveys, where the simulation can surprise you rather than merely echo a setpoint. And lightweight logging (DogLog, in 581 and Spectrum 3847) is the counter-movement to AdvantageKit's IO-layer ceremony: telemetry in a one-line call, no required IO interfaces, at the cost of replay fidelity. The logging spectrum now runs from bare println → DogLog/Epilogue → full AdvantageKit IO + replay, and the choice is a real engineering trade-off.

# The pattern catalog

Setting all 37 codebases side by side, the recurring architecture reduces to a handful of named patterns. The first several are near-universal among serious teams; the coordination choices are where teams diverge.

## 1. The IO layer (hardware abstraction)

Insert an interface between a subsystem and its physical devices; provide real, simulated, and (for AdvantageKit) replay implementations. Defined by 6328, formalized as a generic base class in 254, reached in Kotlin by 3636/4099, in C++ by 2056/1538, and replaced by a message contract in 971. The closest thing FRC has to a required pattern for serious software.

## 2. The null object and the test — the IO layer's deferred dividend

A Sim implementation makes a subsystem runnable without hardware; a No-op / Null implementation (SciBorgs' NoElevator, 2706's ElevatorIONull) makes it runnable with hardware disabled; together they make the subsystem unit-testable on CI. 1155 cash this in with 14 JUnit suites, 3015 with 37 test files. This is the difference between an IO layer used for simulation convenience and one used for genuine software verification.

## 3. Library / robot separation

Split reusable, season-independent infrastructure from this-year's-robot code, by package (lib vs frc20XX) or by directory. Explicit in 254, 3061, and 971; partial in 190 via shared/. Lets a team carry hard-won swerve, vision, and controls code across seasons instead of rewriting it every January.

## 4. A separate world-model (RobotState)

Centralize the robot's belief about the field — pose estimate, game-piece state — in one class fed by odometry and vision, rather than scattering it across subsystems. Named identically in 254 and 6328; present as the localizer process in 971. Decouples “what we know” from “what we control.”

## 5. Wanted-state / current-state (intent vs execution)

Hold two states per mechanism — the one requested and the one actually in effect — with a transition function the only thing allowed to move between them. Explicit in 2910 (hand-written) and 4504 (framework-provided via MagicBot). The in-process equivalent of 971's Goal/Status split, and the most robust way to stop callers from driving a mechanism into an illegal configuration.

## 6. Kinematic safety as a separate layer

When two mechanisms share space and can collide, separate “which pose we want” from “what trajectory through configuration space is safe.” 1678's MotionPlanner is the explicit case; on-the-fly field path planners (SciBorgs' RepulsorFieldPlanner, and in force across 3476, 4481, 3015, 6995) are the drivetrain analog. The repulsor / potential-field approach — treat the goal as an attractor and obstacles as repulsors, follow the resulting vector field — has become a stock drivetrain capability, not a flourish.

## 7. The three path concerns, pulled apart

Beginner code mashes pathing into one blob; the corpus separates three jobs. PathPlanner (in 20 of the breadth-set 26) handles human-authored, waypoint-style paths. Choreo (14 of 26) — a time-optimal trajectory generator that solves for the fastest physically-feasible path given the robot's real torque and traction limits — handles machine-optimized trajectories where every tenth of a second counts, frequently alongside PathPlanner rather than replacing it. Repulsor-field planning handles reactive obstacle avoidance. “Where we want to go,” “what is the fastest legal path,” and “how we follow it” are three distinct concerns.

## 8. Operational reliability as architecture

The most mature teams treat reliability as a designed-in concern, not a debugging afterthought: AdvantageKit's whole-match log replay (6328 and everyone using it), 3061/3015's self-check fault reporting, and 971's process isolation and message logging. All three are different answers to the same question — “when the robot misbehaves on the field, how do we know why?”

# The coordination spectrum

How teams coordinate multiple mechanisms into coherent robot-level behavior is the richest point of divergence. Across all three surveys it now spans six paradigms, plus an orthogonal choice between centralized and distributed state. These are not competitors to pick among once and for all — they are rungs and forks. A program grows from command composition, to a distributed or centralized FSM, to a state graph or behavior tree when transitions outgrow a switch statement, with message passing reserved for when true process isolation is needed.

| **Paradigm** | **Exemplars** | **What it is best at** |
| --- | --- | --- |
| Command composition | 254, 1155, 3061, 190 | Resource arbitration; composing reusable command objects |
| Wanted/current FSM (distributed) | 2910, 33, 4099, 4504 | Localizing each mechanism's intent-vs-execution split |
| Centralized RobotManager FSM | 581 | Reasoning about whole-robot states in one place |
| State graph (search over states) | 6328, 254 | Complex transition logic; pathfinding through legal states |
| Behavior tree | 3015 | Deeply nested, reactive decision logic borrowed from game AI |
| Message passing (inter-process) | 971 | Process isolation; language-agnostic contracts |

# The teams, placed

Every team that got a teardown, sorted by where it puts its primary decoupling boundary, how it coordinates, and the one concern it elevates to architecture.

| **Team** | **Lang** | **Hardware decoupling** | **Coordination** | **Signature concern** |
| --- | --- | --- | --- | --- |
| 6328 | Java | IO layer (defined it) | State graph (JGraphT) | Log replay |
| 254 | Java | Generic ServoMotorSubsystem | A* over state graph | Library-grade reuse |
| 971 | C++/Rust | Message contract (.fbs) | Goal messages between processes | Process isolation |
| 3061 | Java | IO layer | Command composition | Self-check / fault reporting |
| 190 | Java | IO layer | Per-variant superstructure | Multi-robot variants |
| 2910 | Java | IO layer | Wanted/current FSM (every level) | Intent vs execution |
| 1678 | Java | Generic bases + IO | State machine + MotionPlanner | Kinematic safety |
| 3636 | Kotlin | IO layer (typed units) | State enums + commands | Compile-time unit safety |
| 4504 | Python | Component/controller split | MagicBot StateMachine (framework) | Dependency injection |
| 1155 | Java | IO layer (Real/Sim/No) | Commands + command classes | Unit testing on CI |
| 2706 | Java | IO layer (Real/Sim/Null) | Superstructure singleton | Convergence / null object |
| 3015 | J/K/C++ | IO layer | Behavior tree | Behavior-tree runtime + editor; testing |
| 581 | Java | Dumb-subsystem setters | Centralized RobotManager FSM | One-place state; lightweight logging |
| 4481 | Java | IO (Real/Replay/IdealSim) | Superstructure + commands | Replay-first IO; kinematic planning |
| 3476 | Java | IO layer | Superstructure-as-action FSM | Repulsor-field path planning |
| 4099 | Kotlin | IO layer | Request-based superstructure | Kotlin ergonomics (data requests) |
| 33 | Java | lib/Subsystem + RobotState | State-machine classes | 254-lineage FSM + state-machine tests |
| 2767 | Java | IO layer (replay vendordeps) | Commands + thirdcoast lib | Deterministic replay; telemetry |
| 1538 | C++ | CowLib + NT serializers | Command-based | Modern C++ + C++ unit tests |
| 2056 | C++ | IO/ directory | Command-based | IO layer in C++ (single-process) |
| 1114 | Java | IO layer | Commands | maple-sim physics simulation |
| 2877 | Java | YAGSL + IO | Commands | Library-heavy bring-up; physics sim |
| 3847 | Java | Command factories | Commands | DogLog lightweight logging |
| 5712 | Java | IO layer | Commands | Forkable AdvantageKit swerve template |
| 5026 / 1257 / 1741 / 9015 | Java | IO layer | Superstructure / commands | AdvantageKit regional convergence |

**The one-line summary of all three surveys:** every serious team decouples the subsystem from its hardware (IO layer or message contract), then differentiates on coordination (command composition → state machine → state graph → behavior tree → message bus) and on which non-motion concern it elevates to architecture (replay, testing, safety, diagnostics, reuse, variants).

# Tooling adoption across the breadth set

Convergence is easier to see in counts than in prose. Adoption across the twenty-six-team Survey III corpus (the counts are signal for where to look, not a benchmark — every claim was confirmed by reading source):

| **Tool / layer** | **Teams (of 26)** | **Reading** |
| --- | --- | --- |
| Command-based (WPILib) | 26 (J/K/C++) | Universal substrate |
| PathPlanner | 20 | Default path-following |
| PhotonVision | 17 | Vision/AprilTag localization assumed |
| Choreo (trajectory optimization) | 14 | Now a distinct layer above PathPlanner |
| Per-subsystem IO layer | 10 J/K + 2056 (C++) | The dependency-inversion default |
| AdvantageKit + log replay | ~11 | Power-user logging; spreading to regionals |
| YAGSL (off-the-shelf swerve) | 2877, 4915 (+) | Templated swerve for faster bring-up |
| maple-sim (physics simulation) | 1114, 2877, 4915 | Dynamics-level simulation, past SimIO |
| DogLog (lightweight logging) | 581, 3847 | Low-ceremony alternative to AdvantageKit |
| Behavior-tree framework | 3015 | Sole instance — the new frontier |

# Implications for a teaching ladder

The architecture maps onto a progression that can be taught in order — each rung a concrete refactor a student performs on their own working code, motivated by a problem they have just felt. The mechanisms change every game; the architecture does not. A curriculum that teaches these rungs is teaching software engineering — dependency inversion, separation of concerns, contract-based design, reuse, verification — using a robot as the motivating problem. That is a stronger and more transferable claim than “we teach kids to code robots.”

### Rung 1 — Subsystem / command split

The WPILib baseline. A student writes a subsystem with motor objects and a command that calls its methods. Immediate working robot; the modularity is the scheduler stopping two commands from fighting over a motor.

### Rung 2 — Extract the IO interface (then the null object, then the test)

The teachable moment is “I want to test this without the robot.” Pull the motor calls behind an ElevatorIO interface, write an ElevatorIOSim, and the same subsystem runs on a laptop. The next two moves are a no-op ElevatorIONull (run with the mechanism unplugged) and a JUnit test that drives the sim subsystem and asserts on the result. The test is where the IO layer stops being a simulation trick and becomes software engineering. SciBorgs is the worked example. This is the single highest-value architectural lesson in modern FRC and the entry point to AdvantageKit.

### Rung 3 — Separate the world-model and the coordinator

When two mechanisms must move together safely, hard-coded if-statements break down. Introduce a RobotState for beliefs and a superstructure for coordination — and teach wanted/current before the state graph. 2910's two-enum machine teaches the core idea (callers request intent, a transition function owns execution) without the graph-search machinery. It is the right first state machine; 6328's JGraphT graph is the optimization for when transitions get complex.

### Rung 4 — The behavior tree, when transitions outgrow a switch

3015's leaf/decorator/blackboard library is the worked example, and it transfers directly to robotics and game AI outside FRC. Pair it with the state graph as the two ways to handle decision logic too tangled for a switch statement.

### Rung 5 — Library / robot separation

Once a second season starts, the pain of rewriting swerve motivates pulling reusable code into a lib package. Reuse becomes a structural decision, not a copy-paste.

### Rung 6 (capstone) — Message-passing / process isolation

971's architecture is the stretch goal: separate processes, typed message contracts, replayable channels. Almost no team needs it, but understanding it is what turns “FRC programmer” into “understands distributed robotics systems.”

### Three lateral lessons

- **Use a second language to separate principle from ceremony.** Showing the same elevator IO in Java (6328) and Kotlin (3636) makes visible which lines are the design and which are Java boilerplate — type safety, singletons, data-carrying enums, with a robot as the motivating example.

- **Separate the three path concerns explicitly.** Human-authored path (PathPlanner), machine-optimized trajectory (Choreo), reactive obstacle avoidance (repulsor field). A beginner conflates them; the corpus pulls them apart, and so should a curriculum.

- **Frame logging and simulation as trade-offs, not defaults.** Have students feel the AdvantageKit IO-layer ceremony, then show DogLog doing most of the value in one line, and discuss what replay fidelity is worth. Likewise, move simulation from setpoint-echo (hand-written SimIO) to real dynamics (maple-sim) — the difference between “the code runs without a robot” and “the simulation could surprise me,” which is when simulation starts catching real bugs.

# Caveats and things to verify

- **Public ≠ internal.** 6328 and 254 publish daily mirrors of internal repos; what is public is real competition code, but documentation and commit history may be thinned. Treat the structure as authoritative and the comments as incomplete.

- **Season snapshots.** The surveys span 2024–2025 (with two historical exceptions noted below). The IO-layer and state-graph patterns are stable across recent years, but specific class names shift season to season. Cite “2910's 2025 code,” not “2910's approach” in the abstract — 2910 in particular has changed paradigm emphasis across seasons.

- **Two historical references.** Team 33's “Buzz26” is a 2020 codebase — a clean 254-lineage FSM + RobotState exemplar with state-machine unit tests, but cite it as historical, not a current build. 1678's well-known C/C++ work is in older archived repos; their public 2025 code is Java, so pull a pre-2024 1678 (or 971) repo if the C++ comparison matters.

- **971 build complexity.** Their architecture is genuinely excellent and genuinely hard to adopt. Hold it up as an aspiration and a teaching object, not a template to copy without dedicated software mentorship.

- **MagicBot example is a 2024, mid-tier team.** 4504 cleanly demonstrates the framework (DI + framework FSM), but it is not an elite codebase; do not read it as a performance benchmark.

- **Selection bias toward strong teams.** Especially in the first two surveys, these are not the median FRC team, whose code is closer to the unmodified WPILib tutorial. The point of the set is to show the ceiling and the ladder up to it. The Survey III breadth set was added specifically to test how far down the convergence reaches — and it reaches far.

- **Counts are signal, not proof.** Grep-based marker counts located the patterns; every claim was confirmed by reading source. Several repos (Rembrandts 4481, TechHOUNDS 868, Grasshoppers 95) use non-standard Gradle layouts, so flat file counts understate them.

- **Some teams keep robot code private.** 1690 Orbit, 1574 MisCar, 1323 MadTown, 118 Robonauts, and 195 CyberKnights publish only tooling (scouting, dashboards) or use private GitLab; their robot code could not be included.

# Master repository list

All thirty-seven repositories analyzed across the three surveys, cloned to the local corpus (final clone June 2026). Public student/team repositories cited for structural analysis and teaching reference; study for technique, not for copying. “Survey” marks which sweep each entered in.

| **Team** | **Repository (team / season)** | **Lang** | **Survey** | **URL** |
| --- | --- | --- | --- | --- |
| 6328 | Mechanical-Advantage / RobotCode2025Public | Java | I | github.com/Mechanical-Advantage/RobotCode2025Public |
| 254 | Team254 / FRC-2025-Public | Java | I | github.com/Team254/FRC-2025-Public |
| 971 | frc971 / 971-Robot-Code | C++/Rust | I | github.com/frc971/971-Robot-Code |
| 3061 | HuskieRobotics / frc-software-2025 | Java | I | github.com/HuskieRobotics/frc-software-2025 |
| 190 | Team-190 / 2k25-Robot-Code | Java | I | github.com/Team-190/2k25-Robot-Code |
| 2910 | FRCTeam2910 / 2025CompetitionRobot-Public | Java | II | github.com/FRCTeam2910/2025CompetitionRobot-Public |
| 1678 | frc1678 / C2025-Public | Java | II | github.com/frc1678/C2025-Public |
| 3636 | FRC3636 / frc-2025 | Kotlin | II | github.com/FRC3636/frc-2025 |
| 4504 | BC-Robotics-4504 / 2024-Season | Python | II | github.com/BC-Robotics-4504/2024-Season |
| 1155 | SciBorgs / Reefscape-2025 | Java | II | github.com/SciBorgs/Reefscape-2025 |
| 2706 | PhantomCatz / RobotCode2025-Reefscape | Java | II | github.com/PhantomCatz/RobotCode2025-Reefscape |
| 3015 | Ranger Robotics — 2024 Public | J/K/C++ | III | github.com/3015RangerRobotics/2024Public |
| 581 | Blazing Bulldogs — 2024 Crescendo | Java | III | github.com/team581/frc-2024-crescendo-gamma |
| 4481 | Team Rembrandts — 2025 (public) | Java | III | github.com/FRC-4481-Team-Rembrandts/2025-robot-public |
| 3476 | Code Orange — FRC-2025 | Java | III | github.com/FRC3476/FRC-2025 |
| 4099 | The Falcons — Reefscape-2025 | Kotlin | III | github.com/team4099/Reefscape-2025 |
| 33 | Killer Bees — Buzz26 (frc2020) | Java | III | github.com/FRC33/Buzz26 |
| 2767 | Stryke Force — reefscape | Java | III | github.com/strykeforce/reefscape |
| 1538 | The Holy Cows — 1538_2025 | C++ | III | github.com/TheHolyCows/1538_2025 |
| 2056 | OP Robotics — PublicCodeBank | C++ | III | github.com/Team2056/PublicCodeBank |
| 1114 | Simbotics — 2025-Simbot-CMD-Public | Java | III | github.com/Simbotics/2025-Simbot-CMD-Public |
| 2877 | LigerBots — ReefScape2025 | Java | III | github.com/ligerbots/ReefScape2025 |
| 4915 | Spartronics — 2025-Reefscape | Java | III | github.com/Spartronics4915/2025-Reefscape |
| 3847 | Spectrum — 2025-Spectrum | Java | III | github.com/Spectrum3847/2025-Spectrum |
| 5712 | Hemlock Gray Matter — 2024-Robot | Java | III | github.com/Hemlock5712/2024-Robot |
| 5026 | Iron Panthers — FRC-2025 | Java | III | github.com/Iron-Panthers/FRC-2025 |
| 1257 | Parallel Universe — 2025-Robot | Java | III | github.com/FRC1257/2025-Robot |
| 1741 | Red Alert — RA25_RobotCode | Java | III | github.com/RAR1741/RA25_RobotCode |
| 9015 | Questionable Engineering — Reefscape | Java | III | github.com/FRC9015/Reefscape |
| 6995 | NOMAD — Robot-2025 | Java/Python | III | github.com/frc6995/Robot-2025 |
| 868 | TechHOUNDS — 2025-Robot | Java | III | github.com/frc868/2025-Robot |
| 95 | The Grasshoppers — FRC2025 | Java | III | github.com/first95/FRC2025 |
| 2412 | Robototes — Reefscape2025 | Java | III | github.com/robototes/Reefscape2025 |
| 3128 | Aluminum Narwhals — 3128-robot-2025 | Java/Python | III | github.com/team3128/3128-robot-2025 |
| 4607 | C.I.S Robotics — Comp-Bot-2025 | Java | III | github.com/FRC4607/Comp-Bot-2025 |
| 7028 | Binary Battalion — frc-7028-2025 | Java | III | github.com/STMARobotics/frc-7028-2025 |
| 5190 | Green Hope Falcons — 2025CompetitionSeason | Java | III | github.com/FRC5190/2025CompetitionSeason |

**Discovery method.** Teams were drawn from the FRC “Open Alliance” community on Chief Delphi, GitHub topic and keyword search, and known powerhouse and regional orgs; each repository was verified public and currently existing via git before cloning. Teams whose only public repositories are tooling rather than robot code were excluded.

# Sources

- All 37 repositories above (cloned to the local corpus, 2025–2026).

- Mechanical-Advantage / AdvantageKit and “Setting the Foundation” IO-layer rationale — github.com/Mechanical-Advantage/AdvantageKit; littletonrobotics.org

- WPILib frc-docs, “Structuring a Command-Based Project” — github.com/wpilibsuite/frc-docs

- MagicBot framework documentation — robotpy.readthedocs.io

- Choreo trajectory optimizer — sleipnirgroup.github.io/Choreo

- DogLog logging library — doglog.dev

- maple-sim physics simulation — shenzhen-robotics-alliance.github.io/maple-sim

- Chief Delphi: FRC 6328 Open Alliance build threads (2022–2025), “State Machines in FRC Programming” thread, and Open Alliance build threads — chiefdelphi.com

- Tino-FRC-2473 / FSMBotTemplate (FSM-as-alternative reference) — github.com/Tino-FRC-2473

Page
