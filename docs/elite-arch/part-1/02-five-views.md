---
title: 2. The architecture in five views
weight: 2
---
No single drawing captures an architecture. A floor plan, a wiring diagram, and a description of how
people move through a building are all true at once, and none of them is the others. Software is the
same, and the standard way to hold several true pictures at once is Kruchten's **4+1 view model**:
four views of the structure — *logical*, *development*, *process*, *physical* — tied together by a
fifth, a set of *scenarios* that walk through all four. This chapter renders the Elite Architecture in
those five views, at low resolution. It is the whole board before we pick up any one piece.

All five describe **positive space** — where the parts are. The chapters after this one describe the
**negative space**, the seams between the parts. See the board first.

## Logical view — the parts and how they relate

The logical view asks what the major components are and how they talk. "Component" here is the
software-engineering sense, not WPILib's: a coherent unit of responsibility, which may be one
subsystem or a cluster of them. An elite robot has six that recur.

```d2
direction: down
DS: "Driver Station / auto selector
(human or routine intent)"
CMD: "Command & binding layer
(RobotContainer, triggers)"
SUP: "Superstructure
(planning — one goal to many setpoints)"
SUBS: "Subsystems" {
  DRIVE: Drive
  ELEV: Elevator
  ARM: Arm
  INTAKE: Intake
  VIS: Vision
}
RS: "RobotState
(the shared world model)"
IO: "IO layer
(per-subsystem hardware interface)"
HW: Hardware / sim
DS -> CMD: button / auto step
CMD -> SUP: goal
SUP -> SUBS: setpoints
SUBS -> IO: device commands
IO -> HW: voltages
SUBS.DRIVE -> RS: odometry
SUBS.VIS -> RS: vision observations
RS -> SUP: pose · situation
```

Read it top to bottom and the responsibilities separate cleanly. **Intent** arrives from the driver or
an autonomous routine. The **command layer** turns a button or an auto step into a request. The
**superstructure** is the planner: it takes one robot-wide goal and decides the legal setpoint each
subsystem should hold. The **subsystems** each close their own control loop. The **IO layer** is the
only thing that touches devices. And off to the side, the **world model** (`RobotState`) is written by
the sensing subsystems and read by the planner — the one place the robot's belief about the field
lives. Communication flows down as *commands* and up as *state*; no component reaches across a layer to
poke another's hardware.

## Development view — the libraries it stacks on

The development view asks what the code is built *out of* — the library layering a programmer sees at
build time. Every FRC robot is a stack, and the elite move is a rule about which layer may depend on
which.

```d2
direction: up
WPI: "WPILib — HAL, wpimath, command-based
the floor; every team builds on it"
VENDOR: "Vendor libraries — Phoenix 6 (CTRE),
REVLib, PhotonVision / Limelight"
IOIMPL: "IO implementations — ElevatorIOTalonFX, ...
the one place vendor types are allowed"
LOGIC: "Subsystem logic · Superstructure · RobotState
no vendor type; depends only on WPILib + the IO interface"
WPI -> VENDOR
VENDOR -> IOIMPL
WPI -> LOGIC
IOIMPL -> LOGIC: plugged in via the IO interface { style.stroke-dash: 4 }
```

At the bottom is **WPILib** — the hardware abstraction layer, the `wpimath` geometry and control
classes, and the command-based framework. Everyone stands on it. On top of it sit the **vendor
libraries**: CTRE's Phoenix 6 for Falcon/Kraken motors and the Pigeon gyro, REVLib for SPARK
controllers, PhotonVision or the Limelight library for cameras. A naive robot lets those vendor types
spread everywhere. The elite robot confines them: only the **IO implementations** import `com.ctre` or
`com.revrobotics`, and the **logic layer** — subsystems, coordination, world model — depends on
WPILib and the team's own IO *interface*, never on a vendor. That single dependency rule is what later
lets a subsystem run in simulation or against a different motor brand without edits. (Most teams also
pull in an ecosystem tier — AdvantageKit or DogLog for logging, PathPlanner or Choreo for paths — and
the same rule applies: useful, but kept off the logic's critical dependencies.)

## Process view — what happens every 20 ms

The process view asks what runs *when*. An FRC robot is, at heart, one loop that fires every 20 ms (50
Hz), and the most useful thing to trace through it is a single packet of driver intent becoming motion
and coming back as measurement.

```d2
direction: right
DS: "Driver Station
joysticks @ ~50 Hz"
NET: radio / network
READ: "1. read
DS packet + IO.updateInputs()"
LOG: "2. log
snapshot every input"
DECIDE: "3. decide
scheduler to goal to setpoints"
ACT: "4. actuate
IO writes over CAN"
PLANT: motors · sensors
DS -> NET -> READ
READ -> LOG -> DECIDE -> ACT
ACT -> PLANT
PLANT -> READ: sensor reads, next tick { style.stroke-dash: 4 }
```

Each tick runs the same four steps in the same order: **read** the driver packet and the sensor inputs
through the IO layer, **log** that snapshot, **decide** what the mechanisms should do (the scheduler
runs commands, a command sets a superstructure goal, the goal fans out to setpoints), and **actuate**
by writing through the IO layer onto the CAN bus. The driver never commands a motor directly; the
packet sets *intent*, and the loop turns intent into voltage. Most of the robot is single-threaded by
design — predictability beats parallelism here — with two deliberate exceptions: high-rate odometry
can run on its own 250 Hz thread, and vision runs asynchronously on a coprocessor and pushes
timestamped measurements in when they are ready.

## Physical view — what connects to what

The physical view is the one most software writeups skip, and on a robot it is indispensable: the code
runs on real electronics wired in a specific topology, and the boundaries in the logical view often
mirror boundaries in the wiring. This is the robot as an electrician sees it.

```d2
direction: down
DSL: "Driver Station laptop
(field wall / pit)"
RADIO: "Robot radio
(Wi-Fi to the field)"
SWITCH: Ethernet switch / PoE
RIO: "roboRIO
runs the robot program"
PDH: "Power Distribution Hub
battery to everything"
LL: "Limelight
smart camera"
OPI: "Coprocessor
Orange Pi · PhotonVision"
CANrio: "CAN bus (roboRIO)" {
  PIGEON: Pigeon 2 — gyro
  MA: TalonFX — arm
  MI: SPARK MAX — intake
  PDHc: Power Distribution Hub
}
CANivore: "CANivore bus (USB-CAN)" {
  DRV: 4x TalonFX — drive
  STR: 4x TalonFX — steer
  ENC: 4x CANcoder
}
LOCAL: "roboRIO DIO / PWM / Analog
beam breaks · limit switches · servos"
DSL -> RADIO: Wi-Fi
RADIO -> SWITCH
SWITCH -> RIO: Ethernet
SWITCH -> LL: Ethernet
SWITCH -> OPI: Ethernet
RIO -> CANrio: CAN
RIO -> CANivore: USB
RIO -> LOCAL: wires
PDH -> RIO: 12 V { style.stroke-dash: 4 }
```

The **roboRIO** is the brain and the only thing running team code. Everything actuated or sensed over
**CAN** hangs off one daisy-chained, terminated bus — motor controllers, the Pigeon gyro, CANcoders,
the power distribution hub — and strong teams put the swerve modules on a **second** CAN bus (a
CTRE CANivore over USB) to get the bandwidth for high-rate odometry. **Cameras and coprocessors** are
not on CAN at all; they reach the roboRIO over **Ethernet** through a switch, and talk to the field
through the **radio**. Simple sensors — beam breaks, limit switches, servos — wire straight into the
roboRIO's digital, PWM, and analog ports. Notice the mirror: the IO seam in the code falls almost
exactly on the CAN boundary in the wiring — the things behind an `XxxIO` interface are, physically,
the things on the bus.

## Scenarios — the views in motion

The fifth view is the others put in motion: a concrete task traced through all four. Two are enough to
show the shape.

**A teleop score.** The operator presses *score L4*. A driver packet (process view) carries the
button to the roboRIO; the binding layer (logical view) turns it into a goal handed to the
superstructure, which sequences setpoints — clear the frame, raise the elevator, then release — and
the subsystems drive those setpoints through their IO layer onto the CAN bus (physical view), all in
code that imports no vendor type above the IO line (development view). The whole path, button to motor
voltage, completes inside one or a few 20 ms ticks.

**An autonomous routine.** No driver packet now; intent comes from a path-follower running as a
command. It reads the robot's pose from `RobotState` — fused from CANivore odometry and Ethernet
vision corrections — computes a chassis speed, and feeds the drivetrain the same setpoint path a
teleop request would. Same components, same loop, same wiring; only the source of intent changed. That
interchangeability of intent sources is the architecture working as designed.

Five views, one architecture. They show you where everything *is*. The next chapters turn the picture
inside out and look at the **seams** — the joints between these parts, where the architecture's real
leverage lives. They are the elite target, not the median: measured across 55 season repos the IO seam
appears in 24 teams, a `RobotState` world model in 26, and a real coordinator in 23 — but **all three
together in only 10 teams (18%)**. The individual parts are common; assembling the full set of seams is
what separates the top tier. We start with the spine: [the IO seam](03-the-io-seam.md).
