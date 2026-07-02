---
title: 6. The drivetrain — the special subsystem
weight: 6
---
Ask "what is a drivetrain" and the easy answer is "the thing that makes the robot move." The corpus
shows that undersells it. Every other subsystem is *either* an actuator (an arm moves) *or* a sensor
(a camera measures). The drivetrain is the only one that is **both at once** — and what it measures is
the single value the rest of the robot depends on most: where it is on the field. That is why it earns
its own chapter even in the overview.

## Three roles in one class

A drivetrain is simultaneously three architectural things, and a team's sophistication is largely
*which of the three it separates into its own layer*:

```d2
direction: down
DRIVE: Drivetrain {
  ANCHOR: "3 — World-model anchor
owns the pose estimator"
  SUB: "2 — Subsystem
the command target"
  DEV: "1 — Device / plant
4 modules + gyro"
  ANCHOR -- SUB
  SUB -- DEV
}
HW: hardware / CTRE swerve
WORLD: Auto · Aim · Vision
DRIVE.DEV -> HW: below the IO line { style.stroke-dash: 4 }
DRIVE.ANCHOR -> WORLD: Pose { style.stroke-dash: 4 }
```

A novice team fuses all three into one `Drivetrain extends SubsystemBase` god-class. An elite team
splits them: the device below an IO seam, the subsystem above it, the pose estimator inside the
subsystem. The whole build is, in effect, "give each of the three roles its own altitude."

## The one subsystem you can assume exists

Across 55 season repos, a drivetrain class appears in 52 (94%), lives in a `/subsystems/` directory in
85%, and is modeled as a command-based subsystem in 81%. There is no competitive robot in the corpus
whose drivetrain is *not* a subsystem — it is the load-bearing example of the command-based pattern.
And it is overwhelmingly swerve: differential drive survives almost exclusively in Ri3D (Robot in 3
Days demo builds) and rookie code, with true
swerve prevalence around 85–90% once you count the CTRE-generated robots a class-name grep misses. For
a competitive team in this era, "drivetrain" means "swerve" by default.

## The spectrum: generated default versus owned seam

Classifying swerve drivetrains by primary architecture reveals where the seam discipline actually
lives:

| Style | share | what it means |
|---|---|---|
| CTRE-generated, used ≈ as-is | 48% | the generated `CommandSwerveDrivetrain` *is* the subsystem — fast, vendor-locked |
| CTRE wrapped below an owned IO seam | 14% | the 254/2910 pattern — generated device demoted below a `DriveIO` |
| hand-rolled monolithic | 12% | one big `Drivetrain extends SubsystemBase` |
| per-module `ModuleIO`/`GyroIO` | 12% | built from motors, fine-grained seam |
| YAGSL / REV template / differential | ~14% | config black box or legacy |

Two readings: about **63% of teams sit on CTRE's generated drivetrain** in some form — it has become
the de-facto default drive base of FRC — while only about **27% own a real IO seam.** The seam the
rubric rewards is still a minority practice, concentrated in the strongest teams.

The elite move reads straight off the package listing. In 254's and 2910's `drive/` directories the
three roles are split into separate files, and the CTRE-generated `CommandSwerveDrivetrain` is
**demoted to a device** — it does not `implements Subsystem`; it is wrapped by a `DriveIOHardware` so
`com.ctre` stops at the seam and never reaches the subsystem. They ingest the generator's constants but
own the architecture — "generate the numbers, own the architecture." There are two altitudes to cut
the seam (per-module when you build from motors, per-drivetrain when you wrap a vendor's swerve); both
are the same seam at different heights, a distinction [Part II ch.
19](../part-2/19-the-drivetrain-subsystem.md) develops.

## Pose is the proof

The claim that the drivetrain is the world-model anchor is measurable. In the CTRE drive state struct,
the `Pose` field is read **682 times across the corpus — more than any actuator field on any subsystem.**
Auto, aiming, and vision all consume it. The drivetrain's most important output is not its motion
command but its state estimate: *where am I*. That single number is why the drivetrain feeds the state
seam of [ch. 4](04-the-state-seam.md), and why "what is a drivetrain" is finally a question about where
you draw your boundaries.

That closes the architectural core. The next section steps back to the practices that hang off these
seams — [simulation, testing, and logging](07-cross-cutting-practices.md).
