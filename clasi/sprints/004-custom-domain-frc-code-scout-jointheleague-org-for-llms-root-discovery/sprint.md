---
id: '004'
title: Custom domain frc-code-scout.jointheleague.org for llms root discovery
status: planning-docs
branch: sprint/004-custom-domain-frc-code-scout-jointheleague-org-for-llms-root-discovery
worktree: false
use-cases:
- SUC-005
- SUC-006
issues:
- custom-domain-for-llms-root.md
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Sprint 004: Custom domain frc-code-scout.jointheleague.org for llms root discovery

## Goals

Give the published site its own hostname, `frc-code-scout.jointheleague.org`,
so `llms.txt` and `llms-full.txt` land at the domain root — where the
`llms.txt` convention says agents look — instead of under the GitHub Pages
project-site path where sprint 002 shipped them.

## Problem

An agent testing the published site completely missed `llms.txt`/
`llms-full.txt` (sprint 002's deliverable). Root cause: agents probe for
`llms.txt` at the **domain root** (`/llms.txt`), and as a GitHub Pages
*project* site the files live under a path
(`league-robotics.github.io/frc-code-scout/llms.txt`), where the convention
never looks. Giving the repo its own hostname puts them at the root.

## Solution

Move the site to `https://frc-code-scout.jointheleague.org/` via a DNS CNAME
(`frc-code-scout.jointheleague.org → league-robotics.github.io`, stakeholder's
action) plus a GitHub Pages custom-domain setting and a `baseURL` change on
the repo side. Two tickets split the work along the one hard constraint in
this sprint: **never set the Pages custom domain before the DNS CNAME
resolves** — GitHub starts redirecting the live site to the new hostname the
moment the custom domain is set, which would take the site down until DNS
lands.

- **Ticket 001 (repo-side, safe to land anytime)**: `site/hugo.toml`
  `baseURL` → `https://frc-code-scout.jointheleague.org/`. The sprint 002
  generator (`scripts/generate_llms_full.py`) reads `baseURL` out of
  `hugo.toml`, so `llms.txt`/`llms-full.txt` links update automatically —
  verified by regenerating and inspecting output. No other file needs an
  edit (see Design Rationale — the issue's claim about `docs/wiki/overview.md`
  needing an update did not hold up under re-verification).
- **Ticket 002 (DNS-gated cutover)**: confirm the CNAME resolves, set the
  Pages custom domain (`gh api -X PUT repos/League-Robotics/frc-code-scout/pages
  -f cname=frc-code-scout.jointheleague.org`), let the sprint branch merge
  through the team-lead's normal close flow, then verify the deployed site at
  the new root.

## Success Criteria

- `https://frc-code-scout.jointheleague.org/llms.txt` and `/llms-full.txt`
  return HTTP 200 at the domain root, with entries linking to the new domain.
- The homepage banner and sidebar-footer pointers (sprint 002) resolve on the
  new domain.
- Old published URLs (`league-robotics.github.io/frc-code-scout/*`) redirect
  to the new domain, so the docs-hub entry keeps working.
- HTTPS is enforced once GitHub issues the certificate for the new domain.
- The custom domain is never set before DNS resolves — no user-facing outage
  window.

## Scope

### In Scope

- `site/hugo.toml`: `baseURL` → `https://frc-code-scout.jointheleague.org/`.
- Regenerating and spot-checking `llms.txt`/`llms-full.txt` locally against
  the new `baseURL`.
- Local `hugo --minify --source site` build verification.
- DNS resolution check (`dig`/`host`) as a hard gate before touching Pages
  settings.
- Setting the GitHub Pages custom domain via `gh api`.
- Post-cutover verification: llms files at the new root, homepage/footer
  pointers, old-URL redirect behavior, HTTPS enforcement once the cert lands.

### Out of Scope

- Creating the DNS CNAME record itself — stakeholder's action, external to
  this repo, already in progress per the 2026-07-17 instructions.
- Any change to `scripts/generate_llms_full.py`'s logic — it already reads
  `baseURL`/`repoUrl` from `hugo.toml`; sprint 002's Migration Concerns
  flagged this as the one place that needs to stay in sync, and this sprint
  is that sync.
- Any change to `docs/wiki/_subsystem.yml`, `AGENTS.md`, or
  `.github/workflows/deploy-pages.yml` — grepped for hardcoded old-domain
  references; none found (see Design Rationale).
- Re-litigating sprint 002's `llms.txt`/`llms-full.txt` content design —
  only the domain the links point to changes here.

## Test Strategy

Config-and-DNS sprint; no application test suite involved.

- **Ticket 001 (pre-merge, on the sprint branch)**: run
  `python3 scripts/generate_llms_full.py` standalone and confirm every
  generated link now uses `https://frc-code-scout.jointheleague.org/`; run
  `hugo --minify --source site` and confirm `site/public/llms.txt` /
  `llms-full.txt` build cleanly with the new base URL; grep the repo for any
  remaining `league-robotics.github.io/frc-code-scout` references outside
  archived sprints and generated output.
- **Ticket 002, pre-cutover gate**: `dig`/`host` confirms the CNAME resolves
  to `league-robotics.github.io` before any Pages setting is touched. If it
  does not resolve, the ticket blocks — see ticket 002's acceptance criteria.
- **Ticket 002, post-close (mirrors sprint 002 ticket 003's precedent)**: the
  deployed-leg checks (files reachable at the new root, redirects, HTTPS
  enforced) can only be verified after the sprint branch merges to `master`
  and Pages redeploys, so they are recorded post-merge by the team-lead via
  `review_sprint_post_close`, exactly as sprint 002 ticket 003 did.

## Architecture

**Sizing: Small.** One build-config value (`baseURL`) and one GitHub Pages
account-level setting (custom domain) change. No new module, no new or
changed cross-module dependency, no data-model change. The generator and
templates sprint 002 built already derive everything from `baseURL`/
`repoUrl` in `hugo.toml` by design (see sprint 002's Migration Concerns,
which anticipated exactly this kind of domain change) — this sprint exercises
that design rather than extending it.

### Architecture Overview

N/A — no component diagram warranted. This sprint changes one config value
consumed by components sprint 002 already documented
(`scripts/generate_llms_full.py`, `deploy-pages.yml`, the Hugo build) and
adds one external, account-level setting (Pages custom domain) that sits
outside this repo's component graph entirely.

### Design Rationale

**Decision: change `baseURL` in `hugo.toml` only; no CNAME file added to the
repo or `site/static/`.**
- Context: the older GitHub Pages deploy method (publishing a branch such as
  `gh-pages`) requires a `CNAME` file in the published output because the
  custom-domain setting isn't persisted separately from the branch content.
  This repo deploys via `actions/upload-pages-artifact` +
  `actions/deploy-pages` (confirmed in `.github/workflows/deploy-pages.yml`,
  no `CNAME`-file handling present), where the custom domain is a repository
  setting (`gh api .../pages` `cname` field) that persists independently of
  each deploy's artifact contents.
- Alternatives considered: add a `site/static/CNAME` file so it rides along
  with the build the way sprint 002's static outputs do — rejected, it's the
  wrong mechanism for this deploy method and risks confusing the two Pages
  publishing models.
- Why this choice: matches how this repo actually deploys; one `gh api` call
  in ticket 002 sets the domain once, and it stays set across every future
  deploy with no repo-side file to maintain.
- Consequences: the custom domain is external state (a GitHub repo setting),
  not visible in the repo's own files — worth remembering if this sprint's
  intent needs re-discovering later.

**Decision: `docs/wiki/overview.md` is untouched by this sprint, despite the
issue naming it as a file needing a URL update.**
- Context: the issue text (written 2026-07-17, same day as sprint 003) states
  a grep found `hugo.toml` and `docs/wiki/overview.md` as "the only two files
  hardcoding old URLs." Re-verifying during this sprint's planning
  (`grep -rln "league-robotics.github.io/frc-code-scout"` across the repo,
  excluding archived sprints and generated output) found only `site/hugo.toml`
  — `docs/wiki/overview.md` does not match. Reading the file shows why:
  sprint 003 (closed earlier today) already rewrote its outbound link from
  the direct `league-robotics.github.io` URL to the hub-canonical
  `https://robots.jointheleague.org/frc-code-scout/` redirect, specifically
  to avoid an https→http downgrade hop. That hub URL doesn't hardcode the
  GitHub Pages hostname at all — it's an indirection the hub owns, and it
  will keep resolving to whatever the Pages site's current address is,
  including through the redirect GitHub Pages installs automatically when a
  custom domain is set (see Success Criteria). The issue's claim predates or
  didn't account for sprint 003's fix.
- Alternatives considered: change `docs/wiki/overview.md`'s link to point
  directly at `https://frc-code-scout.jointheleague.org/` anyway, matching
  the issue's literal instruction — rejected, it would replace a
  domain-agnostic indirection sprint 003 deliberately introduced with a
  hardcoded link that would need updating again on any future domain change,
  the exact problem the hub redirect exists to avoid.
- Why this choice: trust the re-verified current state of the file over a
  same-day issue note that predates a same-day sprint closing; don't
  introduce a regression against sprint 003's own design rationale.
- Consequences: ticket 001 still re-runs this grep itself before concluding
  no edit is needed, in case the file changes again before ticket execution.
  If the grep result differs at execution time, the ticket updates the file
  and this note is superseded — not a sprint-blocking discrepancy either way.

**Decision: split into two tickets strictly along the DNS-resolution gate,
not by file or by "frontend vs. backend."**
- Context: the issue's one hard constraint is sequencing — repo-side changes
  are safe to stage on the sprint branch at any time, but the Pages
  custom-domain setting must never be flipped before DNS resolves, or the
  live site goes down mid-propagation.
- Alternatives considered: one ticket covering everything — rejected, it
  would either force the whole ticket to block on stakeholder DNS action
  (delaying safe repo-side work for no reason) or risk an implementer setting
  the Pages domain too early inside a single undifferentiated task list.
- Why this choice: ticket 001 has zero risk and no external dependency, so it
  proceeds immediately; ticket 002 carries the one genuinely risky,
  externally-gated step and states the blocking condition explicitly in its
  own acceptance criteria.
- Consequences: ticket 002 depends on ticket 001 (needs the new `baseURL`
  already merged/mergeable) and additionally depends on an external fact
  (DNS resolution) that no ticket dependency graph can express — called out
  in the ticket text itself per the team-lead's instruction.

### Migration Concerns

No data migration. Sequencing is the only real risk in this sprint:

- **Outage window if sequencing is violated**: setting the Pages custom
  domain before DNS resolves makes GitHub redirect the live site to a
  hostname that doesn't yet resolve, taking the site down until DNS
  propagates. Ticket 002 gates on a `dig`/`host` check before touching Pages
  settings, and blocks with a report to the stakeholder rather than
  proceeding if DNS isn't ready.
- **HTTPS certificate lag**: GitHub issues the TLS certificate for a new
  custom domain after the domain is set and DNS is confirmed reachable; this
  can lag by minutes to an hour. "Enforce HTTPS" cannot be verified/enabled
  until the cert lands, so ticket 002 treats that check as best-effort at
  execution time and notes it explicitly if the cert hasn't issued yet.
- **Old-URL redirect**: GitHub Pages automatically 301-redirects the old
  `league-robotics.github.io/frc-code-scout/*` URLs to the new custom domain
  once it's set — this is existing GitHub Pages behavior, not something this
  sprint implements, but ticket 002 verifies it holds so the docs-hub entry
  (which links through `robots.jointheleague.org/frc-code-scout/`, itself
  chaining to the github.io URL as of today) keeps working.

## Use Cases

### SUC-005: AI agent fetches llms.txt/llms-full.txt at the domain root
Parent: UC-007

- **Actor**: AI coding agent (or any automated crawler) landing on the
  published site
- **Preconditions**: DNS CNAME resolves; the Pages custom domain is set;
  the site is built and deployed with `baseURL =
  https://frc-code-scout.jointheleague.org/`.
- **Main Flow**:
  1. Agent requests `https://frc-code-scout.jointheleague.org/llms.txt` at
     the bare domain root — no project-path guessing required, matching the
     `llms.txt` convention.
  2. Request succeeds (200) because the site now serves from its own
     hostname rather than a GitHub Pages project-site subpath.
  3. Agent follows the link to `/llms-full.txt`, or to an individual page
     via an `llms.txt` entry, exactly as sprint 002 built — every link now
     resolves under the new domain.
- **Postconditions**: Agent finds and fetches the single-file dump (or a
  specific page) without needing to already know the GitHub Pages project
  path.
- **Acceptance Criteria**:
  - [ ] `https://frc-code-scout.jointheleague.org/llms.txt` returns 200 at
        the bare root.
  - [ ] `https://frc-code-scout.jointheleague.org/llms-full.txt` returns 200
        at the bare root.
  - [ ] Every link inside both files points at `frc-code-scout.jointheleague.org`,
        not the old `league-robotics.github.io/frc-code-scout` path.

### SUC-006: Maintainer cuts the site over to the custom domain without an outage
Parent: UC-007

- **Actor**: Maintainer (team-lead, executing the repo-side steps on the
  stakeholder's behalf per the 2026-07-17 directive)
- **Preconditions**: Stakeholder has created the DNS CNAME record; ticket
  001's `baseURL` change has merged (or is ready to merge) to `master`.
- **Main Flow**:
  1. Maintainer checks DNS resolution (`dig`/`host` for
     `frc-code-scout.jointheleague.org`) before touching any Pages setting.
  2. If it resolves to `league-robotics.github.io`, maintainer sets the
     Pages custom domain (`gh api -X PUT .../pages -f
     cname=frc-code-scout.jointheleague.org`).
  3. The sprint branch merges to `master` through the normal close flow,
     redeploying the site with the new `baseURL`.
  4. Maintainer verifies: `llms.txt`/`llms-full.txt` reachable at the new
     root; homepage banner and sidebar-footer pointers (sprint 002) resolve
     correctly; old `league-robotics.github.io/frc-code-scout/*` URLs
     redirect to the new domain; HTTPS is enforced once the certificate has
     issued.
- **Postconditions**: Site is live at `frc-code-scout.jointheleague.org` with
  no downtime attributable to sequencing, and every sprint 002 discoverability
  feature works at the new root.
- **Error Flow**: DNS does not resolve at execution time — ticket 002 blocks
  without setting the Pages custom domain, and the team-lead reports the
  blocked state to the stakeholder rather than proceeding or guessing.
- **Acceptance Criteria**:
  - [ ] DNS resolution confirmed before the Pages custom domain is set (never
        the other order).
  - [ ] Deployed site serves at the new root with `llms.txt`/`llms-full.txt`
        present.
  - [ ] Homepage and footer pointers (sprint 002) resolve on the new domain.
  - [ ] Old published URLs redirect to the new domain.
  - [ ] HTTPS enforced once the certificate has issued (or explicitly noted
        as pending if it hasn't, at execution time).

## GitHub Issues

None. This sprint is tracked via the local CLASI issue
`custom-domain-for-llms-root.md` (linked above), not a GitHub issue in this
repo.

## Definition of Ready

Before tickets can be created, all of the following must be true:

- [x] Sprint planning document is complete (sprint.md, including its
      Architecture and Use Cases sections)
- [x] Architecture review passed (or skipped, for changes with no
      architectural impact)
- [x] Stakeholder has approved the sprint plan

## Tickets

| # | Title | Depends On |
|---|-------|------------|
| 001 | Repo-side URL migration (baseURL + llms regeneration) | — |
| 002 | DNS-gated cutover and end-to-end verification | 001 |

Tickets execute serially in the order listed.
