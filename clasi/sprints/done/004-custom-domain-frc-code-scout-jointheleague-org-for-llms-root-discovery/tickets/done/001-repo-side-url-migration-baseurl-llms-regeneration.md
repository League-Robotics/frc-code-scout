---
id: '001'
title: Repo-side URL migration (baseURL + llms regeneration)
status: done
use-cases:
- SUC-005
depends-on: []
github-issue: ''
issue: custom-domain-for-llms-root.md
completes_issue: false
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Repo-side URL migration (baseURL + llms regeneration)

## Description

Point the site's build config at the new custom domain so every generated
URL — including sprint 002's `llms.txt`/`llms-full.txt` links — is correct
once the domain cuts over in ticket 002. This ticket is entirely safe to
complete and merge-ready before the stakeholder's DNS record resolves; it
changes no live infrastructure, only build-time config consumed the next
time the site is built.

`site/hugo.toml`'s `baseURL` is the single source of truth for the
published-site URL: `scripts/generate_llms_full.py` (sprint 002) reads
`baseURL` and `params.repoUrl` out of this file with a small regex-based
extractor to build both the published-site and raw-GitHub-markdown links in
`llms.txt`/`llms-full.txt`. Changing `baseURL` and regenerating is therefore
sufficient to update every link in both files — no other generator code
changes.

`completes_issue: false` because ticket 002 is the one that actually
completes the parent issue's acceptance criteria (the deployed cutover);
this ticket only stages the repo-side half.

## Acceptance Criteria

- [x] `site/hugo.toml`'s `baseURL` is
      `https://frc-code-scout.jointheleague.org/` (was
      `https://league-robotics.github.io/frc-code-scout/`).
- [x] Running `python3 scripts/generate_llms_full.py` standalone regenerates
      `site/static/llms-full.txt` and `site/static/llms.txt`, and every link
      in both files uses the new `frc-code-scout.jointheleague.org` domain
      — spot-check the homepage/page headers in `llms-full.txt` and several
      `llms.txt` entries' published-site links (raw GitHub links are
      unaffected, since they come from `params.repoUrl`, not `baseURL`).
- [x] `hugo --minify --source site` builds cleanly with no new errors or
      warnings, and `site/public/llms.txt` / `llms-full.txt` reflect the new
      domain.
- [x] A fresh repo-wide grep for `league-robotics.github.io/frc-code-scout`
      (excluding `clasi/sprints/done/**`, `site/public/**`, `site/static/**`
      generated output, and this sprint's own issue/planning files) returns
      no hits outside `site/hugo.toml` before the edit — re-verify this
      ticket's own premise rather than trusting the sprint plan's grep
      result, since the repo may have changed since planning.
- [x] `docs/wiki/overview.md` is confirmed to need no change: its outbound
      link is `https://robots.jointheleague.org/frc-code-scout/`, a
      domain-agnostic hub redirect (sprint 003), not a hardcoded reference
      to the GitHub Pages hostname. If the re-verification grep above finds
      it (or any other file) now hardcoding the old URL, edit that file too
      and note the discrepancy against this ticket's plan in the PR/commit.
- [x] `AGENTS.md` and `docs/wiki/_subsystem.yml` confirmed to have no
      hardcoded domain references needing a change (re-verify; sprint
      planning found none).
- [x] `.github/workflows/deploy-pages.yml` confirmed to have no hardcoded
      domain reference or CNAME-file step needing a change (this repo
      deploys via `actions/upload-pages-artifact` + `actions/deploy-pages`,
      where the custom domain is a repository setting, not a file in the
      published artifact — see sprint.md Design Rationale).
- [x] Changes committed on the sprint branch; no application code touched
      outside `site/hugo.toml`, `site/static/llms.txt`,
      `site/static/llms-full.txt`, and (only if the re-verification grep
      requires it) `docs/wiki/overview.md`.

## Testing

- **Existing tests to run**: none — no application test suite covers this
  docs-publishing pipeline (same as sprint 002/003 precedent).
- **New tests to write**: none; this is a config-value change plus
  regeneration of already-tested generator output (sprint 002 built and
  verified `generate_llms_full.py`'s logic).
- **Verification command**:
  `python3 scripts/generate_llms_full.py && hugo --minify --source site`,
  then inspect `site/static/llms.txt`, `site/static/llms-full.txt`, and
  `site/public/index.html` for the new domain.

## Implementation Plan

**Approach**:

1. Edit `site/hugo.toml`: change `baseURL` from
   `"https://league-robotics.github.io/frc-code-scout/"` to
   `"https://frc-code-scout.jointheleague.org/"`. Leave `params.repoUrl`
   untouched (it points at the GitHub repo, not the published site, and is
   unaffected by the domain change).
2. Run `python3 scripts/generate_llms_full.py` standalone; diff or inspect
   `site/static/llms.txt` and `site/static/llms-full.txt` to confirm every
   published-site link now uses the new domain.
3. Run `hugo --minify --source site --destination /tmp/<scratch>` (or the
   repo's normal build location) and confirm `llms.txt`/`llms-full.txt`
   carry through into `site/public/` unchanged from step 2's output, and
   that `index.html` and other rendered pages don't hardcode the old domain
   anywhere `hugo.toml`'s `baseURL` templating didn't already cover.
4. Re-run the repo-wide grep for the old domain string, excluding archived
   sprints and generated output, and resolve any unexpected hits (expected:
   zero, per this sprint's planning-time verification).
5. Confirm `AGENTS.md`, `docs/wiki/_subsystem.yml`, and
   `.github/workflows/deploy-pages.yml` have nothing to change (planning
   found no hits; re-confirm here).
6. Commit on the sprint branch. Do not touch any Pages/DNS setting — that is
   entirely ticket 002's responsibility and is gated on the stakeholder's
   DNS record.

**Files to create/modify**:
- `site/hugo.toml` (baseURL).
- `site/static/llms.txt`, `site/static/llms-full.txt` (regenerated output;
  these are already build artifacts checked in as the "current" static
  copy per sprint 002's approach — regenerate and commit the refreshed
  versions).
- `docs/wiki/overview.md` — only if step 4's re-verification finds it
  actually needs a change (planning-time verification found it does not).

**Testing plan**: script-level and build-level verification as described
above; no automated test suite applies.

**Documentation updates**: none beyond the regenerated `llms.txt`/
`llms-full.txt` themselves, which are generated documentation artifacts.
