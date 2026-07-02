# The Drivetrain as Architecture — What a Drive Base *Is*, Empirically

*A corpus investigation into the one subsystem every robot has. The question isn't "how do you write
a swerve drive" — it's **what is a drivetrain, architecturally**: is it a subsystem, is it
fundamental, what role does it play that other mechanisms don't? The answer, from reading 55 teams'
code: the drivetrain is the only subsystem that is **both an actuator and the robot's primary
sensor**, and its most-consumed output is not motion but **pose** — it is the physical seat of the
robot's world-model. This doc is the empirical companion to the design in
[`../specs/portable-swerve-interface.md`](../specs/portable-swerve-interface.md); the spec says what
to build, this says what teams actually built and why the design follows from it.*

> **Status:** empirical, from `data/code-index.duckdb` (684 repos, 629k symbols, 280k imports) and
> `grep` over the 683 cloned repos under the corpus root. Prevalence figures use **one season repo per
> team (latest year), 55 teams**. Counts shift a little with detector definitions (noted inline); the
> *shape* is robust. Method queries are reproducible against the index — see **Pointers**.

---

## 0. The question, and why it's not obvious

Ask "what is a drivetrain" and the easy answer is "the thing that makes the robot move." But
architecturally that undersells it, and the corpus shows why. Every other subsystem is *either* an
actuator (an arm moves) *or* a sensor (a camera measures). The drivetrain is the only one that is
**both at once** — and what it measures is the single value the rest of the robot depends on most:
**where am I on the field.** So the drivetrain is not "a subsystem like the others." It is the
subsystem that holds the robot's place in the world.

---

## 1. Three roles in one class

Reading how teams structure it, a drivetrain is simultaneously **three architectural things**, and the
sophistication of a team is largely *which of the three it separates into its own layer*:

1. **A device / plant** — four swerve modules + a gyro (or, when wrapping CTRE, the whole
   `CommandSwerveDrivetrain`). The physical hardware. Belongs *below* the IO line.
2. **A subsystem** — the WPILib command target, the requirement-locking unit. The coordination handle
   the rest of the code schedules against.
3. **A world-model anchor** — it owns the `SwerveDrivePoseEstimator`, so it is where wheel odometry +
   gyro + vision fuse into **the robot's pose**. This is the role that makes it *fundamental* rather
   than merely universal — see §8, where `Pose` is read 682× across the corpus.

A novice team fuses all three into one `Drivetrain extends SubsystemBase` god-class. An elite team
splits them: device below an IO seam, subsystem above it, pose-estimator inside the subsystem. The
whole spec is, in effect, "give each of the three roles its own altitude."

---

## 2. Universality — the only subsystem you can assume exists

Across 55 season repos (one per team, latest year):

| | | |
|---|---|---|
| Have a drivetrain class | **52 / 55** | **94%** |
| Drivetrain lives in a `/subsystems/` directory | **47 / 55** | **85%** |
| Import `SubsystemBase` (command-based at all) | **45 / 55** | **81%** |

So: **the drivetrain is the one near-universal subsystem, and teams overwhelmingly model it as a
command-based `Subsystem`.** The handful without a detectable drivetrain class are library / Ri3D /
off-season repos, not robots missing a drive base. There is no competitive robot in the corpus whose
drivetrain is *not* a subsystem — it is the load-bearing example of the command-based pattern.

---

## 3. Drive type — swerve is the world now

| Drive type | season repos |
|---|---|
| Swerve | **≥ 38 / 55 (69%)** — *undercount*, see note |
| Differential (tank / arcade) | **4 / 55 (7%)** |
| Both present (legacy + current) | 3 |

The swerve figure is a floor: the `SwerveModule`-class detector **misses pure CTRE-generated robots**,
which use the *library's* `SwerveModule` rather than a user-defined one, so true swerve prevalence is
≈85–90%. Differential survives only as Ri3D/rookie/B-team code. **For a competitive team in this era,
"drivetrain" means "swerve" by default** — which is why the design spec is swerve-shaped and treats
differential as the degenerate case, not the other way around.

---

## 4. The architecture spectrum — how the drivetrain is built

Classifying the ~49 swerve-ish drivetrain repos by *primary* architecture (priority-ordered, so each
repo lands once):

| Style | repos | share | what it means |
|---|---|---|---|
| **CTRE-generated, used ≈as-is** | 24 | **48%** | the generated `CommandSwerveDrivetrain` *is* the subsystem — fast, vendor-locked (doc 07's default) |
| **CTRE wrapped below an owned IO seam** | 7 | 14% | 254/2910 pattern — generated device demoted below a `DriveIO`/`SwerveIO` (§5) |
| **Hand-rolled monolithic** | 6 | 12% | one big `Drivetrain extends SubsystemBase` |
| **AdvantageKit per-module `ModuleIO`/`GyroIO`** | 6 | 12% | built from motors, fine-grained seam |
| **YAGSL** | 3 | 6% | JSON-config black box |
| differential-only | 2 | 4% | — |
| REV MAXSwerve template | 1 | 2% | — |

Two readings of this table:

- **≈63% of teams sit on CTRE's generated drivetrain in some form** (48% as-is + 14% wrapped). The
  CTRE swerve generator has effectively become the *default* drive base of FRC — which is exactly
  doc 07's thesis (`07-code-generators.md`) seen from the drivetrain side.
- **Only ≈27% own a real IO seam** (14% CTRE-wrapped + 12% per-module). The seam that the rubric
  rewards — and that the spec is built around — is still a minority practice, concentrated in the
  strongest teams. Supporting signal: `SwerveSetpointGenerator` appears in **9 teams**, maple-sim in
  **11** — the elite-practice tail.

Naming corroborates the spread (distinct teams defining a class of that name):
`SwerveModule` (40), `DriveConstants` (38), `Drive` (32), `TunerSwerveDrivetrain` (22),
`Drivetrain` (21), `CommandSwerveDrivetrain` (19), `DriveSubsystem` (14), `SwerveSubsystem` (11),
`SwerveModuleIO` (8), `MAXSwerveModule` (7), `SwerveSetpointGenerator` (9), `MapleSimSwerveDrivetrain` (6).

---

## 5. The elite pattern — read it straight off the package listing

The clearest evidence in the whole investigation is what the strongest teams' `drive/` directories
*contain*. Two examples, verbatim from disk:

```
254 (2025)  subsystems/drive/          2910 (2026)  subsystems/drive/
  DriveSubsystem.java   ← Subsystem       SwerveSubsystem.java   ← Subsystem
  DriveIO.java  @AutoLog ← IO SEAM         SwerveIO.java  @AutoLog ← IO SEAM (two inputs structs)
  DriveIOHardware.java  ← real impl        SwerveIOCTRE.java      ← real impl
  DriveIOSim.java       ← sim impl         SwerveIOSim.java       ← sim impl
  CommandSwerveDrivetrain.java ← CTRE      CommandSwerveDrivetrain.java ← CTRE device
  Comp/Prac/SimTunerConstants  ← owned     SetModulePositionsRequest.java ← custom SwerveRequest
  DriveViz.java         ← telemetry
```

Three things this layout proves:

1. **The three roles of §1 are split into separate files.** `DriveSubsystem` (role 2) sits on top of
   `DriveIO` (the seam to role 1), with the pose-estimator (role 3) inside the subsystem.
2. **The CTRE-generated `CommandSwerveDrivetrain` is demoted to a device.** In both repos it
   **does not `implements Subsystem`** — it's a plain class wrapped by `DriveIOHardware`/`SwerveIOCTRE`
   so `com.ctre` stops at the seam and never reaches the subsystem. (Contrast the 48% who let the
   generated class *be* their subsystem.)
3. **They ingest the generator's constants but own the architecture** — 254 even keeps *three*
   `TunerConstants` variants (`Comp`/`Prac`/`Sim`) as owned files. Exactly doc 07's "generate the
   numbers, own the architecture."

And the hand-rolled end of the spectrum still reaches for a seam in spirit: team 868's Ri3D
`Drivetrain extends SubsystemBase implements BaseSwerveDrive` — a *team-defined* `BaseSwerveDrive`
interface — shows even a one-week robot instinctively wants a contract in front of the hardware.

---

## 6. Seam granularity — two places to cut, and what decides it

The elite repos reveal a subtlety the per-module AdvantageKit template alone wouldn't: there are
**two altitudes** at which teams cut the IO seam, and the right one depends on what's below it.

| Granularity | seam | who | when it's right |
|---|---|---|---|
| **Per-module** | `ModuleIO` + `GyroIO` (one drive + steer + encoder ×4) | AdvantageKit template, the 6 per-module teams | you **build from motors** |
| **Per-drivetrain** | one `DriveIO`/`SwerveIO` wrapping the whole CTRE swerve | 254, 2910 | you **wrap a vendor's swerve** (CTRE already abstracts the modules) |

Both are the *same seam* — data-struct read side, intent write side, vendor types below only — cut at
different heights. Re-cutting per-module *below* CTRE's `CommandSwerveDrivetrain` would be redundant,
so 254/2910 cut once, around the whole thing. The coarse contract is tiny: **`SwerveRequest` in,
`SwerveDriveState` out** (§7–8). This nuance is now §3.3 of the spec.

---

## 7. The `CommandSwerveDrivetrain` interface (the device most teams stand on)

Since ~63% of teams stand on CTRE's generated drivetrain, its surface *is* the de-facto drive API.
What it **is**:

```java
class CommandSwerveDrivetrain extends TunerSwerveDrivetrain implements Subsystem
//    TunerSwerveDrivetrain extends SwerveDrivetrain<TalonFX, TalonFX, CANcoder>
```

i.e. CTRE's generic `SwerveDrivetrain<TalonFX,TalonFX,CANcoder>` + the one `implements Subsystem` that
makes it command-schedulable. The generated subclass adds a tight surface — consensus methods across
the 19 teams that have one, by team prevalence:

| Method | teams | role |
|---|---|---|
| `applyRequest(Supplier<SwerveRequest>)` | 16 | **the control entry point** (`= run(() -> setControl(req))`) |
| `startSimThread()` | 15 | 5 ms `Notifier` → `updateSimState(dt, V)` |
| `periodic()` | 12 | applies alliance/operator perspective |
| `addVisionMeasurement(...)` | 11 | pose fusion (often overridden for `fpgaToCurrentTime`) |
| `sysIdQuasistatic` / `sysIdDynamic` | 10 | characterization (see §9 on the name) |
| `configureAutoBuilder` | 6 | PathPlanner wiring |

Everything substantive — `setControl`, `getState`, `registerTelemetry`, `resetPose`,
`setOperatorPerspectiveForward` — is **inherited** from CTRE's `SwerveDrivetrain`. The two leaks that
force a wrap if you want vendor-neutrality: the class *is* a `SwerveDrivetrain<TalonFX,…>`, and
`getModule(i)`/`getPigeon2()` return raw `TalonFX`/`Pigeon2`. Strip it to the contract and it is
exactly the coarse `DriveIO` of §6: **request in, state out.**

---

## 8. The contract surface: `SwerveRequest` in, `SwerveDriveState` out

The two CTRE types that *are* the drive contract, ranked by real corpus usage.

### 8.1 `SwerveRequest` — the control vocabulary (intent objects, not method calls)

```java
interface SwerveRequest { StatusCode apply(SwerveControlParameters params, SwerveModule<?,?,?>... modules); }
```

| Request (by corpus uses) | uses | purpose |
|---|---|---|
| `FieldCentric` | **324** | field-relative translate + rotate (default teleop) |
| `SysIdSwerveRotation` | 129 | rotation characterization (§9) |
| `SwerveDriveBrake` | 119 | X-lock the wheels |
| `FieldCentricFacingAngle` | 115 | field translate, heading held by a θ-PID |
| `ApplyRobotSpeeds` (+`ApplyFieldSpeeds` 25) | 102 | raw `ChassisSpeeds` (path-follower entry) |
| `SysIdSwerveTranslation` / `SysIdSwerveSteerGains` | 92 / 91 | translation / steer characterization |
| `RobotCentric` | 80 | robot-relative drive |
| `PointWheelsAt` | 74 | aim modules at one angle |
| `Idle` | 48 | do nothing |
| `RobotCentricFacingAngle` | 2 | (noise — droppable) |

Builder usage confirms the modifier surface: `withVelocityX/Y` (368/353), `withDriveRequestType` (337,
the open-vs-closed-loop switch), `withRotationalRate` (294), `withDeadband`/`withRotationalDeadband`
(148/126), `withTargetDirection` (101, for FacingAngle), `withForwardPerspective` (58),
**`withWheelForceFeedforwardsX/Y` (44/40)** — the live channel by which the L3 setpoint generator's
per-module forces reach the wheels.

### 8.2 `SwerveDriveState` — and the finding that names the whole doc

CTRE models drive state as a **flat, PascalCase, public-field POD**. Field access counts:

| Field | accesses | | Field | accesses |
|---|---|---|---|---|
| `Pose` | **682** | | `ModulePositions` | 55 |
| `ModuleStates` | 322 | | `FailedDaqs`/`SuccessfulDaqs` | 19 / 17 |
| `Speeds` | 243 | | `RawHeading` | 17 |
| `ModuleTargets` | 154 | | `Timestamp` | ~0 |
| `OdometryPeriod` | 101 | | | |

**`Pose` is read 682 times — more than any actuator field on any subsystem in the corpus.** That single
number is the empirical proof of §1's claim: the drivetrain's most important output is not its motion
command but its **state estimate** — *where am I* — because auto, aiming, and vision all consume it.
The drivetrain is the world-model anchor, measured. And note CTRE shipped this state as a flat data
struct — the same *inputs-struct-as-data* idea AdvantageKit formalizes with `@AutoLog`, arrived at
independently. Modeling our neutral `DriveIOInputs` on these fields is adopting a convergent consensus,
not inventing one.

---

## 9. Sidebar: the one name to *not* keep — `SysId`

The characterization requests (`SysIdSwerve*`, ~310 uses combined) are the #2 request family, so the
capability is essential — but the **name** should not survive into a portable interface.
`SysId` = "System Identification," a control-theory term that **collides with software's prior claims
on both words**: *system* reads as the machine/OS, *identification* reads as identity/auth, and the
abbreviation `sysId` is indistinguishable from a system identifier (UUID/PID/tenant key). It fails the
"a name must survive a change of reader" test. The FRC community already routed around it — teams say
**"characterize the drive,"** the gains are *"characterization gains"* — so the portable interface
names the arm **`Characterize` / `PlantResponse`**, following the community's correction. (`plant` is
the one control term software never spent; `response` is native characterization vocabulary.) The
general policy and the worked design now live in §5.1 of the spec.

---

## Pointers (how this was derived)

- **Index:** `data/code-index.duckdb` — `symbols` (kind/name/parent/file_path), `imports`
  (target/raw), `repos` (cloned/fork/year), 55 season repos via `row_number() over (partition by
  team order by year desc)`. Queried with the repo `.venv` duckdb.
- **Source reads:** `grep` over the 683 cloned repos at the corpus root (`SwerveRequest\.\w+`,
  `SwerveDriveState` field access, `.withX` builders), and direct reads of the 254/2910/868/2877
  `drive/` packages.
- **Architecture detectors** (with their definitional caveats) and the prevalence tables are
  reproducible from the queries above; counts move a few points with detector phrasing, the shape does
  not.

## See also (internal)

- [`../specs/portable-swerve-interface.md`](../specs/portable-swerve-interface.md) — the design this
  evidence motivates (the 5-layer model; §3.3 granularity, §5 the request union, §5.1 naming, §6.1 the
  state struct all cite the numbers here).
- [`07-code-generators.md`](07-code-generators.md) — why ≈63% of drivetrains are CTRE-generated; the
  "generate the constants, own the architecture" rule the 254/2910 layout embodies.
- [`02-frc-37-team-survey.md`](../archived/corpus-analysis/02-frc-37-team-survey.md) — the modularity ladder the architecture
  spectrum (§4) is a per-subsystem slice of.
- [`03-io-layer-strategy-pattern.md`](../archived/corpus-analysis/03-io-layer-strategy-pattern.md) — why the seam in §5–6 is
  ports-and-adapters.
- [`../specs/portable-motor-interface.md`](../specs/portable-motor-interface.md) — the `MotorIO` the
  per-module seam composes; the naming philosophy §9 applies.
