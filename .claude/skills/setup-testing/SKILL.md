---
name: setup-testing
description: Add the JUnit test harness to a WPILib robot project so subsystems can be unit-tested in simulation — a HAL bootstrap + deterministic sim-time stepping helper, the Test=command+assertions pattern, and a CI workflow that runs `gradle test` on every push. Use when a project has no tests, or to enable testing before adding subsystems ("set up testing", "add a test harness", "make this testable in CI").
---

# Set up testing

Make the IO seam pay its dividend: once a subsystem can be built on its `*IOSim`, it's unit-testable
with no hardware. The full rationale + the kinds of tests are in **`knowledge/build-spec/testing.md`**
(bundled). This skill installs the harness so `add-subsystem`'s generated tests run.

## Steps
1. **Confirm JUnit 5 is on the test classpath.** In `build.gradle`, ensure `testImplementation` for
   `org.junit.jupiter:junit-jupiter` and `test { useJUnitPlatform() }`. GradleRIO projects often have
   this; add it if missing.
2. **Add the harness.** Copy `templates/UnitTestingUtil.java` into the project's test-support package
   (e.g. `frc/robot/lib/`). It provides the four moves every sim test needs:
   - `setupTests()` — boot the simulated HAL + DriverStation, restart sim timing.
   - `fastForward(ticks|time)` — step `CommandScheduler` **and** `SimHooks.stepTiming` together
     (deterministic; a "4-second" test runs instantly).
   - `run(command)` / `runToCompletion(command)` — schedule and advance.
   - `reset(subsystems...)` — cancel commands + `close()` each `AutoCloseable` subsystem (`@AfterEach`).
3. **Make subsystems `AutoCloseable`** so `reset(...)` can free sim resources between tests.
4. **(Optional) the system-check pattern** — a `Test = (Command, assertions)` that runs as a unit
   test *or* bound to a dashboard button on the real robot. See `testing.md` §6.
5. **Add the CI gate.** Copy `templates/test.yml` to `.github/workflows/` — it runs `./gradlew test`
   on push/PR so tests gate merges (rubric D4 level 3). Without CI, a test suite is decoration.

## Verify
- `./gradlew test` runs and passes (write one real test first via `add-subsystem`, or a smoke test).
- A test constructs a subsystem on its `*IOSim`, commands a setpoint, and asserts — no `HAL` errors
  (that means `setupTests()` ran) and it completes instantly (sim time, not wall-clock).
- Flaky tests are `@Disabled` **with the reason written down**, not deleted (`testing.md` §7).
