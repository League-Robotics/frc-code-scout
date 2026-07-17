---
id: '003'
title: Verify end-to-end site build and deployment
status: open
use-cases: [SUC-003, SUC-004]
depends-on: ['001', '002']
github-issue: ''
issue: agent-single-file-site-dump.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Verify end-to-end site build and deployment

## Description

End-to-end verification that the generator (ticket 001) and the
discoverability templates (ticket 002) work together, in CI, producing a
deployed site where `llms-full.txt`, `llms.txt`, and both pointer
locations are live and correct. This ticket does not add new source files;
it is the sprint's acceptance gate, and any small defects it surfaces
should be fixed by amending ticket 001's or 002's files, not by adding new
ones.

## Acceptance Criteria

- [ ] Local build (`python3 scripts/generate_llms_full.py && hugo --minify
      --source site`) succeeds with no errors or new warnings introduced
      by this sprint's changes.
- [ ] `site/public/llms-full.txt` exists, is non-empty, and the number of
      per-page headers in it matches the number of `.md` files under
      `docs/elite-arch/` at verification time (49 as of sprint planning —
      recount, since content may have changed since).
- [ ] `site/public/llms.txt` exists, links to `llms-full.txt` first, and
      its table of contents lists every page present in `llms-full.txt`'s
      header set, each with a working published-site link, a working raw
      GitHub Markdown link, and a non-empty description.
- [ ] Pushing this sprint's branch changes (or a `workflow_dispatch` run)
      triggers `deploy-pages.yml`, and the run completes successfully
      (`gh run list` / `gh run view` shows success), with the new
      generation step visible in the run log.
- [ ] The deployed
      `https://league-robotics.github.io/frc-code-scout/llms-full.txt`
      and `.../llms.txt` are reachable (HTTP 200) and their content
      matches the local build's output.
- [ ] The deployed homepage
      (`https://league-robotics.github.io/frc-code-scout/`) shows the
      agent-facing banner pointing to `llms-full.txt`.
- [ ] At least one other deployed page shows the sidebar-footer pointer.
- [ ] Two or three of `llms.txt`'s raw-GitHub-Markdown links are spot
      checked and resolve to real files on the `master` branch (e.g.
      `https://raw.githubusercontent.com/League-Robotics/frc-code-scout/master/docs/elite-arch/...`).

## Testing

- **Existing tests to run**: none — no automated test suite applies to
  this docs-publishing pipeline; this ticket's checklist *is* the test
  plan.
- **New tests to write**: none.
- **Verification command**:
  `python3 scripts/generate_llms_full.py && hugo --minify --source site`
  locally, followed by `gh run watch` (or `gh run list` after a push) for
  the CI leg, followed by `curl -sI` against the deployed URLs listed
  above to confirm HTTP 200.

## Implementation Plan

**Approach**:

1. Run the local build steps in the same order `deploy-pages.yml` will
   (generator script, D2 diagram rendering, `hugo --minify --source
   site`) and inspect the output files directly.
2. Push the sprint branch (or use `workflow_dispatch`) and monitor the
   `deploy-pages.yml` run via `gh run list`/`gh run watch` until it
   completes.
3. Once deployed, fetch the live URLs — `llms-full.txt`, `llms.txt`, the
   homepage, and one other page — and confirm their content matches
   tickets 001's and 002's acceptance criteria.
4. Spot-check two or three `llms.txt` raw-GitHub-Markdown links resolve
   correctly against the `master` branch.
5. If any check fails, fix it in ticket 001's or 002's files (this ticket
   creates no new files of its own) and re-run the affected checks.

**Files to create/modify**: none expected. Any fixes surfaced by
verification land in `scripts/generate_llms_full.py`,
`.github/workflows/deploy-pages.yml`, `site/layouts/index.html`, or
`site/layouts/_default/baseof.html` — the files ticket 001/002 already
own.

**Testing plan**: this ticket's Acceptance Criteria constitute the
sprint's full test plan — script/build-level (ticket 001), template-level
(ticket 002), and end-to-end deployment-level (here).

**Documentation updates**: none required beyond what tickets 001/002
already added.
