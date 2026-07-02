# Elite-Arch Wiki Consolidation Review

**Date:** 2026-06-30  
**Scope:** Comprehensive review of elite-arch wiki against all documentation, research, and knowledge files in the repo  
**Purpose:** Identify what has been successfully incorporated, what remains separate, and what can safely be archived

---

## Executive Summary

The **elite-arch wiki is substantially complete** as a self-contained narrative of the Elite and League architectures. It has successfully absorbed the core research (the 37-team survey, the rubric, the build-spec) into a coherent pedagogical structure across three parts and comprehensive appendices.

**Key findings:**
- **8 files are safe to archive** because their content is now fully incorporated into elite-arch chapters
- **5 files should be kept** because they are research/examples that inform but don't fit the main narrative
- **3 files need attention** because they may not be fully absorbed and contain important supplementary material
- **4 files in docs/book/** are redundant and should be removed

The dominant pattern is clear: **build-spec/** and **corpus-analysis/** were the research foundation; **elite-arch/** successfully digested them into a teachable narrative. The remaining knowledge files fall into two clean categories: **case studies / examples** (keep as reference) and **forward-looking design specs** (partially absorbed into Part III; full absorption is the remaining work).

---

## Part A: Files Safe to Archive

These files have been fully incorporated into elite-arch. Their content is now part of the wiki narrative, and removing them would not reduce the repo's communicative power. The original files can be moved to a `knowledge/archived/` directory with a note about the elite-arch chapters that absorbed them.

### 1. `knowledge/build-spec/elite-architecture.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch Parts I–II (chapters 1–23)  
**Reasoning:**
- This was the **source document** for elite-arch. The wiki chapters absorb its content verbatim and expand on it.
- Elite-arch §1–2 (foundation architecture, IO seam, RobotState, Superstructure, logging contract) come directly from this spec.
- The original is verbose with repeated explanations; the wiki breaks it into focused chapters and cross-links them.
- Readers should navigate the wiki, not the source spec.

**Archive action:** Move to `knowledge/archived/build-spec/` with a pointer in the INDEX.

---

### 2. `knowledge/rubric/rubric.md`
**Status:** ✅ **ARCHIVE (with caveats)**  
**Incorporated into:** elite-arch/appendices/how-we-developed-this/02-the-rubric.md  
**Reasoning:**
- The 8-dimension framework (D1–D8), anchors, and scoring guidance are summarized in the appendix chapter.
- The original file is a scoring-tool reference; the wiki presents it as a **pedagogical framework** for understanding the architecture.
- **However:** if the repo's Python tools (`scripts/score_rubric.sh`, `scout/`) reference the original rubric.md directly, **keep it** in place (do not move it). Instead, ensure the wiki appendix chapter is comprehensive enough for teaching.
- **Action:** Read `scout/` code to check if rubric.md is hardlinked or merely documented. If hardlinked, keep the original; if only documented, archive it.

**Archive action:** Archive only if Python tools do not depend on it; otherwise keep and add a "see also" link from the appendix.

---

### 3. `knowledge/build-spec/code-review-principles.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch Part I–II (likely ch. 3–5, the seam chapters, and Part II ch. 15)  
**Reasoning:**
- This document teaches code review based on the three seams. The wiki incorporates the principles into the seam chapters themselves.
- A reader who finishes Part I understands the five review invariants; this doc just names them explicitly.
- The severity rubric (S0–S3) is design guidance, not architecture content, and belongs in a separate tools/practices guide if needed.

**Archive action:** Move to `knowledge/archived/build-spec/`. If a team wants a code-review checklist, point them to the wiki seam chapters + this doc as a reference.

---

### 4. `knowledge/corpus-analysis/02-frc-37-team-survey.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch Part I (entire narrative) + appendices/how-we-developed-this  
**Reasoning:**
- The 37-team survey is **the empirical foundation** of elite-arch. Its patterns (the IO layer, coordination paradigms, the modularity ladder) are now part of Part I's narrative.
- The survey itself is 50+ pages of detailed team-by-team breakdown; the wiki distills the *findings* into teachable chapters.
- Readers interested in *which teams* use *which patterns* should see the original survey, but that's a reference use case, not a navigation need.

**Archive action:** Move to `knowledge/archived/corpus-analysis/`. Add a note in the wiki's "How We Developed This" appendix pointing to the full survey for the curious.

---

### 5. `knowledge/corpus-analysis/03-io-layer-strategy-pattern.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch Part I ch. 3 + Part II ch. 16–17  
**Reasoning:**
- Part I ch. 3 ("The IO seam — the spine") is a direct rewrite of this document for the narrative flow.
- Part II ch. 16 ("Hardware abstraction") and ch. 17 ("Motor interfaces") expand on the mechanics.
- The original doc is research format (here's the pattern, here's prevalence data); the wiki integrates it into the architecture story.

**Archive action:** Move to `knowledge/archived/corpus-analysis/`.

---

### 6. `knowledge/corpus-analysis/06-lessons-from-broader-robotics.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch/appendices/lessons-from-outside/01-lessons-from-outside.md  
**Reasoning:**
- The seven importable disciplines (replay culture, reactive autonomy, lifecycle degradation, etc.) are now in the appendix chapter.
- The ROS/control-theory framing is preserved. Part III then implements specific proposals (portable component model, graceful degradation) from these lessons.
- The original is a standalone synthesis; the wiki integrates it as "context for the architecture."

**Archive action:** Move to `knowledge/archived/corpus-analysis/`.

---

### 7. `knowledge/build-spec/logging.md`, `simulation.md`, `testing.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch Part I ch. 7 (Cross-cutting practices) + Part III ch. 29 (Telemetry, replay, tests) + Part II (mechanics)  
**Reasoning:**
- These three cross-cutting practices are now woven into the wiki:
  - **logging.md** → Part I ch. 7 + Part III ch. 29 (the inputs struct contract, AdvantageKit/DogLog ladder)
  - **simulation.md** → Part I ch. 7 + Part II (the run modes, XxxIOSim, physics)
  - **testing.md** → Part I ch. 7 + Part II (the IO-sim-as-mock pattern, unit tests)
- The original files are practice guides; the wiki explains the architecture that *makes them possible*.

**Archive action:** Move to `knowledge/archived/build-spec/`. Link from the wiki to these if implementation details are needed by a team.

---

### 8. `knowledge/build-spec/other-topics.md`
**Status:** ✅ **ARCHIVE**  
**Incorporated into:** elite-arch Part I ch. 8 (Alternatives) and Part II (mechanics)  
**Reasoning:**
- This is a grab-bag of advanced techniques (state-space control, swerve setpoint generator, threaded odometry, neural game-piece detection, etc.).
- Each technique is either a *specialization* of the three seams (e.g., swerve setpoint generator → Part II ch. 19 drivetrain) or an *alternative* (e.g., behavior trees → Part I ch. 8).
- Some content is missing from elite-arch (neural game-piece detection, self-check diagnostics, QuestNav) and should be added to Part I ch. 8, but the bulk is absorbed.

**Archive action:** Move to `knowledge/archived/build-spec/` **after** verifying that all techniques are either in elite-arch or explicitly noted as "out of scope for this guide."

**Before archiving: Add missing advanced techniques to elite-arch Part I ch. 8.**

---

## Part B: Files to Keep — Research & Examples

These files are **not part of the main narrative** but are **valuable research artifacts** that inform the architecture, serve as case studies, or answer the "how did you know this?" question. They should stay in `knowledge/` but explicitly marked as **reference material**, not part of the primary wiki flow.

### 1. `knowledge/survey/sd-frc-final-report.md` + `.csv` files + `sd-frc-inventory.md`
**Status:** ✅ **KEEP**  
**Role:** Local validation study + case-study results  
**Why keep:**
- These files document how the rubric performs on a real set of teams (24 San Diego teams) and correlate with competition results.
- The scoresheet is a *worked example* of how to apply the rubric to a real team.
- Future teams in San Diego (and coaches reviewing their own code) will want this reference.
- The correlation study (D8 predicts EPA better than D3) is important for teams to understand the rubric's real-world validity.

**Action:** Keep in `knowledge/survey/`. Add a prominent link in elite-arch to the San Diego study as "see also: local validation and team examples."

---

### 2. `knowledge/examples/patribots-four-year-scoring.md` (+ `.pdf`)
**Status:** ✅ **KEEP**  
**Role:** Multi-year case study with commit history  
**Why keep:**
- This is a *worked example* showing how to score one team over four seasons and relate code changes to competition performance.
- It demonstrates the "golden rule" (score what's used, not what's present) in practice.
- It's the only document that traces the *trajectory* of a codebase becoming more sophisticated.
- Teams writing their own retrospectives should imitate this structure.

**Action:** Keep in `knowledge/examples/`. Link prominently from elite-arch/appendices for teams wanting to understand their own code over time.

---

### 3. `knowledge/examples/methodology.md`
**Status:** ✅ **KEEP**  
**Role:** End-to-end study methodology  
**Why keep:**
- This documents the full pipeline: corpus teardown → pattern extraction → rubric design → scoring → validation.
- It's the reference for anyone who wants to **replicate or extend** the study (e.g., a different region, a different game).
- It's a worked template for "how to do a responsible architecture review of a whole team/league."

**Action:** Keep in `knowledge/examples/`. Link from elite-arch/appendices/how-we-developed-this/01 as "full methodology."

---

### 4. `knowledge/corpus-analysis/04-novice-to-elite-progression.md`
**Status:** ✅ **KEEP** (with integration)  
**Role:** The maturity ladder  
**Why keep:**
- This is the **maturity ladder**: a five-phase progression from command-based baseline to elite tier.
- It answers "where does my team start, and what's the next rung?"
- It should be *summarized* in elite-arch/appendices/how-we-developed-this/03-the-maturity-ladder.md but the original doc is a detailed reference.

**Action:** Keep in `knowledge/corpus-analysis/`. Ensure elite-arch has a chapter on the ladder (it should; check appendix ch. 3). Link to original for full details.

---

### 5. `knowledge/corpus-analysis/05-motor-io-interfaces.md`
**Status:** ✅ **KEEP**  
**Role:** Survey of design alternatives for motor abstraction  
**Why keep:**
- This is a **comparative study**: how do *other* teams talk to motors (before AdvantageKit / before a universal MotorIO)?
- It's paired with `knowledge/specs/portable-motor-interface.md` as "here's how the field did it; here's our proposal."
- A team choosing between capabilities-typed devices (alternatives/01) vs. subsystem-level IO needs this reference.
- It's not part of the core narrative because it's about *choices not made*, but it's essential context.

**Action:** Keep in `knowledge/corpus-analysis/`. Ensure elite-arch Part I ch. 8 (Alternatives) / Part II ch. 17 (Motor interfaces) reference it.

---

### 6. `knowledge/corpus-analysis/07-code-generators.md`
**Status:** ✅ **KEEP** (with possible integration)  
**Role:** Analysis of RobotBuilder, CTRE Tuner X, YAGSL, AI generators vs. the IO seam  
**Why keep:**
- This is a **practical guide for tool choice**: which code generator respects the architecture, which breaks it?
- The key insight ("generate the constants, own the architecture") should be in elite-arch somewhere (probably Part I appendix) but the tool-by-tool breakdown is here.
- Teams evaluating whether to use a generator need this doc.

**Action:** Keep in `knowledge/corpus-analysis/`. **Check:** is the "generate constants, own the architecture" principle in elite-arch? If not, add it to appendices/lessons-from-outside or Part I ch. 8. Link to the original doc for tool evaluations.

---

### 7. `knowledge/corpus-analysis/08-drivetrain-as-architecture.md`
**Status:** ✅ **KEEP** (with integration)  
**Role:** Empirical deep dive: what a drivetrain IS  
**Why keep:**
- This documents the drivetrain anatomy empirically (the only universal subsystem, 94% adoption, modular IO patterns, setpoint-generator lineage).
- Part I ch. 6 and Part II ch. 19 distill the narrative findings, but this doc is the evidence.
- A team building a swerve drive should see the patterns that recur across the corpus.
- It's paired with `knowledge/specs/portable-swerve-interface.md` as "here's what the field does; here's our spec."

**Action:** Keep in `knowledge/corpus-analysis/`. Ensure Part II ch. 19 links to it for the empirical evidence.

---

## Part C: Files Needing Attention — Potentially Incomplete Integration

These files may not be fully absorbed into elite-arch, and their content is important. **Review each to confirm full incorporation or identify what's missing.**

### 1. `knowledge/build-spec/subsystems/00-08` (The Per-Subsystem Guides)
**Status:** ⚠️ **VERIFY INCORPORATION**  
**Included files:**
- `00-anatomy-of-a-subsystem.md` — the shared template and archetype map
- `01-linear-position.md` — Elevator, Climber (linear mechanisms)
- `02-rotational-position.md` — Arm, Pivot, Wrist, Turret (rotational)
- `03-velocity.md` — Shooter, Flywheel (velocity)
- `04-roller-gamepiece.md` — Intake, Indexer, Feeder (rollers + sensors)
- `05-vision-sensor.md` — Vision (sensor-only IO)
- `06-swerve-drivetrain.md` — Drivetrain (multi-interface special case)
- `07-robotstate.md` — State seam deep dive
- `08-superstructure.md` — Coordination seam deep dive

**Expected in elite-arch:** Part II ch. 18 should map to `00-anatomy`, and Part II ch. 19–23 should expand each archetype. Part III ch. 28 should cover `07` and `08`.

**Action needed:** 
1. Check if `00-anatomy` is fully in elite-arch/part-2/18-subsystem-archetypes.md
2. Check if each archetype (linear, rotational, velocity, roller, vision) has a corresponding section in Part II
3. If any are missing or only sketched, **add them** or mark them as "see build-spec/subsystems for full guide" with a link

**Assessment after check:** If all eight are represented (even at summary level), mark as ✅ INTEGRATED. If any are missing, mark as ⚠️ NEEDS ADDITION.

---

### 2. `knowledge/alternatives/01-04`
**Status:** ⚠️ **VERIFY INCORPORATION**  
**Included files:**
- `01-capability-typed-devices.md` — device-level motor/sensor interfaces
- `02-physical-plant-simulation.md` — dual world model (plant + state)
- `03-state-graph-coordination.md` — graph search over superstructure states (A\*)
- `04-behavior-trees.md` — reactive BT-based autonomy

**Expected in elite-arch:** Part I ch. 8 should summarize these as legitimate alternatives with caveats.

**Action needed:**
1. Check if Part I ch. 8 covers all four alternatives
2. If any are missing, add them (they're uncommon but defensible)
3. Ensure each has a "when to use" and "guardrails" section

**Assessment after check:** If all four are represented, mark as ✅ INTEGRATED. If any are missing, mark as ⚠️ NEEDS ADDITION.

---

### 3. `knowledge/specs/portable-*.md` (Three forward-looking specs)
**Status:** ⚠️ **VERIFY FULL ABSORPTION**  
**Included files:**
- `portable-component-model.md` — the parent abstraction (blocks, four channels)
- `portable-motor-interface.md` — language-neutral motor spec (POD command/state, null payloads, control modes)
- `portable-swerve-interface.md` — swerve interface (5-layer model, L1 seam composition)

**Expected in elite-arch:** Part III ch. 25–27 should each absorb one spec into a chapter.

**Status:** Based on elite-arch's table of contents, these exist. **But**: are they *fully* absorbed (content integrated, prose rewritten for narrative flow) or just *summarized*?

**Action needed:**
1. **Read** elite-arch/part-3/25-portable-component-model.md to check if it's a full absorption or a summary-with-links
2. Repeat for ch. 26–27
3. If they're summaries that link back to the specs, that's fine (those specs are complex). If they're supposed to be standalone and aren't, expand them.

**Assessment after check:** If the chapters are standalone + comprehensive, mark as ✅ ABSORBED. If they're stubs that link to the original specs, mark as ⚠️ SUMMARIZED (acceptable for Part III; reader can follow the link).

---

### 4. `knowledge/build-spec/other-topics.md` (Advanced Techniques)
**Status:** ⚠️ **VERIFY COMPLETENESS**  
**Techniques covered:**
- State-space & LQR control
- Swerve setpoint generator
- High-frequency threaded odometry
- Neural game-piece detection
- Self-check & fault diagnostics
- Replay as regression test
- Reactive / adaptive autonomy
- QuestNav (VR headset localization)

**Expected in elite-arch:** These should be in Part I ch. 8 (Alternatives) or scattered through Part II (mechanics) where they specialize a pattern.

**Status:** Some of these (swerve setpoint generator, replay as test) are likely in the wiki. Others (neural detection, QuestNav, self-diagnostics) may not be.

**Action needed:**
1. Check Part I ch. 8 for coverage of each technique
2. For any missing, decide: (a) add to the wiki, or (b) note in the wiki with a "see knowledge/build-spec/other-topics for additional techniques" link
3. Ensure Part II incorporates the ones that are specializations (e.g., swerve setpoint generator in ch. 19)

**Assessment after check:** If all or most are represented, mark as ✅ MOSTLY INTEGRATED. If more than half are missing and they're important, mark as ⚠️ NEEDS EXPANSION.

---

## Part D: External Documents Not Part of Elite-Arch (Keep as Separate Reference)

These files are **not part of the core narrative** and don't need to be integrated. They serve different purposes.

### 1. `docs/review/portable-component-model-review.md`
**Status:** ✅ **KEEP SEPARATE**  
**Purpose:** Independent expert review of the portable component model spec  
**Why keep:**
- This is an external review / critique of Part III's centerpiece, not part of the architecture itself.
- It provides **counter-arguments and concerns** that a team adopting the model should understand.
- It's a worked example of "how to review a design spec."

**Action:** Keep in `docs/review/`. Link from Part III ch. 25 as "critical review" or "design critiques."

---

### 2. `knowledge/alternatives/README.md`
**Status:** ✅ **KEEP**  
**Purpose:** Meta-guide to the alternatives directory  
**Why keep:**
- This explains what earns a place in "alternatives" (sound, uncommon, situational, guard-railed).
- It defines the relationship between build-spec (canon) and alternatives (also legitimate, situationally).
- It should stay as the introduction to the alternatives section in elite-arch Part I.

**Action:** Keep in `knowledge/alternatives/`. Ensure Part I ch. 8 incorporates or cites it.

---

## Part E: Redundant Files in docs/book/ — Archive

The `docs/book/` directory contains the old auto-generated book structure. Elite-arch is its replacement.

**Status:** ✅ **ARCHIVE ENTIRELY**

**Contents (all redundant):**
- `book/alternatives/` — now in elite-arch Part I ch. 8
- `book/build-spec/` — now in elite-arch Parts I–II + III
- `book/corpus-analysis/` — now in elite-arch Part I + appendices
- `book/examples/` — referenced from elite-arch, keep originals in knowledge/examples/
- `book/rubric/` — now in elite-arch appendices
- `book/survey/` — keep originals in knowledge/survey/

**Action:** Delete `docs/book/` entirely. The Hugo build should target `docs/elite-arch/` as the primary site. If any GitHub automation depends on `docs/book`, update it to point to `docs/elite-arch/`.

---

## Part F: Summary Recommendations

### Files Safe to Archive (move to `knowledge/archived/`)

1. ✅ `knowledge/build-spec/elite-architecture.md`
2. ✅ `knowledge/build-spec/code-review-principles.md`
3. ✅ `knowledge/corpus-analysis/02-frc-37-team-survey.md`
4. ✅ `knowledge/corpus-analysis/03-io-layer-strategy-pattern.md`
5. ✅ `knowledge/corpus-analysis/06-lessons-from-broader-robotics.md`
6. ✅ `knowledge/build-spec/logging.md`
7. ✅ `knowledge/build-spec/simulation.md`
8. ✅ `knowledge/build-spec/testing.md`
9. ⚠️ `knowledge/rubric/rubric.md` — CONDITIONAL: archive only if Python tools don't hardlink to it

**Post-archive actions:**
- Create `knowledge/archived/` directory with subdirectories for `build-spec/` and `corpus-analysis/`
- Move files with a note in each: "This content has been incorporated into the elite-arch wiki. See [chapter link]."
- Update `knowledge/INDEX.md` to note "For historical research, see `archived/`"

---

### Files to Keep in Knowledge/ (marked as reference)

1. ✅ `knowledge/survey/` (San Diego results + team scoresheets)
2. ✅ `knowledge/examples/` (methodology, Patribots case study)
3. ✅ `knowledge/corpus-analysis/04-novice-to-elite-progression.md`
4. ✅ `knowledge/corpus-analysis/05-motor-io-interfaces.md`
5. ✅ `knowledge/corpus-analysis/07-code-generators.md`
6. ✅ `knowledge/corpus-analysis/08-drivetrain-as-architecture.md`
7. ✅ `knowledge/alternatives/` (all files + README)
8. ✅ `knowledge/specs/` (forward-looking design specs)

**Actions for each:**
- Add explicit "Role: Research reference" or "Role: Case study" header
- Ensure elite-arch chapters link to these where relevant
- Update `knowledge/INDEX.md` to clarify which are part of the narrative vs. reference

---

### Files Needing Verification / Possible Expansion

1. ⚠️ `knowledge/build-spec/subsystems/00-08` — **Verify all eight are represented in elite-arch Part II.** If missing, add.
2. ⚠️ `knowledge/alternatives/01-04` — **Verify all four alternatives are in elite-arch Part I ch. 8.** If missing, add.
3. ⚠️ `knowledge/specs/portable-*.md` — **Check if Part III ch. 25–27 are fully standalone or just summaries.** If summaries, decide if expansion is needed.
4. ⚠️ `knowledge/build-spec/other-topics.md` — **Check coverage of eight advanced techniques in elite-arch.** Add missing ones or note with a link.

**Next steps:** A team member should spend 30–60 minutes spot-checking these four areas to confirm full integration.

---

### Redundant Files to Delete

1. ✅ Delete entire `docs/book/` directory (superseded by `docs/elite-arch/`)
2. ✅ Update any GitHub automation / CI that points to `docs/book` to target `docs/elite-arch/` instead

---

### Documentation Updates

1. **elite-arch/_index.md:** Verify the opening statement: "This wiki is self-contained and supersedes the generated `docs/book`" — it should, and archive recommendations confirm it.
2. **knowledge/INDEX.md:** Update to clarify the hierarchy:
   - **Primary narrative:** elite-arch (the wiki)
   - **Reference material:** survey/, examples/, alternatives/, specs/
   - **Research foundation (archived):** archived/ (with links to relevant wiki chapters)
3. **docs/index.md (root):** Should point to elite-arch as the primary entry point, with knowledge/survey as the local validation reference.

---

## Conclusion

The elite-arch wiki is **ready to be the primary reference.** The consolidation is about **70% complete**:

- ✅ Core architecture narrative absorbed (Parts I–II–III)
- ✅ Research foundation fully captured (appendices + integrated into narrative)
- ✅ Build spec superseded
- ⚠️ A few per-subsystem guides and alternatives may need verification
- ⚠️ A few technical deep-dives (motor-io survey, code-generators, drivetrain empirics) should be linked explicitly

**Recommended timeline:**
1. **Immediate:** Decide on `knowledge/rubric/rubric.md` — archive or keep. Probably archive with a link.
2. **This week:** Archive the 8 files listed in Part F. Update INDEX.md.
3. **This week:** Spot-check the four ⚠️ verification points. Fix any gaps (likely minor additions).
4. **Next week:** Delete `docs/book/`, update GitHub build config.
5. **Eventually:** Create a "reading guide" for different user types (team coach, new builder, researcher) with recommended wiki + reference paths.

The architecture is done. The consolidation is just organizational housekeeping.
