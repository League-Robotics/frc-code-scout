---
title: 1. How we read the corpus
parent: Part I — The Elite Architecture
grand_parent: The Elite & League Architectures
nav_order: 1
---

# 1. How we read the corpus

The architecture in this book was not designed from first principles. It was read out of source
code — dozens of public FRC repositories, plus a wider base of Botball, FLL, and WRO programs — and
then turned into something you can teach and grade. This chapter is the method, because the method is
what makes the rest trustworthy.

## Two questions

Everything here sits on two questions. The practical one: *what does sophisticated student robot code
actually look like, concretely enough to teach and to grade?* The local one: *how do San Diego's
teams stack up against that standard, and does better code correlate with winning?* The standard was
learned nationally — from the best teams in the country — and then applied locally. The rubric is
San-Diego-applied but nationally-derived.

## The pipeline

The work ran in nine stages, from corpus to rubric to ranked survey to a four-year deep dive on one
team.

| Stage | What happened |
|---|---|
| 1. Corpus teardown | Read public repos to find the recurring architecture |
| 2. Pattern extraction | Named the shared structures: the IO layer, the coordination paradigms, the ladder |
| 3. Local inventory | Catalogued every San Diego team with public code (29 FRC orgs, 12 FTC) |
| 4. Bulk download | Shallow-cloned and pruned every repo to a code-only corpus |
| 5. Rubric design | Turned the patterns into an eight-dimension anchored rubric |
| 6. Pilot + refinement | Scored three teams to test the instrument; fixed two scoring rules |
| 7. Full scoring + validation | Scored 24 teams, paired with Statbotics EPA, measured what predicts results |
| 8. Build spec | Distilled a foundation-first architecture to grow into |
| 9. Patribots deep dive | Re-cloned four seasons with full history; scored year by year |

Stages 1–2 produced no scores — only a shared vocabulary of observable structures. Three teardowns
established it: a broad baseline of 21 non-FRC repos (every program converges on the same three
layers — device map, motion primitives, mission logic), a survey of 37 FRC teams across four
languages and six coordination paradigms, and a deep dive on the IO layer (FRC's house name for the
Strategy pattern).

A deliberate cost is baked into stage 4. Clones are shallow and `.git`-stripped, which keeps the
corpus small but erases commit history. That is why the sustainability dimension is read as a floor,
and why the Patribots deep dive (stage 9) re-cloned with full history to see what the survey could
not.

## The golden rule: score what's used, not what's present

The single rule that governs all scoring: **every candidate is confirmed by opening the file.** A
Choreo vendordep with no referenced trajectories is not Choreo adoption. An empty `src/test` folder
is not testing. A class named `Superstructure` that only holds references is baseline command-based
wearing a level-3 name.

This is not fastidiousness — it is measured. On the same 55 teams, scores from a model that *opened
the files* predict EPA at Spearman ρ ≈ 0.53; a mechanical pass that scores grep hits as presence
reaches only ρ ≈ 0.29. Confirming use roughly doubles the rubric's predictive validity. The cheap
pass is a lead sheet, not a score.

The grep matters less than people expect in another way too: agreement between the mechanical pass
and the confirmed score is high for testing, architecture, and simulation (κ ≈ 0.8), but low for
autonomous, vision, and sustainability (κ ≈ 0.6) — exactly the dimensions where "present" diverges
most from "used." Spend the reading budget there.

## What to carry forward

Read the best code first to learn what good looks like; name the structures before scoring anything;
confirm every claim by reading. The next two chapters set the two reference points the rest of Part I
measures against — the command-based baseline ([ch. 2](02-the-baseline.md)) and the eight-dimension
rubric ([ch. 3](03-the-rubric.md)).
