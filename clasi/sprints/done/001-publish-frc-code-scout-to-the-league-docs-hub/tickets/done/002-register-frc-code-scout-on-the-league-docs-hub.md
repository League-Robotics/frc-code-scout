---
id: '002'
title: Register frc-code-scout on the League docs hub
status: done
use-cases:
- SUC-001
depends-on:
- '001'
github-issue: ''
issue: publish-to-league-docs-hub.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Register frc-code-scout on the League docs hub

## Description

Open a PR against `League-Robotics/League-Robotics.github.io` (default
branch `master`) adding an entry for `frc-code-scout` to its
`subsystems.yml`, then merge it — admin access on the hub repo is
confirmed via `gh` CLI, logged in as `ericbusboom`. This registers the
repo with the hub so it knows this repo exists and where its docs
live; it depends on ticket 001 because the entry should point at real,
already-landed `docs/wiki` content rather than an empty path.

## Acceptance Criteria

- [x] Hub repo (`League-Robotics/League-Robotics.github.io`) cloned to
      the scratchpad directory; a new branch created off `master`
- [x] `subsystems.yml` gains an entry:
      ```yaml
        - name: frc-code-scout
          repo: League-Robotics/frc-code-scout
          branch: master
      ```
      preserving the file's existing style/formatting/ordering.
      `docs_path` is omitted: the file's header comment documents
      `docs/wiki` as the default, and every existing entry omits the
      field for that same reason, so `docs_path: docs/wiki` was left
      out to match convention rather than stated redundantly.
- [x] PR opened via `gh` against
      `League-Robotics/League-Robotics.github.io`
      ([PR #2](https://github.com/League-Robotics/League-Robotics.github.io/pull/2))
- [x] PR merged (squash-merged, no `--admin` override needed;
      merge commit `6651de80fd4703ffdca1f364d5ad79e468878e7c`)
- [x] Entry present on the hub repo's `master` branch after merge
      (verified via `gh api repos/League-Robotics/League-Robotics.github.io/contents/subsystems.yml`)

## Implementation Plan

**Approach**: Clone the hub repo into the scratchpad dir, create a
branch (e.g. `add-frc-code-scout-subsystem`), append the entry
preserving existing indentation/ordering conventions in
`subsystems.yml`, commit, push, `gh pr create`, `gh pr merge` (admin
rights already confirmed — no additional authorization needed).

**Files to create/modify** (in the external hub repo, not this repo):
`subsystems.yml`.

**Documentation updates**: None in this repo.

## Testing

- **Existing tests to run**: None in this repo (change is entirely in
  the external hub repo). Confirm any CI checks the hub repo runs on
  PRs pass before merging.
- **New tests to write**: None. Validate `subsystems.yml` parses as
  YAML after the edit, before opening the PR.
- **Verification command**: `uv run pytest` (no-op here; kept for
  convention — nothing in this repo changes)

## Notes

Credential-visibility check for the notify workflow's prerequisites,
run against `League-Robotics/frc-code-scout`:

- Org secret `DOCS_HUB_APP_PRIVATE_KEY` — visible (confirmed via
  `gh api repos/League-Robotics/frc-code-scout/actions/organization-secrets`).
- Org variable `DOCS_HUB_APP_ID` (value `3989816`) — visible (confirmed via
  `gh api repos/League-Robotics/frc-code-scout/actions/organization-variables`).

Note: `gh api repos/League-Robotics/frc-code-scout/actions/variables/DOCS_HUB_APP_ID`
and `gh variable list -R League-Robotics/frc-code-scout` both come back
empty/404 because those endpoints only surface repo-level variables, not
org-level ones inherited by the repo. The org-scoped endpoints above are
the correct check, and both prerequisites are visible — no gap for the
notify workflow.
