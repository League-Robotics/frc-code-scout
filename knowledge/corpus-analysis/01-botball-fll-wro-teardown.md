**Inside Competition Robot Code**

How Botball, FLL, and WRO Teams Actually Structure Their Programs

*A teardown of 21 real team repositories across four code formats and eleven competition seasons (2014–2025)*

# What this document is

This is a structural analysis of **real competition code written by student robotics teams**, pulled directly from public repositories. The goal is not to grade any team, but to extract the recurring architecture — the shapes that show up again and again across leagues, languages, and years — so it can be taught explicitly. 

The headline finding: despite using different hardware (KIPR Wallaby, LEGO EV3, LEGO SPIKE Prime), different languages (C, C++, Python, graphical block code), and different games every season, **every program converges on the same three-layer structure and the same handful of motion primitives.** The game changes annually; the architecture does not. That stability is the thing worth teaching.

## The corpus

Twenty-one repositories were collected and analyzed. They span:

- **Three leagues: **Botball / Junior Botball Challenge (KIPR), FIRST LEGO League (FLL), and World Robot Olympiad (WRO RoboMission).

- **Four code formats: **plain-text C/C++, plain-text Python, LEGO EV3-G graphical projects (.ev3), and LEGO SPIKE Prime word-block projects (.llsp3).

- **Eleven seasons: **2014 through 2025, including a longitudinal run of one team (Dead Robot Society) across four seasons and a WRO world-record full-score program.

| **Team / repo** | **League** | **Format** | **What it offers** |
| --- | --- | --- | --- |
| Dead Robot Society (×10 seasons) | Botball | Python | Named-subroutine mission scripts; longitudinal evolution |
| jbc-norman 2016 & 2020 | Jr. Botball | C + Python | 1,600+ files; how beginners' code actually looks |
| ihsboost | Botball | C++ | A full OOP control library (PID class hierarchy) |
| Tyngsborough HS | Botball | Python | Custom 'Botball for Python' framework; clean module boundary |
| LACT-0636, Parkside, Perry, SSMS, NoHo | Botball | C | Range from inline dead-reckoning to module split |
| GO-Robot (Germany) | FLL | Python | 1,000-line driving library with pluggable stop-methods |
| ducc. (Singapore) | WRO | EV3-G | World-record full-score RoboMission run |
| WRO 2025 RoboMission (Spanish) | WRO | SPIKE | 52-procedure block program, color-keyed cargo logic |

# The universal structure: three layers

Every program in the corpus separates into the same three layers, whether the team named their files that way or not. Reading any new competition program is mostly a matter of finding these three layers in it.

## Layer 1 — Constants & device map

Names the physical ports and the magic numbers: which motor is plugged into which port, where the color sensors are, and the exact servo positions for 'claw open' versus 'claw closed.' Nothing executes here — it is a lookup table the rest of the code reads from. The LACT team's claw definitions are typical:

#define CLAW       0      // servo port

#define CLAW_OPEN  2047   // fully open

#define CLAW_CLOSE 400    // gripping a game piece

#define CLAW_COW   1600   // half-open for the 'cow' object

#define WRIST_UP   1300

#define WRIST_DOWN 335

Teaching point: **the numbers are physical measurements, not arbitrary.** 2047 and 400 are calibrated to a specific robot's geometry. This is where students learn that code reflects the machine.

## Layer 2 — Motion primitives

A small, reusable set of movement functions that hide a sensor-feedback loop inside a simple call. This is the engineering core, and it is where the three leagues converge most tightly — every team independently arrives at nearly the same primitive set:

- **Drive-until-condition. **The workhorse. Competition code overwhelmingly prefers 'drive until a sensor says stop' over 'drive 30 cm,' because dead reckoning accumulates error.

- **Square-up-on-a-line. **Let one wheel keep going until both floor sensors hit a line, which re-zeroes the robot's heading against a physical landmark. The single most important reliability trick in the genre.

- **PID line-following. **Steer proportionally to how far off-center the robot is over a line edge. Appears in the FLL, WRO, and C++ library code.

- **Turn-to-angle. **Either timed (open-loop, no gyro) or gyro-feedback (closed-loop). The clearest hardware-driven difference between teams.

## Layer 3 — The mission script

The actual game plan, written as a sequence of calls to the primitives. This is the part that reads like a to-do list and changes completely every season. A good mission layer reads as plain English. Dead Robot Society's 2019 main() is the clearest example:

def main():

    act.init()                # enable servos, camera, calibrate, wait for light

    act.grab_bot_mayor()      # collect the scoring figures

    act.head_to_elec_lines()  # navigate to next mission area

    act.connect_elec_lines()  # actuate arm+motor to attach lines

    act.get_water_cube()      # drive to cube, lower arm, close claw, raise

    act.drop_water_cube()     # carry to target, release

# The locate – grip – relocate pattern

The game action you asked about — drive somewhere, sense a color, grab an object, carry it elsewhere — appears in nearly every repo. It is always built the same way: **approach roughly, then locate precisely against a landmark, then actuate the gripper in a fixed open/lower/close/raise order.** Dead Robot Society's water-cube grab:

def get_water_cube():

    g.create_drive_timed(-400, 4)         # approach the cube zone (rough)

    g.rotate(-90, 250)                    # face the cube

    g.create_drive_timed(500, 2.1)        # close in

    m.drive_to_black_and_square_up(100)   # LOCATE precisely on the line

    move_servo(c.sky_arm, c.arm_down)     # lower

    move_servo(c.sky_claw, c.claw_closed_water)  # GRIP

    move_servo(c.sky_arm, c.arm_vertical) # lift to carry

The same skeleton appears in the WRO world-record program as the MyBlocks findContainer → lowerClaw → grabContainers, and in the SPIKE program as the procedures set_carga_color → blue_carga (set cargo color, then handle blue cargo). Different hardware, identical logic.

## Branching on a sensed game state

The closest thing to 'intelligence' in these autonomous runs: sense one fact early, store it, and branch the whole mission on it. Dead Robot Society reads a camera at startup to detect **which building is burning** (returns 0/1/2 for left/middle/right) and every later subroutine branches on that value — three different grab routines, three different delivery approaches. The robot runs one program but takes a different physical path depending on what it saw.

## The match-lifecycle wrapper

Because these robots are fully autonomous with a hard time limit, the mission is bracketed by two rituals. A **start gate** (wait for the light to turn on, or a button press) and a **dead-man timer.**

shut_down_in(119.5);   // spawn a background timer that kills ALL motors

                       // at 119.5s no matter where the robot is in its code

The match ends at 120 seconds and a robot still moving gets penalized, so shut_down_in() runs in parallel with everything else. This is a clean, concrete example of how a competition rule shapes program structure.

# The sophistication spectrum

The same problem — 'follow a line smoothly' — is solved at wildly different levels across the corpus. Laying these side by side is the single best way to show students what 'getting better at this' actually means.

### Level 1 — Inline dead reckoning (LACT 2017)

No line-following at all. The mission is a flat list of distance/speed moves with comments. Brittle (any wheel slip compounds) but easy to read and debug. The team even left **commented-out camera-centering code** — a vision approach they tried and abandoned for hardcoded moves.

create_forward(64, 300);   // moving down middle of field towards botguy

create_left(1, 300);

straighten_ridge();        // physical re-alignment against a wall

### Level 2 — Proportional control (GO-Robot FLL)

A real feedback loop. Steering is proportional to the error between the sensor reading and a target, and — unusually for a school team — the PID gains are recomputed as a function of current speed on every loop.

change   = colorsensor.get_reflected_light() - 50   # error: dist from edge

steering = change*Kp + integral*Ki + (change-old)*Kd

movement_motors.start_at_power(speed, steering)

### Level 3 — An OOP controller library (ihsboost C++)

A high-school Botball team that built a reusable C++ library with a controller class hierarchy: an AccelerateController base class with Linear, Sinusoidal, and PID subclasses. Their PID uses trapezoidal integration and a properly dt-scaled derivative — textbook-correct control theory:

void PIDController::step(double error) {

    // trapezoidal integration, (b1+b2)/2 * h

    error_integral += (past_error + error) * .5 * dt;

    cur_speed = Kp*error + Ki*error_integral + Kd*(error-past_error)/dt;

    past_error = error;

}

Same idea as Level 2, but written as a library a whole team can reuse for years. This is the trajectory a serious program is aiming at: **from hardcoded moves, to feedback loops, to reusable abstractions.**

# Reading graphical (block) code as text

Two leagues ship their programs as graphical block code, not text — LEGO EV3-G (.ev3) and SPIKE Prime word blocks (.llsp3). These look like opaque binaries, but both are simply **ZIP archives** with a parseable program description inside. No bytecode disassembly is required.

| **Format** | **League(s)** | **What it really is** | **How to read it** |
| --- | --- | --- | --- |
| .ev3 | FLL (legacy), WRO | ZIP → .ev3p XML block diagrams | unzip, parse XML for MyBlock calls |
| .llsp3 | FLL, WRO RoboMission | ZIP → scratch.sb3 → Scratch JSON | unzip twice, walk the block tree |
| .rbf | (compiled EV3 output) | Actual VM bytecode | ev3dev lmsdisasm.py (rarely needed) |

Crucially, **the team ships the editable project, not a compiled binary** — so the logic is always recoverable. The block names are the mission vocabulary. Extracting them from the WRO world-record run yields its full mission script:

runWRO (top-level):

    fuelBigShip → travelToDepot → collectContainers → travelToSmallShip

    → [battery check] → unloadSpecialContainer → moorRobot → endRun

That is the identical init → named tasks → end shape as the Botball Python main() — recovered from a graphical file that started out looking unreadable.

# What stays the same across years

Tracking one team (Dead Robot Society) across three seasons shows the architecture holding constant while only the mission verbs change with each new game:

| **Season** | **The mission sequence (verbs change, skeleton doesn****'****t)** |
| --- | --- |
| 2017 | init → get_out_of_startbox → go_to_far_side → go_and_drop_poms → go_and_dump_blue → shutdown |
| 2018 | init → turnToRing → liftRing → dropRing → turnToTram → slideTram → approachBotguy → deliverBotguy |
| 2020 | init → head_to_botguy → grab_botguy → drop_botguy → grab poles → grab_orange_ball → deliver |

Every year: **initialize, run a sequence of named grab-and-deliver tasks, then debug/shut down.** A student who learns to read one season's code can read any season's code. This is the strongest argument for teaching the structure rather than the syntax.

# Implications for a teaching ladder

The corpus maps cleanly onto a progression you can teach in order:

- **Start with the mission script. **A beginner can write a flat list of timed moves (Level 1) on day one and have a robot that completes a run. Immediate payoff.

- **Introduce sensors as ****'****stop conditions.****'**** **Replace 'drive 4 seconds' with 'drive until you see black.' This is the conceptual leap from open-loop to closed-loop, and it is the single highest-value lesson.

- **Add proportional steering. **Once students believe sensors, line-following with a proportional term (Level 2) is a natural next step and visibly smoother.

- **Refactor into primitives, then a library. **When students copy-paste the same move sequence three times, that is the teachable moment for functions, then modules, then the OOP library (Level 3).

- **Botball/C++ rewards the deepest CS. **If the League's pitch is 'programming using robotics as the vehicle,' Botball is the strongest fit: real C/C++, true autonomy, object manipulation, and room for the ihsboost-style library work that looks like genuine software engineering.

**Tooling note: **Two small extractor scripts were written during this analysis — one for .ev3 and one for .llsp3 — that turn any graphical project into a readable mission outline. They make the entire library, regardless of format, analyzable as text. They can be reused to fold in any new repositories.

# Control systems survey

Every text-source repository in the corpus was scanned for control-theory constructs — PID terms, Kalman filtering, velocity profiling, and feedforward — and each hit was then read in context to separate real implementations from library calls, comments, and false positives. The summary up front: 

- **PID is rare as hand-written code but ubiquitous as a library call. **Exactly one team wrote a textbook-correct full PID from scratch (ihsboost). One more wrote a full P+I+D line-follower (GO-Robot). Everyone running KIPR hardware inherits a motor-level PID for free through the firmware API, whether they invoke it or not.

- **Kalman filtering: none. **Zero instances across all 26 repositories. This is expected at this level — see the discussion below.

- **Velocity profiling: two real instances. **ihsboost (explicit acceleration controllers, including an S-curve) and GO-Robot (trapezoidal accel/brake keyed to distance). A few others ramp speed crudely.

- **Feedforward: none named explicitly. **No repo computes a feedforward term, though the velocity profiles function as open-loop feedforward in practice.

## Findings by repository

The table classifies each repo by the most advanced control construct it actually implements (not merely references):

| **Repository** | **Closed-loop?** | **Controller type** | **Velocity profile** |
| --- | --- | --- | --- |
| ihsboost (C++) | Yes | Full PID class (P+I+D), trapezoidal integral, dt-scaled derivative | Yes — Linear + Sinusoidal (S-curve) controller classes |
| GO-Robot FLL | Yes | Full P+I+D line-follower; gains recomputed from speed each loop | Yes — trapezoidal accel/brake by distance |
| KIPR-firmware users* | Yes | 6-param motor PID (p/i/d numerator+denominator) via set_pid_gains API | Firmware-internal velocity loop |
| LACT-0636 (C) | Yes | P-only gyro correction (single Kp, threshold bang-bang) | No |
| DRS Create-19/20 | Yes | P-only / stepwise reflectance lookup ('proportional_line_follow') | Crude speed ramp only |
| DRS Lego / other seasons | Mixed | Bang-bang line-following, timed moves | No |
| jbc-norman, Parkside, Perry, SSMS, NoHo | No* | Open-loop timed moves; consume KIPR firmware PID at motor level | No |
| Tyngsborough HS | Partial | Encoder/gyro-aware moves, no explicit PID term | Minor ramp |
| ducc WRO (EV3-G) | Yes | PID line-track inside MyBlocks (graphical) | Acceleration MyBlock (accelSync) |
| WRO 2025 / 2023 (SPIKE) | Yes | Block-based proportional drive + acceleration block | SPIKE movementSetAcceleration block |

*** **Every team on KIPR Wombat/Wallaby hardware (all Botball/JBC repos here) gets a velocity-loop PID inside the motor controller via set_pid_gains(motor, p, i, d, pd, id, dd). Most teams never tune it — but 'are they using PID?' has to be answered yes at the firmware level even when the team's own code is purely open-loop.

## To what extent is PID actually used?

Three distinct layers, and conflating them gives the wrong answer:

- **Firmware PID (everywhere on KIPR): **the motor controller closes a velocity loop on every commanded move. Free, invisible, almost never tuned by students.

- **Hand-written steering PID (rare): **only ihsboost and GO-Robot implement a real multi-term controller in their own code. These are the two repos worth studying for PID pedagogy.

- **Degenerate ****'****PID****'**** (common): **many teams call something a proportional follower that is really a single gain, a threshold, or a lookup table. Worth flagging to students as the gap between naming and implementing.

## PID specification — the two real implementations

**ihsboost** — a continuous-time PID with proper numerical methods. Gains Kp, Ki, Kd passed at construction; integral via trapezoidal rule; derivative divided by the timestep dt = 1/updates_per_second:

PIDController(Kp, Ki, Kd, updates_per_second);  // dt = 1/updates_per_second

void step(double error) {

    error_integral += (past_error + error) * 0.5 * dt;   // trapezoidal I

    cur_speed = Kp*error + Ki*error_integral

              + Kd*(error - past_error)/dt;              // dt-scaled D

    past_error = error;

}

**GO-Robot (FLL)** — a discrete PID for line-following where the error is the color sensor's distance from the edge value (reflected light − 50). Distinctive feature: the gains are not constants but are **recomputed from the current speed on every iteration**, so fast driving uses gentler correction:

change   = reflected_light - 50                  # error = distance from edge

steering = change*pReglerLight + integral*iReglerLight

         + dReglerLight*(change - old_change)    # full P + I + D

# pReglerLight, dReglerLight are functions of speed, set each loop:

pReglerLight = -0.04*speed + 4.11

dReglerLight =  0.98*speed - 34.2

The KIPR firmware controller, by contrast, is specified as **six short integers** — proportional, integral, and derivative gains each as a numerator/denominator pair — because the embedded controller uses integer fraction math rather than floats: set_pid_gains(motor, p, i, d, pd, id, dd).

## Is anyone doing Kalman filtering?

**No — not a single repository.** There are zero references to Kalman filters, covariance, or state estimation anywhere in the corpus. This is the expected result and is worth stating plainly for the curriculum, because it marks a real ceiling:

- These robots run short (≤ 2 minute), highly structured courses on known fields. Re-zeroing against physical landmarks (the square-up-on-a-line trick) cheaply corrects accumulated error, so the statistical sensor fusion a Kalman filter provides isn't needed to win.

- The sensor suites are simple — reflected light, a gyro, encoders, occasionally a camera. Kalman filtering earns its complexity when you must fuse noisy, redundant sensors continuously (drones, self-driving cars). Notably, the one category that does approach it is **WRO Future Engineers** (autonomous vehicles with continuous camera + odometry), which we deliberately set aside as off-pattern — that is exactly where sensor fusion would start to appear.

- Pedagogically: Kalman filtering is a reasonable **capstone / stretch topic**, not part of the core ladder. A student who has mastered PID line-following and gyro-corrected turns has the prerequisites; the mat games themselves never force the lesson.

## Who is using velocity profiles?

Two repositories implement genuine velocity profiling; the rest either ramp speed crudely or not at all.

**ihsboost** provides an AccelerateController base class with two profile shapes as subclasses:

- LinearController — constant acceleration (trapezoidal velocity profile): speed rises linearly from from_speed to to_speed.

- SinusoidalController — an S-curve profile using a sine easing function, which limits jerk (the rate of change of acceleration) for smoother starts and stops:

cur_speed = from_speed + delta_speed * sin(num_steps/total * PI/2);

**GO-Robot (FLL)** implements a trapezoidal profile keyed to distance traveled rather than time: it accelerates over the first portion of the move, cruises at max speed, then brakes over the final portion toward an end speed. Acceleration and braking fractions are tunable per call:

addSpeedPerDegree = (maxspeed - startspeed) / accelerateDistance

subSpeedPerDegree = (maxspeed - endspeed)  / deccelerateDistance

if drivenDistance > brakeStartValue:  speed -= subSpeedPerDegree*step  # brake

elif speed < maxspeed:                speed += addSpeedPerDegree*step  # accel

Dead Robot Society's later seasons add a crude linear ramp on some moves, but nothing parameterized like the two above. No repo implements true motion planning (path generation, spline following) — the WRO world-record run achieves its smoothness through a hand-tuned sequence of profiled segments, not a planner.

## What this means for the teaching ladder

The control-systems progression that the corpus actually exhibits, in order of sophistication: **timed open-loop moves → bang-bang / threshold control → single-gain proportional → full PID → PID with velocity profiling → (capstone) sensor fusion / Kalman.** The corpus is dense at the bottom three rungs, thin at full PID (two teams), thinner at profiling (two teams), and empty at fusion. That emptiness is the opportunity: a program that teaches clean PID and trapezoidal profiling would put students ahead of nearly every team surveyed, and Kalman filtering remains available as a genuine stretch goal for the strongest students.

# Complete repository list

All 26 repositories in the analyzed corpus, grouped by team. These are public student/team repositories; they are cited here for structural analysis and teaching reference. Per several teams' own stated wishes, code should be studied for technique, not copied into a competing team's robot.

| **Repository (team / season)** | **League** | **Format** | **URL** |
| --- | --- | --- | --- |
| Dead Robot Society — Create-19 | Botball | Python | github.com/deadrobots/Create-19 |
| Dead Robot Society — Create-20 | Botball | Python | github.com/deadrobots/Create-20 |
| Dead Robot Society — Create-18 | Botball | Python | github.com/deadrobots/Create-18 |
| Dead Robot Society — Create-17 | Botball | Python | github.com/deadrobots/Create-17 |
| Dead Robot Society — Lego-20 | Botball | Python | github.com/deadrobots/Lego-20 |
| Dead Robot Society — Lego-19 | Botball | Python | github.com/deadrobots/Lego-19 |
| Dead Robot Society — Lego-18 | Botball | Python | github.com/deadrobots/Lego-18 |
| Dead Robot Society — Lego-17 | Botball | Python | github.com/deadrobots/Lego-17 |
| Dead Robot Society — BoVot-17 | Botball | Python | github.com/deadrobots/BoVot-17 |
| Dead Robot Society — StackOverBot-17 | Botball | Python | github.com/deadrobots/StackOverBot-17 |
| Dead Robot Society — motorsPlusPlus | Botball | Python | github.com/deadrobots/motorsPlusPlus |
| IHS Robotics — ihsboost library | Botball | C++ | github.com/ihsrobotics/ihsboost |
| Norman JBC — 2020 | Jr. Botball | C + Python | github.com/wibeasley/cms-norman-jbc-2020 |
| Norman JBC — 2016 | Jr. Botball | C + Python | github.com/wibeasley/cms-norman-jbc-2016 |
| LACT Botball 0636 — 2017 | Botball | C | github.com/LACT-Botball-0636/Botball-2017 |
| Tyngsborough HS — botball-2019 | Botball | Python | github.com/tyngsboroughrobotics/botball-2019 |
| Tyngsborough HS — game-2020 | Botball | Python | github.com/tyngsboroughrobotics/game-2020 |
| Tyngsborough HS — 'Botball for Python' | Botball | Python | github.com/tyngsboroughrobotics/botball |
| Parkside Robotics — 2018 | Botball | C | github.com/ParksideRobotics/Botball-2018-Program |
| Perry Robotics Team 2 — 2023 | Botball | C | github.com/perryrobotics/2023-Team-2-Create-Robot |
| SSMS Botball 7 | Botball | C | github.com/Sailedout/ssms-botball-7 |
| NoHo Botball — 2014 | Botball | C | github.com/NoHoBotball/Botball2014 |
| GO-Robot — Python for SPIKE Prime | FLL | Python | github.com/GO-Robot-FLL/Python-for-Spike-Prime |
| ducc. — WRO 2023 (world record) | WRO | EV3-G | github.com/8076ducc/wro-2023 |
| WRO 2025 RoboMission (SPIKE) | WRO | SPIKE | github.com/THEGABOALE/WRO-2025-RoboMission-Spike-Prime |
| WRO 2023 RoboMission junior | WRO | SPIKE | github.com/Apress/WRO-2023-Robomission-junior |

**Discovery method: **repositories were found through GitHub topic pages (botball, fll, wro), keyword search, and enumeration of prolific team organizations. WRO Future Engineers (autonomous-vehicle) repositories were intentionally excluded from the core set because their game type — continuous camera-based driving rather than line-follow / color / gripper mat missions — falls outside the pattern under study. They remain the place to look for the sensor-fusion techniques absent from this corpus.

# Mission primitives: designing a language from the evidence

The question is not 'what primitives would be elegant?' but 'what primitives have student teams already converged on, independently, across leagues and languages?' The answer is recoverable, because **the function libraries the teams wrote are their implicit vocabularies.** Every Python def, every C function, every EV3 MyBlock and SPIKE procedure is a word a team needed often enough to name. Clustering those names across the corpus gives an empirical primitive set.

## Method

Every named function, MyBlock, and procedure was extracted from 16 teams' code (the text repos plus the EV3 and SPIKE graphical projects), normalized to lowercase, and sorted into semantic concepts. Each concept was then scored by **how many independent teams exhibit it** — team coverage, not raw frequency, so one verbose team can't skew the result. A concept used by many teams who never saw each other's code is, by definition, a primitive of the domain.

## The empirical primitive set (ranked by team coverage)

| **Concept** | **Teams** | **Tier** |
| --- | --- | --- |
| Drive forward / backward (timed or by distance) | 14 / 16 | Core motion |
| Turn / rotate / spin (by angle or time) | 14 / 16 | Core motion |
| Open / close gripper (claw) | 11 / 16 | Core effector |
| Calibrate sensors / gyro / reset | 11 / 16 | Setup |
| Line follow | 10 / 16 | Core motion |
| Move servo (generic, to a position) | 10 / 16 | Core effector |
| Travel-to named location (navigation verb) | 10 / 16 | Composite |
| Square up / align on a line | 9 / 16 | Core motion |
| Raise / lower arm | 9 / 16 | Core effector |
| Read color / detect object (vision) | 9 / 16 | Sensing |
| Shutdown / end run | 9 / 16 | Lifecycle |
| Drive until condition (sensor stop) | 8 / 16 | Core motion |
| Pivot / arc on one wheel | 7 / 16 | Core motion |
| Wait for start (light / button) | 6 / 16* | Lifecycle |

*** **undercounted: many teams use the KIPR built-in wait_for_light() directly rather than wrapping it in a named function, so it doesn't appear in their vocabulary even though every autonomous run begins with it. The lifecycle primitives are universal in practice.

## The key structural discovery: a move is a motion + a stop condition

Two teams, working independently in different languages, arrived at the same non-obvious abstraction. GO-Robot (FLL, Python) built a family of stopMethod objects — stopLine, stopAlign, stopTangens, stopDegree, stopTime, stopResistance — any of which can be handed to any motion function to tell it when to quit. Dead Robot Society (Botball, Python) built the same thing as predicate functions passed to drive_condition(): on_black, bumped, hit_wall, black_left_or_right.

This convergence is the most important finding for language design. It says the natural grammar of a mission is not drive(30cm) but **verb + magnitude + until-condition**: 'drive forward, up to 30 cm, **until** you see a line.' The termination condition is a first-class concept, not an afterthought — because on a real field, sensor landmarks are more reliable than dead-reckoned distances.

## Three tiers, not one flat list

The extracted vocabulary separates cleanly into three layers. A language for these missions wants all three, because teams clearly think in all three.

**Tier 1 — Primitives (the verbs). **Atomic robot actions with a magnitude and an optional stop condition. Universal across teams.

- drive — forward/back, by distance or time, at a speed

- turn — by angle (gyro) or time, on-spot or pivot/arc

- follow_line — along an edge, until a stop condition

- square_up — align both sensors on a line (re-zero heading)

- grip / release and arm_to / servo_to — effectors to a named position

**Tier 2 — Stop conditions (the ****'****until****'**** clause). **Composable terminators, used by both convergent teams.

- until_distance, until_time, until_line, until_aligned, until_stalled, until_color

**Tier 3 — Mission tasks (the sentences). **Named compositions of primitives plus a target object/location. These are what a team's main() actually calls — e.g. DRS's grab_water_cube, head_to_elec_lines, drop_botguy, or the WRO run's collectContainers, fuelBigShip, moorRobot. A mission language should let users define these from primitives, exactly as the teams do.

## A proposed fourth-style language: “MissionScript”

Synthesizing the evidence: a task-oriented language where a program is a sequence of mission tasks, each task is a sequence of primitive moves, and every move can carry an until clause. It reads like the DRS main() but with the stop-condition abstraction promoted into the syntax. A sketch:

robot:

    drive_motors  = ports B, C        # the chassis pair

    claw = servo 1 ;  arm = servo 3   # named effectors

    line_left = color 2 ; line_right = color 4

 

calibrate gyro

on start_light:                       # lifecycle: wait for the gate

 

task get_water_cube:

    drive forward 40cm until line          # approach, stop on landmark

    square_up on line                      # re-zero heading

    turn -90deg

    drive forward until bump               # close in until contact

    arm to down

    grip                                   # close claw

    arm to carry

 

task deliver to zone_color:

    follow_line right until color == zone_color

    arm to low

    release

 

mission:                                   # the top-level sentence

    get_water_cube

    deliver to RED

    end_run                                # kill motors, stop timer

Everything in that sketch maps to something a real team already wrote. drive forward 40cm until line is DRS's drive_condition(on_black, speed) with a distance cap; square_up on line is their drive_to_black_and_square_up; grip / release / arm to are the universal move_servo(servo, position) form; the task / mission blocks are the Tier-3 composite layer every team builds by hand.

## What the language would deliberately leave out

The corpus is as informative about absences as presences. The following are intentionally not primitives:

- **PID gains and control math. **Hidden inside the primitives. A user says drive forward until line; the runtime owns the controller. Only ihsboost and GO-Robot expose tuning, and they are the exception.

- **Explicit motor commands. **No set_motor_power(left, right) at the mission level — that is the layer below, the one the language compiles down to.

- **Loops and general computation, mostly. **Mission scripts are overwhelmingly linear sequences with occasional branch-on-sensed-state. The language needs if color == ... branching (every team does this) but does not need to be a general-purpose language. Keeping it small is the point.

## Why this is the right shape for teaching

A task-oriented language with an explicit until clause front-loads the single most important concept a beginner must learn — **that robots act on sensed conditions, not blind timing** — and makes the open-loop-to-closed-loop leap a matter of syntax rather than a buried design decision. A student writes drive forward until line on day one and has already internalized the lesson that took several teams in this corpus multiple seasons to adopt consistently. The three-tier structure also gives a natural growth path: start by composing existing primitives into tasks, then later open up the primitives themselves (the PID, the velocity profile) for students ready to go deeper — which is exactly the progression the corpus exhibits from LACT's timed moves up to ihsboost's controller library.

Competition Robot Code Analysis  —  page
