---
id: '003'
title: Verify end-to-end hub publication
status: done
use-cases:
- SUC-001
- SUC-002
depends-on:
- '001'
- '002'
github-issue: ''
issue: publish-to-league-docs-hub.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Verify end-to-end hub publication

## Description

**Amended** (planning defect found during execution): the original
scope of this ticket required a live `notify-docs-hub` run and a live
hub listing — but both are only satisfiable *after* the sprint-close
merge puts `docs/wiki/**` and the workflow file on `master`.
`workflow_dispatch` cannot run a workflow that isn't on the default
branch, and forcing a hub rebuild before `docs/wiki/` is on `master`
risks the hub rendering an empty or broken entry. Since `close_sprint`
requires all tickets done first, the original criteria could never be
satisfied pre-close. This is a sequencing conflict (surface:
internal/process), not a design flaw in the publishing pipeline
itself.

This ticket's scope is now **pre-close structural verification only**:
confirm every deterministic precondition for the pipeline is correctly
in place on the sprint branch and in the already-merged hub PR (ticket
002), so that the close-sprint merge is the only remaining step before
the live behavior (workflow run, hub listing) becomes true. The live
checks move to a **post-close verification** step owned by the
team-lead (see below) — they cannot live in this ticket because they
are post-merge by construction.

## Acceptance Criteria

- [x] Hub registration entry for `frc-code-scout` confirmed present on
      `League-Robotics/League-Robotics.github.io`'s `master` (already
      landed via ticket 002, PR
      <https://github.com/League-Robotics/League-Robotics.github.io/pull/2>
      — re-confirm here, don't just trust the PR-merged status)
- [x] `.github/workflows/notify-docs-hub.yml` (on the sprint branch)
      parses as valid YAML, and passes `actionlint` if it's installed
      (skip with a note if not available)
- [x] The workflow's `on.push.branches` includes `master` (and
      `main`), and `on.push.paths` includes `docs/wiki/**`, matching
      sprint.md's Design Rationale
- [x] Org-level `DOCS_HUB_APP_ID` / `DOCS_HUB_APP_PRIVATE_KEY`
      confirmed visible to this repo (already confirmed during ticket
      002 execution — re-verify via `gh variable list` /
      `gh secret list` if accessible, otherwise cite that prior
      confirmation)
- [x] `https://league-robotics.github.io/frc-code-scout/` is reachable
      (HTTP 200) — this is the link target ticket 001's wiki page
      points to
- [x] `docs/wiki/_subsystem.yml` and `docs/wiki/index.md` frontmatter
      still parse cleanly on the sprint branch (re-check for drift
      since ticket 001)
- [x] Sprint 001's Success Criteria (in `sprint.md`) are confirmed
      **satisfiable by the close-sprint merge** — every precondition
      under this repo's control is in place; nothing further is
      blocked pre-merge

## Post-close verification (team-lead, via `review_sprint_post_close`)

These checks are explicitly out of this ticket's scope — they are
post-merge by construction (the workflow only runs on pushes to
`master`, and the workflow file itself isn't on `master` until
`close-sprint` merges the branch). Pushing directly to `master` outside
the sprint process to satisfy them pre-close is not something this
sprint's process does. After `close-sprint` merges to `master`, the
team-lead confirms:

- [ ] `gh run list` shows a successful `notify-docs-hub` run triggered
      by the merge push to `master`
- [ ] robots.jointheleague.org lists FRC Code Scout with a working
      link to <https://league-robotics.github.io/frc-code-scout/>
- [ ] If either check fails, fix forward (open a new ticket/issue for
      the fix rather than reopening this one — this ticket's scope is
      closed and its linked issue may already be archived)

## Implementation Plan

**Approach**: On the sprint branch, run the structural checks listed
above (YAML parse, optional `actionlint`, trigger-config inspection,
credential visibility, site reachability, frontmatter re-parse). Do
not attempt to trigger the workflow or check the hub's live rendering
from this ticket — those are the team-lead's post-close checks. If a
structural defect is found, fix it here (this ticket, or loop back to
ticket 001/002 artifacts) rather than deferring it.

**Files to create/modify**: None expected (verification only); may
touch ticket 001/002 artifacts if a structural defect is found.

**Documentation updates**: None, unless verification uncovers a doc
fix that's needed.

## Testing

- **Existing tests to run**: None — this ticket is verification, not
  application code.
- **New tests to write**: None (structural/operational verification).
- **Verification command**: `uv run pytest` (no-op; kept for
  convention)

## Verification results

Run on the sprint branch (`sprint/001-publish-frc-code-scout-to-the-league-docs-hub`),
2026-07-17. All checks PASS; no defects found; nothing fixed forward.

| # | Check | Command | Result |
|---|-------|---------|--------|
| 1 | Hub registration entry present | `gh api repos/League-Robotics/League-Robotics.github.io/contents/subsystems.yml --jq '.content' \| base64 -d` | PASS — entry present: `name: frc-code-scout`, `repo: League-Robotics/frc-code-scout`, `branch: master` |
| 2 | Workflow/docs YAML parses | `python3 -c "import yaml; yaml.safe_load(open(...))"` on `.github/workflows/notify-docs-hub.yml`, `docs/wiki/_subsystem.yml`, and `docs/wiki/index.md`'s frontmatter block | PASS — all three parse without error |
| 2a | `actionlint` on workflow | `brew install actionlint` (succeeded, 1.7.12) then `actionlint .github/workflows/notify-docs-hub.yml` | PASS — exit 0, zero findings |
| 3 | Trigger config matches Design Rationale | inspected parsed YAML: `on.push.branches`, `on.push.paths` | PASS — `branches: [main, master]`, `paths: ["docs/wiki/**"]` |
| 4 | Org credentials visible to this repo | `gh api repos/League-Robotics/frc-code-scout/actions/organization-variables`; `gh api repos/League-Robotics/frc-code-scout/actions/organization-secrets` | PASS — `DOCS_HUB_APP_ID` (var) and `DOCS_HUB_APP_PRIVATE_KEY` (secret) both listed, 1 each. Note: `gh variable list` / `gh secret list` (repo-scoped) returned empty since these are org-level, not repo-level — the ticket's documented fallback (org-scoped `actions/organization-variables` / `-secrets` API) is what actually confirmed visibility. |
| 5 | Site reachability | `curl -sIL https://league-robotics.github.io/frc-code-scout/` | PASS — chain ends `HTTP/1.1 200 OK` (301 from `league-robotics.github.io/frc-code-scout/` → `robots.jointheleague.org/frc-code-scout/` → 200; body contains "frc-code-scout"). `docs/wiki/index.md` links exactly `https://league-robotics.github.io/frc-code-scout/` (line 40). Note: the redirect hop downgrades https→http and targets `robots.jointheleague.org` — that's hub-side infra (custom domain/CNAME config) outside this repo's and this ticket's control; not a defect in ticket 001/002 artifacts. |
| 6 | Frontmatter re-parse, required fields | manual inspection of parsed YAML from check 2 | PASS — `docs/wiki/_subsystem.yml` has `name`/`title`/`blurb`; `docs/wiki/index.md` frontmatter has `title`/`blurb` (plus `order`/`updated`/`tags`). No drift since ticket 001. |
| 7 | Sprint.md Success Criteria satisfiable pre-close | read `sprint.md` Success Criteria / Test Strategy sections | PASS — already written in the amended pre-close/post-close split; every pre-close precondition (checks 1–6 above) is confirmed in place. Post-close checks (`gh run list` success, hub listing) are explicitly out of scope here and deferred to the team-lead via `review_sprint_post_close`, per this ticket's "Post-close verification" section. |

No structural defects found in the ticket 001/002 artifacts. No fixes were
needed. Live workflow run and live hub listing remain deferred to
post-close verification, as scoped by this ticket's amendment.
