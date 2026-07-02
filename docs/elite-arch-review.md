# Review — The Elite & League Architectures wiki (`docs/elite-arch/`)

*Full-book editorial and technical review, July 2026. All 49 files read; corpus statistics
cross-checked against `knowledge/`; all internal links machine-checked (0 broken file targets).
Citations are `file:approx-line`.*

## Overall assessment

The book is in better shape than most drafts at this stage. The spine works: baseline → views →
seams → practices → anatomy → proposal → measurement. The best material is unusual for FRC
writing — the statistical self-deflation ("10/55 have all three seams," "almost everyone builds
the seam, almost no one collects the dividend"), the outlier-first reporting in ch. 34, and the
quantified golden rule (mechanical vs confirmed scoring: 0.29 → 0.53). Those earn trust and
should not be touched.

The problems cluster into five themes, in priority order: **(1)** residue from a renumbering that
left wrong chapter numbers in prose all over Part II; **(2)** unreconciled corpus denominators
(37 / 55 / 63 / 24 / 232 team-years) that make correct numbers look like contradictions;
**(3)** causal overclaiming in the front matter that the book's own evidence section quietly
refutes; **(4)** four load-bearing holes in the Part III proposal that ch. 32 doesn't list;
**(5)** heavy unmarked duplication, especially Appendix A vs chs. 33–34.

---

## Theme 1 — Renumbering residue (mechanical, do first)

The Part I chapters were renumbered at some point (old 5→3, 6→4, 7→5, 8→6, 14→8) and Part II
prose still uses the old numbers. Link *targets* are all correct; only the visible text is wrong:

| Location | Says | Should say |
|---|---|---|
| `part-2/16:8` | "Part I, chapter 5" → io-seam | ch. 3 |
| `part-2/17:10` | "Part I ch.5, the IO seam" | ch. 3 |
| `part-2/18:10` | "Chapter 5" | ch. 3 |
| `part-2/19:6,10` | "Part I, chapter 8" → drivetrain (×2) | ch. 6 |
| `part-2/20:10` | "Part I chapter 6" → state-seam | ch. 4 |
| `part-2/21:8,131` | "chapter 6" → state-seam (×2) | ch. 4 |
| `part-2/22:10` | "chapter 7" → coordination-seam | ch. 5 |
| `part-2/23:8` | "Chapter 7" and "chapter 14" | ch. 5, ch. 8 |

Related residue:

- `part-1/09:6` — "belong to [ch. 23 link] **in Part I**": the link goes to Part II, and the
  in-part alternatives chapter is ch. 8. Broken sentence; rewrite.
- `_index.md:36` — "Read Part I straight through (ch. 1 → 8)": Part I has 9 chapters.
- `scoring/34:7` — "This **appendix** is the receipt": it's a Part IV chapter now.
- `scoring/35:7` — link text "[D1–D8 rubric]" targets `34-the-san-diego-scoresheet.md`; should
  target `33-the-rubric.md`.
- Chapters 10–14 and section letter E don't exist (absorbed into Appendix A). Either renumber or
  add one visible sentence in "How to read it" saying the gap is intentional — first-time readers
  will assume missing pages.
- Name drift: "How We **Develop** This" (`_index:38`, Appendix A title) vs "How We **Developed**
  This" (part-1 index, ch. 1) vs directory `how-we-developed-this`. Pick one.
- Stale "next chapter" chains in the appendices from the old linear order:
  `how-we-developed-this/02:79` ("next section" → Part I ch. 2), `05:76` ("next chapter" →
  lessons-from-outside), `lessons-from-outside/01:72` ("next chapter" → Part I ch. 8). Replace
  "next" with explicit pointers.
- `lessons-from-outside/02:34` — "record-and-replay" links to part-1 ch. 3; the subject lives in
  ch. 7. Retarget.

## Theme 2 — Denominator chaos

The book draws on at least five samples — the 37-team hand survey, the 55-repo season index, the
63-team/684-repo full clone, the 24-team San Diego scoresheet, and 232 team-years for
cross-validation — and never says so in one place. The result is that *correct* numbers read as
contradictions:

- `part-1/03:5` "roughly two-thirds" (37-team survey) vs `part-1/03:75` "24 of 55" (44%) — same
  chapter, no reconciliation.
- `part-2/16` "24 teams" vs `part-2/17:42` "27 teams … of 63" for the same IO-seam pattern.
- `part-2/22:56` "22 Superstructures / 12 state machines" (55-repo index, but misattributed to
  "the survey of 37 teams") vs `part-2/23:82` "28 coordinators / 17 FSMs" (any-kind counts).
- `part-2/17:32,34` — `setControl` "2,620 occurrences" and "797 times" two lines apart (raw grep
  vs parsed-call index, unexplained).
- `scoring/33:57` ρ≈0.53 on 232 team-years / 55 teams vs `scoring/34:50` ρ=0.55 on 24 SD teams —
  two validation studies, neither mentions the other. And ch. 33's own scoring unit is "one repo
  per team," which can't produce 232 team-years without explanation.
- `part-3/27:84` introduces "683 repos" cold.

**Fix:** one "samples at a glance" box (Appendix A ch. 1 is the natural home, with a short
version in `part-2/_index.md`), then attach a denominator to every count. This is the single
highest-leverage credibility fix in the book.

Specific count conflicts to resolve while doing it:

- **Patribots 2025: Σ 19.5 / D2 2.5 in `34:24` vs Σ 20.0 / D2 3 in `35:16`** — both `_index`
  blurbs use 20.0. If full-history scoring justified the bump, say so in one sentence in ch. 35
  and footnote ch. 34's table; at 20.0, 4738 ties for #1 in ch. 34's ranking.
- State-graph exemplars: ch. 5 says "6328, 254"; ch. 8 says "254 is the one full instance"; the
  source lists ~5 teams (190, 254, 2910, 3476, 5026) *without* 6328; `part-2/23` headlines 6328
  as a worked example while its own table omits it. Pick a canonical claim and use it everywhere.
- `part-2/17:48` names six reusable-MotorIO teams incl. 2706; `17:571` lists ~10 and omits 2706.
- `part-2/19` puts 254 in both the per-module camp (line 66) and the per-drivetrain camp
  (lines 144, 214–229). If 254 changed between seasons, season-tag every attribution — it would
  actually strengthen the "two altitudes" argument.
- `scoring/34:93` — "2025/2026-only cut (n = 20)" but the table has 18 such rows.

## Theme 3 — Overclaiming the evidence

The book's most honest passage (`how-we-developed-this/04:54-60`) reports that program size +
maturity alone predict EPA at ≈0.60 — better than the rubric's 0.55 — and that the within-team
correlation collapses to ≈0.05. That's close to a null result for "better code causes better
results," and the front matter doesn't survive it:

- `_index.md:8,49` — "**validated** against competition results," "checked against who actually
  wins." Change to "checked against competition results (moderate correlation, heavily
  confounded by program maturity — ch. 34)."
- `scoring/34:97` — "the machinery that **makes** D6 and D7 cheap … **makes** D8 a byproduct" is
  a causal claim the correlational data can't carry, with counterexample 3647 three paragraphs
  up. Soften to "is designed to make."
- `scoring/35` + both `_index` blurbs — "two rules it **proves**." One team selected on the
  outcome illustrates; it doesn't prove. Also the headline "monotonic climb 5.0 → 10.0 → 17.5 →
  20.0" keeps the offseason-rebuild 17.5 that the chapter itself corrects to "~12 in-season."
  Footnote the sequence or show both series.
- `part-2/23:14` — wanted/current FSM "universal among serious teams": the marker hits 2 teams.
  Soften.
- Missing caveats in ch. 34: no CIs at n=24 (the per-dimension *ranking* D8 0.60 vs D3 0.17 is
  the chapter's centerpiece and is not stable at that n); unblinded scoring (the LLM
  agent-confirmed pass knew team identities — this can inflate the confirmed-vs-mechanical gap
  that is the book's headline argument); selection on public repos. One caveat sentence each.
- `part-3/31:5` — "the **proof** the factoring is right" (ROS mapping) is proof by analogy, and
  the mapping hides real mismatches (async many-to-many QoS topics vs synchronous 1:1 calls;
  action-goal handshake vs a re-sent 20 ms command). Soften and add a short "what does *not*
  map" paragraph.

Keep the honesty that already exists — the confound section, ch. 34's outlier-first structure,
ch. 35's "~12 in-season" correction — and propagate it upward instead of diluting it.

## Theme 4 — Part III's unlisted load-bearing problems

Ch. 32's candor is the part's greatest asset, but its two "load-bearing open questions" are not
the biggest ones. Four issues are more structural, and one of its own answers looks wrong:

1. **`State` vs hidden memory.** `25:14` defines `update` as a fold over `State`, but `25:21`
   defines `State` as what the block *exposes*. Real blocks carry hidden memory (PID
   integrators, profile progress, debounce timers). If that memory isn't in `State`, `update`
   isn't a pure function of the logged channels and ch. 29's "bit-identical replay" claim fails
   for any block replayed mid-stream. Either split `State` (exposed) from `Memory` (internal,
   folded), or state the honest contract: replay is valid from tick 0 of a complete log with
   deterministic code — which is AdvantageKit's actual model.
2. **Time is missing from the contract.** No timestamp/dt in `update(Command_in, Observations)`.
   Profiles, PID, and debounce need it; a block that reads the FPGA clock inside `update`
   silently breaks purity and replay. Make the tick time part of `Observations` and elevate
   "no wall-clock reads inside `update`" to a named rule.
3. **The two-pass order looks inverted.** `32:34` commits to command pass first, then state pass,
   and claims this avoids one-tick lag — but commands consuming last tick's state *is* the lag,
   and the Elite loop the book documents (read → log → decide → actuate) runs state first.
   Reverse it or justify it against Part I's own loop.
4. **The `Observations` channel holds three positions at once.** `25:38` settles it (children's
   `State`), `25:55` puts observations in the estimator's `Cmd in` column, `28:15` assigns them
   to `Command_in`, and `32:15` reopens it as the #1 open question. Decide once, fix the ch. 25
   table and ch. 28 bullets, record it in ch. 32 as decided-with-rationale.
5. **Unlisted engineering constraints:** protobuf-java allocation/GC on the RIO (WPILib chose
   QuickBuffers for exactly this; say whether proto types are in-loop PODs or only the log/wire
   form — `26:114`, `31:69`); threading (the 250 Hz odometry thread in `27:120` mutates an
   inputs struct a "pure" update snapshots — who synchronizes, what does replay record?);
   command-based integration beyond the periodic wrap (how `Trigger` bindings and PathPlanner
   `Command`s become the executive's `Command_in`; operator overrides mid-sequence).

Smaller Part III accuracy fixes: `oneof` enforces *at most* one, not exactly one (`26:33`);
`[(unit)="V"]` needs a declared FieldOptions extension to compile (`26:35`); the six-state
lifecycle is an *adaptation* of ROS 2 managed nodes, not "straight from" them — ROS has no
persistent fault state (`30:14`); upstream `ros2_controllers` ships no swerve controller
(`27:131`, `31:27`); AdvantageKit has no symmetric `Outputs` POD convention (`26:19`); "five
write verbs" lists four (`27:45`); Phoenix 6 2025 split `ApplyChassisSpeeds` into
`ApplyRobotSpeeds`/`ApplyFieldSpeeds` — note the drift so readers don't grep for a removed class
(`27:88`).

Pedagogically, Part III is a manifesto with two spec'd leaves. The single highest-value addition:
**one complete worked Elevator block in Java** — `Config`/`Command`/`State` records, the `update`
body, the `Subsystem` wrap, the `RobotContainer` wiring. Second: specify the logging harness the
"for free" claim rides on (how PODs reach a `.wpilog`). Third: show ch. 29's claimed "three-line
test" as actual code, and sketch the `TunerConstants → ModuleConstants` adapter ch. 32 itself
calls the most concrete unbuilt artifact.

## Theme 5 — Duplication

Declared Part I ↔ Part II overlap is fine and working. Undeclared same-depth duplication is not:

- **Appendix A chs. 2 and 4 vs chs. 33–34** — same "why dimensions" argument nearly verbatim
  (including the identical quote), same eight-row table, same outlier paragraphs. Make Appendix A
  genuinely why-shaped (instrument history, design rationale) and cut every table chs. 33–34 own.
- The IO quartet is fully defined three times (`15:74`, `16:281`, `18:29` — the last two with
  identical naming bullets). Home it in ch. 16; others link.
- The vendor-confinement ethic: `16:344` and `18:49` ("stated once" is ironically its second full
  statement). Canonical in ch. 16.
- The loop-above/below table appears verbatim in `15:166` and `16:147`. Keep ch. 16's.
- The D7 ladder appears three times (part-1/04, part-2/20, part-2/21); keep ch. 21's full 0–4
  table, reduce the others to pointers. Same for the D2 ladder (part-1/05, part-2/22) and the
  three renderings of the coordination ladder (22 §6, 23 lede, 23 close — keep the close).
- The 1678 MotionPlanner passage is near-verbatim in both `22:198` and `23:132`; keep ch. 23's.
- "Code is quoted to study the technique, not to copy" appears six times across Part II; once in
  the part index is enough.
- The estimate/status + "every level is named `…State`" argument: `25:100` and `28:87` in nearly
  the same words. The "a name must survive a change of reader" line appears in three consecutive
  chapters (25, 26, 27).
- ch. 3 and ch. 7 repeat the 24-IO/zero-exceptions/one-replay triple nearly verbatim; "build the
  seams, defer the payoffs" is fully stated three times in Part I.

## Code-level errors (will burn a reader)

1. **`FlywheelSim` 2024 constructor** in the velocity archetype's copy-me template
   (`part-2/18:399`) — removed in WPILib 2025; a 2026 student hits a compile error. Ch. 16's
   Kotlin snippet already uses the new signature; the book shows both forms without comment.
2. **Ch. 15's Superstructure switch can't sequence** (`15:205`): three synchronous `setGoal`
   calls in one tick, the last overwriting the first — contradicting the chapter's own prose,
   which describes `Commands.sequence(...)` + `waitUntil(...)` but never shows it. This is the
   single most build-critical gap in Part II: show the working interlock as code.
3. **`estimateCoprocMultiTagPose` is not a PhotonLib API** (`part-2/21:104`; inherited from
   `knowledge/.../05-vision-sensor.md`). The real API is `PhotonPoseEstimator.update()` with
   `PoseStrategy.MULTI_TAG_PNP_ON_COPROCESSOR`. If it's 3061's wrapper, label it.
4. **`PhotonCameraSim` attributed to WPILib** (`21:118`) — it's PhotonLib's.
5. **Dijkstra contradiction on one screen** (`part-2/23:86,112`): the table says Dijkstra = 0
   teams; the 6328 snippet ten lines later calls `DijkstraShortestPath`. 6328's shipped code
   walks the graph with BFS — fix the snippet or add the one-sentence explanation.
6. **`RemoteCANcoder` described as "fused"** (`18:287`) — fusing is `FusedCANcoder`; the word
   teaches the wrong mental model.
7. **Kalman-gain description half right** (`20:100,109`): the gain compares measurement std-devs
   against the estimator's odometry std-devs; "built from the observation's std-devs" alone has
   no reference point.
8. **Undefined symbols in teaching snippets**: `lastOdometryPose` never assigned and
   `estimateAtTime`/`sampleToOdometryTransform` never computed (`20:76-104`); `appliedVolts`
   field undeclared (`18:409`); arrow-switch with no `default` fails definite assignment
   (`18:425`); `armClearedBeforeElevatorRose` is a magic boolean that *is* the thing the test
   exists to check (`22:203`); `started` undeclared in the BT `CommandRunner` (`23:217`);
   Kotlin fenced as ```` ```java ```` (`16:244`).
9. **`SwerveDriveSim` listed as a WPILib class** in the grep cheat-sheet (`33:126`) — WPILib has
   none; maple-sim's is `SwerveDriveSimulation`.
10. **Team attributions to verify**: "2706 PhantomCatz" appears ~7 times across Part II — the
    PhantomCatz GitHub org is FRC **2637** (2706 is Merge Robotics); the error is inherited from
    the corpus docs, so fix both. And 971 writing Java+Lombok+AdvantageKit (`17:174`) needs a
    footnote ("971's 2026 second-robot Java codebase, not their main C++ stack") after verifying
    the repo.
11. **`addVisionMeasurement` vs `addVisionObservation`** drift within and between chs. 20–21,
    plus `21:133` "RobotState wraps a `SwerveDrivePoseEstimator`" directly contradicting ch. 20's
    featured hand-rolled example. One sentence reconciles both.

## Pedagogy

- **D1–D8 are used before they're defined.** Part I references D7, D2, D3–D5 from ch. 4 onward;
  the rubric lives in Part IV. One sentence + link in ch. 1 or 2 fixes the straight-through read.
- **The "L4" collision**: rubric level L4 and game target `SCORE_L4`/`L4_CORAL` are both live in
  adjacent Part II chapters. Disambiguate at first collision (consider "D7-L4" for rubric levels).
- **SciBorgs' private test utilities presented as standard**: `runUnitTest()`, `fastForward()`,
  `setupTests()` (`18:205`, `18:461`, `19:255`) will resolve to nothing in a fresh project. One
  callout naming them and pointing at where the harness is built.
- **The missing timestamp-epoch warning** (ch. 21): feeding `addVisionMeasurement` a timestamp on
  the wrong clock (NT vs FPGA vs CTRE timesync) is the most common way the fusion silently does
  nothing; the corpus itself notes the `fpgaToCurrentTime` override. One warning box. Related
  one-liners worth adding: ambiguity is a single-tag concept (why multi-tag earns trust);
  MegaTag2 needs gyro seeding and is not a symmetric one-file swap; show one concrete std-dev
  formula (`base * distance² / tagCount`).
- **No reading path for the scoring user.** `_index.md` says "a three-part wiki" yet has a
  Part IV, and none of the four "How to read it" personas routes a mentor who wants to score a
  team. Add the persona: ch. 33 → ch. 34 caveats → ch. 35 as worked example. Also link
  `knowledge/examples/sample-score-output-reefscape2025.md` from ch. 33 or add a one-team worked
  scoring box — it's the one thing missing from an otherwise usable instrument.
- **Ch. 9 is the shape outlier**: 2–3× the length of its Part I siblings, mechanics-grade detail
  (state-space matrices, `BaseStatusSignal.waitForAll`), no diagrams, and it points a descriptive
  chapter at prescriptive Part III chapters ("specializes ch. 29/30"). Compress to ch. 8's
  catalog register or move the mechanics to Part II; delete the surviving editorial aside
  ("could reasonably be folded into…").
- Undefined jargon needing 3-word glosses: Ri3D, MOI, anytime A*, CI, wanted/current (used in
  ch. 5's table, defined in ch. 22), N² transitions.
- Terminology to lock: three role-names for the coordination seam ("coordinator," "planner,"
  "executive") — standardize; `RobotStates` (3128's goal enum) one word from `RobotState` in the
  same chapter (`22:79`) — one-line disambiguation; ch. 19 uses "altitude" for seam granularity
  while chs. 15–18 use loop-above/below for control placement — consider "granularity" in ch. 19;
  goal/setpoint/wanted/target equivalence needs one sentence in ch. 22 §5; leaf blocks dropping
  the `_in` suffix (`Command` vs `Command_in`) is justified but never announced (ch. 26).

## What not to change

The positive/negative-space framing and "the views show you the rooms; the seams show the
load-bearing walls" (ch. 1). The statistical self-deflation throughout Part I. Ch. 16's
location-vs-property distinction and its single diagnostic question. Ch. 18's archetype
organization with its preserved failures (the `@Disabled // "Doesn't work :/"` test). Ch. 19's
verbatim 254/2910 directory listings and "demote `CommandSwerveDrivetrain` to a device."
Ch. 15's "replay intercepts at the log step" — the clearest short AdvantageKit-replay
explanation around. Ch. 23's "the interlock *is* the edge." Ch. 22's 5190 anti-pattern
(a level-1 class wearing a level-3 name). Part III's "emission is a return value, never a side
effect," "a discipline, not a base class," and "keep the semantics, drop the transport."
Ch. 27's "one architecture with two open choices." The confound section of
`04-what-it-predicts.md` and the quantified golden rule in ch. 33. Ch. 32's posture.

## Priority order

1. Theme 1 sweep (stale chapter numbers, mislabeled links, "three-part," ch. 34 "appendix") —
   mechanical, an afternoon.
2. Patribots 19.5-vs-20.0 and the samples-at-a-glance box (Theme 2) — credibility.
3. Code errors 1–5 (FlywheelSim, interlock snippet, PhotonLib APIs, Dijkstra) — reader-burning.
4. Part III: decide `Observations`, add hidden-state/time/allocation/threading to ch. 32, fix or
   justify the two-pass order (Theme 4).
5. Soften "validated"/"proves"/"makes" and add the three missing ch. 34 caveats (Theme 3).
6. De-duplicate Appendix A vs chs. 33–34; quartet/ethic/ladders in Part II (Theme 5).
7. Pedagogy adds: D1–D8 intro sentence, scoring persona + worked example, timestamp warning,
   worked Elevator block in Part III.
8. Verify externally: PhantomCatz = 2637, the 971 Java repo, 254's per-module vs wrapped season,
   setpoint generator in Choreo (`part-1/09:14`), `gg.questnav` coordinates.
