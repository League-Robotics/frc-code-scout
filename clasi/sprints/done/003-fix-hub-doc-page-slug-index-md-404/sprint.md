---
id: '003'
title: Fix hub doc page slug (index.md 404)
status: closed
branch: sprint/003-fix-hub-doc-page-slug-index-md-404
worktree: false
use-cases: []
issues:
- fix-hub-doc-page-slug.md
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Sprint 003: Fix hub doc page slug (index.md 404)

## Goals

Fix the 404 on FRC Code Scout's League docs hub page and correct its
outbound link, so the entry sprint 001 shipped is actually reachable
end to end.

## Problem

Sprint 001's post-close verification found the hub homepage card for
FRC Code Scout is live, but the doc page itself 404s:
<https://robots.jointheleague.org/subsystems/frc-code-scout/index/>
serves the GitHub Pages 404 page. Root cause: `docs/wiki/index.md`
collides with the hub's static-site generator, which treats any
`index.*` file as a directory/section index — the rendered page is
dropped in favor of the auto-generated subsystem landing page. Every
working subsystem on the hub (e.g. `ros-deploy`) uses a non-index
filename such as `overview.md`. Separately, the page's outbound link
to `https://league-robotics.github.io/frc-code-scout/` 301-redirects
with an https→http downgrade before reaching its destination, while
`https://robots.jointheleague.org/frc-code-scout/` serves 200 over
https directly.

## Solution

`git mv docs/wiki/index.md docs/wiki/overview.md`, keeping all
frontmatter except bumping `updated` to `2026-07-17`; change the
page's outbound link to the canonical
`https://robots.jointheleague.org/frc-code-scout/`; push to `master`
so the existing `notify-docs-hub` workflow re-pings the hub.

## Success Criteria

- After merge and hub rebuild,
  <https://robots.jointheleague.org/subsystems/frc-code-scout/overview/>
  returns 200 with the page content.
- The page links to <https://robots.jointheleague.org/frc-code-scout/>.
- The hub homepage card still lists FRC Code Scout (unaffected by this
  change).

## Scope

### In Scope

- Rename `docs/wiki/index.md` → `docs/wiki/overview.md`
- Bump the page's `updated` frontmatter field
- Change the page's outbound link to the canonical hub URL
- Commit on the sprint branch, version bump per convention

### Out of Scope

- Any other `docs/wiki` content change
- Any change to the hub's generator/templates (external repo, not
  ours to change, and not needed — this fix matches the convention
  every other working subsystem already follows)
- Any change to `.github/workflows/notify-docs-hub.yml` (its trigger
  is `docs/wiki/**`, which covers the renamed file with no edit
  needed)

## Test Strategy

Two-line content fix; nothing to unit test. Verification splits into
pre-close and post-close for the same reason sprint 001 ticket 003
did: the hub rebuild is only reachable after the merge lands.

- **Pre-close (the ticket, on the sprint branch)**: confirm the file
  was renamed with `git mv` (no leftover `docs/wiki/index.md`),
  frontmatter still parses and is otherwise unchanged except
  `updated`, and the outbound link string exactly matches
  `https://robots.jointheleague.org/frc-code-scout/` with no other
  file in `docs/wiki/` still referencing the old filename or the old
  link.
- **Post-close (team-lead, via `review_sprint_post_close`)**: after
  `close-sprint` merges to `master`, confirm
  `/subsystems/frc-code-scout/overview/` returns 200, confirm the
  rendered page's link is the canonical URL, and confirm the homepage
  card is unaffected.

## Architecture

**Sizing: Trivial/small.** A filename rename plus a one-line URL
string edit inside an existing `docs/wiki` page (the module sprint 001
already established). No new module, no new or changed cross-module
dependency, no data-model change. The notify workflow's trigger
(`docs/wiki/**`) already covers the renamed file, so it needs no edit.
The fix follows the naming convention every other working hub
subsystem already uses — it restores the intended convention rather
than departing from it.

### Architecture Overview

N/A — no component diagram warranted. This touches one file inside
the `docs/wiki` module documented in sprint 001's Architecture section
and doesn't change how that module relates to the notify workflow or
the hub.

### Design Rationale

**Decision: rename to `overview.md` rather than patch the hub
generator or add a redirect.**
- Context: the hub's generator treats `index.*` as a section index,
  colliding with the auto-generated subsystem landing page. That
  generator lives in the external hub repo, not this one.
- Alternatives considered: (a) patch the hub generator to special-case
  `docs/wiki` index files — rejected, out of scope for this repo and
  would change behavior for every subsystem, not just ours; (b) keep
  `index.md` and add a client-side redirect — rejected, adds
  complexity for no benefit when a one-line rename matches the
  convention already used by working subsystems like `ros-deploy`.
- Why this choice: smallest possible fix, matches existing precedent,
  no external-repo change needed.
- Consequences: none — purely additive rename within this repo.

**Decision: switch the outbound link to
`https://robots.jointheleague.org/frc-code-scout/`.**
- Context: the `league-robotics.github.io` URL 301-redirects with an
  https→http downgrade before reaching the destination; the
  `robots.jointheleague.org` URL serves 200 over https directly.
- Alternatives considered: leave the `github.io` URL and rely on the
  redirect — rejected, an unnecessary http-downgrade hop is a needless
  wrinkle for hub visitors.
- Why this choice: direct, canonical, no downgrade.
- Consequences: none — same destination content, cleaner path.

### Migration Concerns

None. Pure rename plus a string edit; no data migration. The old URL
(`/subsystems/frc-code-scout/index/`) was never actually reachable —
it was the 404 bug being fixed here, not a live URL anyone could have
bookmarked as working.

## Use Cases

N/A — trivial. This sprint restores the intended behavior of SUC-001
("Student or mentor discovers FRC Code Scout via the League robots
hub") and SUC-002, both defined in sprint 001's `sprint.md`. It does
not introduce new user-facing behavior or change any use case's actor,
flow, or postconditions, so no new SUC is warranted here.

## GitHub Issues

None. Tracked via the local CLASI issue
`fix-hub-doc-page-slug.md` (linked above).

## Definition of Ready

Before tickets can be created, all of the following must be true:

- [x] Sprint planning document is complete (sprint.md, including its
      Architecture and Use Cases sections)
- [x] Architecture review passed (or skipped, for changes with no
      architectural impact)
- [ ] Stakeholder has approved the sprint plan

## Tickets

| # | Title | Depends On |
|---|-------|------------|
| 001 | Rename docs/wiki/index.md to overview.md and fix canonical link | — |

Tickets execute serially in the order listed.
