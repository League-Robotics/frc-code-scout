---
id: '001'
title: Rename docs/wiki/index.md to overview.md and fix canonical link
status: done
use-cases: []
depends-on: []
github-issue: ''
issue: fix-hub-doc-page-slug.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Rename docs/wiki/index.md to overview.md and fix canonical link

## Description

Fixes the hub-page 404 found in sprint 001's post-close verification.
`docs/wiki/index.md` collides with the League docs hub's static-site
generator, which treats any `index.*` file as a directory/section
index — the rendered page is dropped in favor of the auto-generated
subsystem landing page. Every working subsystem on the hub (e.g.
`ros-deploy`) uses a non-index filename such as `overview.md`.
Separately, the page's outbound link to
`https://league-robotics.github.io/frc-code-scout/` 301-redirects with
an https→http downgrade before reaching its destination, while
`https://robots.jointheleague.org/frc-code-scout/` serves 200 over
https directly — fix both in the same commit since it's the same file.

## Acceptance Criteria

Pre-close, structural — completable on the sprint branch, no live hub
dependency:

- [x] `docs/wiki/index.md` renamed to `docs/wiki/overview.md` via
      `git mv` (no leftover `docs/wiki/index.md`)
- [x] Frontmatter unchanged except `updated: 2026-07-17`; `title`,
      `blurb`, `order`, `tags` preserved exactly as they were
- [x] Page's outbound link changed from
      `https://league-robotics.github.io/frc-code-scout/` to
      `https://robots.jointheleague.org/frc-code-scout/`
- [x] No other file in `docs/wiki/` or `AGENTS.md` still references
      the old filename (`index.md`) or the old link
- [x] `docs/wiki/overview.md` frontmatter parses as valid YAML
- [x] Committed on the sprint branch; `dotconfig version bump` run per
      this repo's convention

## Post-close verification (team-lead, via `review_sprint_post_close`)

Live checks, unreachable pre-merge (the hub only re-renders after the
notify workflow fires on the merge push) — out of this ticket's scope
for the same reason sprint 001 ticket 003's live checks were:

- [ ] `https://robots.jointheleague.org/subsystems/frc-code-scout/overview/`
      returns 200 with the page content
- [ ] The rendered page links to
      `https://robots.jointheleague.org/frc-code-scout/`
- [ ] The hub homepage card for FRC Code Scout is still intact
- [ ] Fix forward if any check fails

## Implementation Plan

**Approach**: `git mv docs/wiki/index.md docs/wiki/overview.md`; edit
the `updated` field and the outbound link URL in the moved file; grep
`docs/wiki/` and `AGENTS.md` for any stray reference to `index.md` or
the old `league-robotics.github.io` link; commit; version bump.

**Files to create/modify**: `docs/wiki/overview.md` (renamed from
`docs/wiki/index.md`). No other files expected to change —
`.github/workflows/notify-docs-hub.yml`'s trigger (`docs/wiki/**`)
already covers the renamed file with no edit needed.

**Documentation updates**: None beyond the renamed page itself.

## Testing

- **Existing tests to run**: None affected — docs-only change. Run
  `uv run pytest` anyway as a no-op regression check per convention.
- **New tests to write**: None (content rename + link edit, not
  application code).
- **Verification command**: `uv run pytest`
