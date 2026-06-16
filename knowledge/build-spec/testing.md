# Testing FRC Robot Code

> A companion to [`elite-architecture.md`](elite-architecture.md) and the
> [subsystem series](subsystems/00-anatomy-of-a-subsystem.md). Testing is the **deferred dividend of
> the IO seam** (rubric D4): once a subsystem can be built on an `XxxIOSim`, you can verify its
> behavior on a laptop, in CI, before it ever reaches a robot.
>
> *Code is quoted to study the technique, not to copy.*

---

## 1. What it is, and why it's rare

A test constructs part of the robot, drives it, and **asserts** what it did. FRC's defining fact
about testing: **almost no one does it.** D4 is the rarest, most discriminating marker in the corpus
— most teams score 0 — and it barely correlates with winning. That's the point: tests don't put
points on the board, they're the clearest signal of real **software-engineering culture** and the
thing that lets a program move fast without breaking itself. The reason it's rare is that it has a
prerequisite — the IO seam — and the reason it's *possible* is that you already built that seam (see
any subsystem doc's §6.1). SciBorgs (1155) is the worked example throughout; Ranger Robotics (3015)
ships 37 test files. They are the exceptions worth copying.

## 2. The kinds of tests (in increasing value)

| Kind | What it does | Example |
|---|---|---|
| **Construction smoke** | build the subsystem, assert it doesn't throw | `Intake.create().close()` |
| **Sim-backed unit** | build subsystem on `XxxIOSim`, command a setpoint, assert it's reached | `ElevatorTest.reachesPosition` |
| **Command/behavior** | run a real `Command` to completion, assert end state | `SwerveTest.testModuleDistance` (odometry) |
| **Coordination** | build *several* subsystems + the command that composes them, assert the joint result | `ShootingTest` (4 subsystems) |
| **System check** | a `Command` + assertions that runs as a unit test **or on the real robot** | SciBorgs `Test` / `goToTest(...)` |
| **Pure-logic** | test math with no HAL (kinematics, a feedforward, `RobotState` fusion) | a `RobotState` test |
| **Characterization** | a SysId *measurement* run (not pass/fail) — produces gains | `SysIdRoutine` |

The ladder maps onto the rubric: a smoke test is D4 L1; sim-backed asserts are L2; tests gating
merges in CI is L3; broad command-level suites are L4.

## 3. The key idea — the IO seam *is* your mock

You do not need Mockito or a mocking framework. **The `XxxIO` interface and its `XxxIOSim`
implementation are the test double.** Mocking "the layer below" means passing the sim impl:

```java
elevator = new Elevator(new SimElevator());   // the mock is just another XxxIO
```
Three things this gives you for free, all from the subsystem series:
- **`XxxIOSim`** — physics-backed fake hardware (the whole mechanism, [`simulation.md`](simulation.md)).
- **A fakeable sensor** — a beam-break exposed as an inputs field can be set in the test (see
  [`04-roller-gamepiece`](subsystems/04-roller-gamepiece.md) §6.1).
- **`NoXxx`** — a null-object impl to test the robot with a mechanism *disabled*.

To test the layer *above* a subsystem (a command, the Superstructure), construct the subsystems on
sim and exercise the command — the mock is still just the sim IO, one level down.

## 4. The harness — how a sim test actually runs

A WPILib unit test must boot a simulated HAL and control time deterministically. SciBorgs' helper is
the canonical harness; learn these four moves:

*1155 SciBorgs — `Reefscape-2025/.../lib/UnitTestingUtil.java`*
```java
public static void setupTests() {                 // 1. boot the simulated HAL + DriverStation
  assert HAL.initialize(500, 0);
  DriverStationSim.setEnabled(true); DriverStationSim.setTest(true); DriverStationSim.notifyNewData();
  SimHooks.restartTiming();
}
public static void fastForward(int ticks) {       // 2. step the scheduler AND sim time, deterministically
  for (int i = 0; i < ticks; i++) {
    CommandScheduler.getInstance().run();
    SimHooks.stepTiming(TICK_RATE.in(Seconds));    // time is controlled, not wall-clock
  }
}
public static void run(Command c, int runs) { c.schedule(); fastForward(runs); }     // 3. schedule + advance
public static void runToCompletion(Command c) {    // 4. run until the command finishes
  c.schedule(); fastForward(1);
  while (c.isScheduled()) fastForward(1);
}
public static void reset(AutoCloseable... subsystems) throws Exception {  // teardown: @AfterEach
  CommandScheduler.getInstance().cancelAll();
  for (var s : subsystems) s.close();
}
```
The two non-obvious essentials: **`HAL.initialize`** (without it, constructing a subsystem that
touches WPILib hardware throws), and **`SimHooks.stepTiming`** (so `Timer`/profiled controllers
advance by a known dt — your test is a deterministic fast-forward, not a sleep). Make subsystems
`AutoCloseable` so `reset()` can free their sim resources between tests.

## 5. Organization, goals, and CI

**Organize** `src/test/java` to mirror `src/main/java`, one `XxxTest` per subsystem
(`ElevatorTest`, `SwerveTest`, …) — so the test for a mechanism lives beside nothing else and a new
member finds it by name. Put shared helpers (`UnitTestingUtil`, an `Assertion`/`Test` type) in a
`lib/` test-support package.

**Goals**, in priority order:
1. **Regression** — a refactor that breaks "elevator reaches L4" fails CI, not the robot at an event.
2. **Sim validation** — does the controller *actually* converge with these gains? (catches a sign
   error or an untuned profile before bag day).
3. **Interlock safety** — the highest-value test: assert two mechanisms sequence safely (see
   [`08-superstructure`](subsystems/08-superstructure.md) §6.1) — the failure that physically breaks
   robots.

**CI gate (D4 L3):** a `.github/workflows/*.yml` running `./gradlew test` on every push/PR, so tests
*gate merges*. Tests that aren't run are decoration; the workflow is what turns a test suite into a
safety net. JUnit 5 idioms the corpus uses: `@Test`, `@ParameterizedTest @ValueSource(...)` (sweep
setpoints), `@RepeatedTest(5)` (random inputs), `@BeforeEach setupTests()` / `@AfterEach reset(...)`.

## 6. The system-check trick — one artifact, two uses

SciBorgs' best idea: a **`Test` is a command plus assertions**, runnable as a JUnit test *or* on the
real robot as a "systems check."

*1155 SciBorgs — `Reefscape-2025/.../lib/Test.java`*
```java
public record Test(Command testCommand, Set<Assertion> assertions) { /* ... */ }
public static void runUnitTest(Test test) { runToCompletion(toCommand(test, true)); }
```
The subsystem exposes a `goToTest(setpoint)` that returns a `Test` (drive to the setpoint, assert it
arrived). In a JUnit test you `runUnitTest(elevator.goToTest(L4))`; at an event you bind the *same*
`Test` to a dashboard button to verify the real mechanism. One assertion, two environments — write it
once.

## 7. Be honest about what your sim is tuned for

A sim test is only as good as the sim's physics constants. The corpus is candid about this:
SciBorgs' `ElevatorTest` and `SwerveTest` (velocity + odometry) run, but their `ArmTest` is
`@Disabled` ("Doesn't work :/") — an arm's moment of inertia is hard to estimate, so the sim won't
settle until it's measured ([`02-rotational-position`](subsystems/02-rotational-position.md) §6.1). The
right move is not to delete a flaky test but to **leave it disabled with the reason written down** and
fix the constant. A disabled-with-a-reason test is a TODO; a deleted test is amnesia.

## 8. Checklist — is your testing real?

- [ ] `src/test` mirrors `src/main`; one `XxxTest` per subsystem, helpers in a `lib/` support package.
- [ ] Tests construct subsystems on `XxxIOSim` (the IO seam is the mock) — no Mockito needed.
- [ ] A harness boots the HAL (`HAL.initialize`) and steps sim time (`SimHooks.stepTiming`) deterministically.
- [ ] Subsystems are `AutoCloseable`; `@AfterEach` cancels commands and closes them.
- [ ] At least one **command-level** test runs a real command to completion and asserts end state.
- [ ] At least one **interlock** test asserts two mechanisms sequence safely.
- [ ] `.github/workflows` runs `./gradlew test` on every PR — tests gate merges.
- [ ] Flaky tests are `@Disabled` with the reason, not deleted.
