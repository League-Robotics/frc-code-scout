---
id: '001'
title: Add docs/wiki publication files and notify workflow
status: in-progress
use-cases:
- SUC-001
- SUC-002
depends-on: []
github-issue: ''
issue: publish-to-league-docs-hub.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Add docs/wiki publication files and notify workflow

## Description

Add the repo-side files required by the League Robotics docs hub
publishing spec (<https://robots.jointheleague.org/publishing/>):
`docs/wiki/_subsystem.yml`, one `docs/wiki` landing page, and the
`notify-docs-hub` GitHub Actions workflow adapted for this repo's
`master` default branch. Also add the `AGENTS.md` section that tells
future agents `docs/wiki/` is the hub's source of truth. This is the
foundation ticket — ticket 002 (hub registration) and ticket 003
(verification) both depend on these files existing and being valid.

## Acceptance Criteria

- [x] `docs/wiki/_subsystem.yml` exists with `name: frc-code-scout`,
      `title: FRC Code Scout`, and a one-sentence `blurb`; parses as
      valid YAML
- [x] `docs/wiki/index.md` exists with frontmatter `title` and `blurb`
      (optionally `order`, `slug`, `updated: 2026-07-17`, `tags`),
      written in plain language for students/mentors visiting the
      robots site (not rubric jargon) — describing what FRC Code Scout
      is for and why a visitor would go there, drawn from `README.md`
      / `AGENTS.md` wording (scores FRC/FTC team code against an
      8-dimension rubric *and* provides build-out skills for elite
      robot architecture)
- [x] The page links to
      <https://league-robotics.github.io/frc-code-scout/>
- [x] `.github/workflows/notify-docs-hub.yml` exists, reconstructed
      from the spec's template with `on.push.branches: [main, master]`
      (matching the `deploy-pages.yml` convention already in this
      repo, since this repo's default branch is `master`, not `main`)
      and `paths: ["docs/wiki/**"]`, plus `workflow_dispatch`
- [x] The workflow mints a token via `actions/create-github-app-token@v1`
      using org-level `vars.DOCS_HUB_APP_ID` /
      `secrets.DOCS_HUB_APP_PRIVATE_KEY` (no repo-local secrets
      created) and sends a `repository_dispatch` (`docs-updated`) to
      `League-Robotics/League-Robotics.github.io`
- [x] `AGENTS.md` gains a short new section stating `docs/wiki/` is the
      source of truth published to the League docs hub, linking to
      <https://robots.jointheleague.org/publishing/>
- [x] All new/modified YAML files parse cleanly
- [ ] Changes committed and pushed to `master` — committed to the sprint
      branch `sprint/001-publish-frc-code-scout-to-the-league-docs-hub`
      per team-lead dispatch instructions (do not push/merge to
      `master` from a ticket; that happens at sprint close)

## Implementation Plan

**Approach**: Create the `docs/wiki/` directory with the two required
files, reusing the existing project-description language from
`README.md`/`AGENTS.md` rather than inventing new framing. Reconstruct
the notify workflow exactly from the publishing spec's template, with
only the branch-list adaptation described above (see sprint.md's
Architecture → Design Rationale for why `[main, master]` and not
`master`-only or renaming the default branch). Add a short, additive
`AGENTS.md` section — do not restructure existing sections.

**Files to create**:
- `docs/wiki/_subsystem.yml`
- `docs/wiki/index.md`
- `.github/workflows/notify-docs-hub.yml`

**Files to modify**:
- `AGENTS.md` (new section)

**Documentation updates**: `AGENTS.md` as above. No `README.md` change
required — out of scope per sprint.md.

## Testing

- **Existing tests to run**: None affected — no application code
  changes. Run `uv run pytest` anyway to confirm the ticket introduced
  no regressions.
- **New tests to write**: None (docs/config only). Validate instead:
  `python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))"`
  against `docs/wiki/_subsystem.yml`, `docs/wiki/index.md`'s
  frontmatter, and `.github/workflows/notify-docs-hub.yml`. Manually
  diff the workflow against the spec template plus the
  `master`-branch adaptation.
- **Verification command**: `uv run pytest`
