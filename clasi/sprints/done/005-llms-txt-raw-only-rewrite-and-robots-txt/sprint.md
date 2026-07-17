---
id: '005'
title: llms.txt raw-only rewrite and robots.txt
status: closed
branch: sprint/005-llms-txt-raw-only-rewrite-and-robots-txt
worktree: false
use-cases:
- SUC-007
- SUC-008
issues:
- llms-txt-raw-only-admonition.md
- add-robots-txt.md
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Sprint 005: llms.txt raw-only rewrite and robots.txt

## Goals

Make the published site's agent-facing surface stronger and more discoverable
in two small, independent ways:

1. Rewrite `llms.txt` so it strongly steers agents toward raw Markdown
   (`llms-full.txt` or per-chapter raw GitHub links) and away from the HTML
   published pages, which add nothing but navigation chrome over content
   `llms.txt` already links in raw form.
2. Serve a `robots.txt` at the site root — currently a 404 — that allows all,
   points at the sitemap, and calls out `/llms-full.txt`/`/llms.txt` as
   conspicuous pointers, since `robots.txt` is often an agent's first fetch
   against an unfamiliar host.

## Problem

Sprint 002 built `llms.txt`/`llms-full.txt`; sprint 004 moved them to the
domain root so the `llms.txt` convention finds them. Two gaps remain, both
raised by the stakeholder on 2026-07-17 while reviewing the live site:

- `llms.txt`'s table of contents still links each entry to the **HTML**
  published page first, with the raw-markdown link as a secondary `(raw)`
  suffix. Agents following the primary link get navigation chrome instead of
  content, when the raw markdown (already linked one hop away) is a strict
  superset of what the HTML page shows.
- The site has no `robots.txt`. It currently 404s, which by crawler
  convention means "allow all" — so this is additive discovery, not a policy
  fix — but it is also a missed opportunity: `robots.txt` is frequently the
  first URL an agent or crawler requests, and right now it says nothing about
  `llms.txt`/`llms-full.txt`.

## Solution

Two disjoint-file changes landing in one sprint:

- **`llms.txt` rewrite** (`scripts/generate_llms_full.py`): add a strong,
  agent-directed admonition immediately after the title/description block
  (before or combined with the existing `llms-full.txt` pointer line)
  instructing agents to prefer `llms-full.txt` or the raw per-chapter links
  below, and to avoid the HTML pages. Remove the HTML published-page link
  from every table-of-contents entry: each entry becomes
  `- [title](raw-url): description` — no published-site URL, no separate
  `(raw)` suffix. `llms-full.txt`'s own format (raw markdown + canonical-URL
  headers, concatenated in book order) is untouched; only regenerated.
- **`robots.txt`**: `enableRobotsTXT = true` in `site/hugo.toml` plus a new
  `site/layouts/robots.txt` template that reads the domain from
  `{{ .Site.BaseURL }}` — never hardcoded a second time, the same discipline
  `generate_llms_full.py` already follows for `llms.txt`/`llms-full.txt`.
  Contents: `User-agent: *` / `Allow: /`, a `Sitemap:` line, and comment
  lines pointing agents at `/llms-full.txt` (index at `/llms.txt`).

Stakeholder's words (2026-07-17), verbatim:

> "add a strong admonition that agents should strongly prefer to use the raw
> chapters or the full llms-full, rather than going to the web pages. In
> fact, I would just take llms.txt and remove references to the HTML
> webpages. The full content of those is in the markdown files, and you've
> got a reference to the markdown files. They don't need to go there to get
> them."

> "all right" (approving the `robots.txt` recommendation), followed by
> "Do that and then re-publish."

## Success Criteria

- Deployed `llms.txt` opens with the admonition, and every ToC entry links
  only to `raw.githubusercontent.com` — zero
  `frc-code-scout.jointheleague.org` HTML page URLs remain in the ToC.
- `llms-full.txt` is byte-format unchanged apart from the regeneration pass.
- Deployed `https://frc-code-scout.jointheleague.org/robots.txt` returns 200
  with Allow-all, a `Sitemap:` line, and the llms pointers; `sitemap.xml`
  still serves 200.
- The domain string appears only via Hugo's `baseURL`/`{{ .Site.BaseURL }}`
  templating in both outputs, never hardcoded a second time.
- Site is re-published per the stakeholder's explicit follow-up instruction.

## Scope

### In Scope

- `scripts/generate_llms_full.py`: `render_llms`/`toc_entry_line` (or
  equivalent) rewritten to the new entry format and admonition; regenerating
  `site/static/llms.txt` and `site/static/llms-full.txt`.
- `site/hugo.toml`: `enableRobotsTXT = true`.
- New `site/layouts/robots.txt` template.
- Verifying `site/themes/hugo-theme-voidmain` has no competing `robots.txt`
  layout that would shadow or conflict with the new project-level template.
- Local verification: run the generator + `hugo --minify --source site`,
  inspect `site/public/robots.txt` and `site/public/llms.txt`.

### Out of Scope

- Any change to `llms-full.txt`'s per-page content or header format.
- The site's homepage banner / sidebar-footer agent pointers (sprint 002) —
  unaffected by either change.
- `sitemap.xml` generation itself — only verified as a non-regression, not
  modified.
- Any DNS/account-level change — sprint 004 already completed the
  custom-domain cutover; this sprint is pure repo-side content/config.

## Test Strategy

Config-and-generator sprint; no application test suite involved (same
precedent as sprints 002–004).

- Run `python3 scripts/generate_llms_full.py` standalone; inspect
  `site/static/llms.txt` for the admonition placement and the new
  `- [title](raw-url): description` entry format (spot-check several
  entries across parts), and confirm `site/static/llms-full.txt` is
  unchanged in structure (diff against a pre-change copy if useful).
- Run `hugo --minify --source site`; inspect `site/public/robots.txt` for
  the expected body and `site/public/llms.txt` for the carried-through
  generator output; confirm `site/public/sitemap.xml` still builds.
- Post-merge (team-lead, mirroring sprint 002/004 precedent): `curl -sI`
  the deployed `robots.txt`, `llms.txt`, and `sitemap.xml` URLs to confirm
  200s at the live domain.

## Architecture

**Sizing: Small.** Two independent, additive changes to already-existing
generated/config surfaces: rewriting the entry format one existing generator
function already emits, and turning on a Hugo built-in
(`enableRobotsTXT`) plus one new template file. No new module, no new or
changed inter-module dependency, no data-model change. The two changes touch
disjoint files and are safe to land together in one ticket.

### Architecture Overview

N/A — no component diagram warranted. This sprint edits the output shape of
one existing generator function (`render_llms`/`toc_entry_line` in
`scripts/generate_llms_full.py`, sprint 002) and adds one new,
self-contained Hugo layout file (`site/layouts/robots.txt`) that Hugo's own
`enableRobotsTXT` wiring discovers by convention. Neither adds a component
or changes an existing inter-component dependency documented in prior
sprints.

### Design Rationale

**Decision: rewrite `toc_entry_line`'s output format in place, no new
flag/mode.**
- Context: the issue is unambiguous that the HTML published-page link
  should be removed from `llms.txt` entirely, not made optional — the
  stakeholder's own words: "I would just take llms.txt and remove
  references to the HTML webpages."
- Alternatives considered: a CLI flag or config toggle switching between the
  old and new entry format — rejected; no consumer needs the old format
  (`llms.txt` has one audience, agents, and the stakeholder's directive is
  unconditional), so a toggle would be speculative generality with a single
  caller.
- Why this choice: matches the instruction literally; keeps the generator's
  one code path simple, consistent with sprint 002's own design stance.
- Consequences: reintroducing an HTML link in `llms.txt` later (unlikely,
  given raw markdown is a strict content superset for agent consumption)
  means revisiting this decision, not flipping a toggle.

**Decision: `llms-full.txt`'s per-page format is untouched.**
- Context: both issues scope the change to `llms.txt` only; `llms-full.txt`
  already contains only raw markdown plus canonical-URL headers, so it has
  no HTML-page reference to remove.
- Alternatives considered: none — explicitly out of scope per the issue
  text ("llms-full.txt (including its per-page canonical-URL headers) ...
  stay as they are").
- Why this choice: no content work needed; regenerating it is a side effect
  of running the same script, not a change.
- Consequences: the ticket's acceptance criteria require confirming
  `llms-full.txt`'s structure is unchanged apart from the regeneration pass,
  so a change in one output can't silently leak into the other.

**Decision: `robots.txt` via Hugo's `enableRobotsTXT` + a
`site/layouts/robots.txt` template, not a static file in `site/static/`.**
- Context: the issue explicitly calls for `enableRobotsTXT = true` plus a
  `layouts/robots.txt` template "so the domain comes from baseURL — never
  hardcoded a second time (same rule the llms generator follows)." A static
  file would hardcode the domain as a literal string, duplicating the
  source of truth `generate_llms_full.py` already treats `hugo.toml`'s
  `baseURL` as.
- Alternatives considered: a static `site/static/robots.txt`, matching how
  `llms.txt`/`llms-full.txt` themselves are checked-in static output —
  rejected specifically because `robots.txt`'s content (the `Sitemap:` line
  and domain-qualified pointers) needs the same anti-hardcoding discipline
  the issue calls out, and Hugo's `{{ .Site.BaseURL }}` templating gives
  that for free where a static file would not.
- Why this choice: one source of truth (`hugo.toml`'s `baseURL`) for every
  domain-bearing output, reached by two different mechanisms appropriate to
  each: the Python generator's regex extractor for `llms.txt`/
  `llms-full.txt`, Hugo's own templating for `robots.txt`.
- Consequences: `robots.txt` becomes template-dependent rather than a plain
  static asset. Planning-time verification
  (`find site/themes -iname "*robots*"`) found no theme-side `robots.txt`
  layout in `site/themes/hugo-theme-voidmain` — nothing to shadow — but the
  ticket re-verifies this rather than assuming it still holds at execution
  time.

### Migration Concerns

None. No data migration, no deployment sequencing gate (unlike sprint 004's
DNS-ordering constraint) — both changes are additive/output-format edits to
already-generated or already-built artifacts, and `robots.txt` currently
404s (crawler default: allow all), so enabling it changes no existing
crawl policy. Both changes can land, merge, and deploy together through the
sprint's normal close flow.

## Use Cases

### SUC-007: AI agent consumes llms.txt without following HTML links
Parent: UC-007

- **Actor**: AI coding agent (or automated crawler) reading the published
  site's `llms.txt`.
- **Preconditions**: Site is built and deployed; `llms.txt` exists at the
  domain root (sprint 004).
- **Main Flow**:
  1. Agent fetches `/llms.txt`.
  2. Immediately after the title/description, the agent reads an explicit
     admonition instructing it to prefer `/llms-full.txt` (everything in one
     fetch) or the per-chapter raw markdown links below, and not to fetch the
     HTML published pages.
  3. Agent either fetches `/llms-full.txt` in one request, or walks the
     Table of Contents — every entry links directly to the raw GitHub
     markdown file for that page; no published HTML URL is present to follow
     instead.
- **Postconditions**: Agent obtains full page content via raw markdown or
  the full dump without an HTML-page round trip; `llms.txt` contains zero
  `frc-code-scout.jointheleague.org` links in its ToC entries.
- **Acceptance Criteria**:
  - [ ] `llms.txt` opens with the admonition, placed after the
        title/description and before or combined with the `llms-full.txt`
        pointer line.
  - [ ] Every ToC entry line reads `- [title](raw-url): description` — no
        published-site URL, no separate `(raw)` suffix.
  - [ ] No `frc-code-scout.jointheleague.org` URLs remain anywhere in
        `llms.txt`'s ToC entries.
  - [ ] Descriptions and part/section heading grouping are unchanged from
        current output.
  - [ ] `llms-full.txt` is unchanged apart from the regeneration pass (same
        per-page raw markdown + canonical-URL header structure, concatenated
        in book order).

### SUC-008: Crawler/agent discovers the site via robots.txt
Parent: UC-007

- **Actor**: AI agent or web crawler landing on the site for the first time.
- **Preconditions**: Site is built and deployed at the custom domain
  (sprint 004).
- **Main Flow**:
  1. Agent requests `/robots.txt` — often its first request against an
     unfamiliar host.
  2. Response is 200: `User-agent: *` / `Allow: /`, a `Sitemap:` line
     pointing at the generated `sitemap.xml`, and comment lines pointing at
     `/llms-full.txt` and `/llms.txt`.
  3. Agent follows the `llms.txt` pointer into the flow described in
     SUC-007.
- **Postconditions**: `robots.txt` becomes another conspicuous, agent-facing
  pointer to the llms endpoints, alongside the homepage banner/footer
  (sprint 002) and the domain-root placement (sprint 004).
- **Acceptance Criteria**:
  - [ ] `https://frc-code-scout.jointheleague.org/robots.txt` returns 200.
  - [ ] Body contains an allow-all rule, a `Sitemap:` line, and comment
        pointers to `/llms-full.txt` and `/llms.txt`.
  - [ ] Domain appears only via `{{ .Site.BaseURL }}` templating, never
        hardcoded a second time.
  - [ ] `sitemap.xml` still serves 200 (non-regression check).

## GitHub Issues

None. This sprint is tracked via two local CLASI issues
(`llms-txt-raw-only-admonition.md`, `add-robots-txt.md`), linked above — no
GitHub issue in this repo.

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
| 001 | llms.txt raw-only rewrite and robots.txt template | — |
| 002 | Deploy verification for llms.txt and robots.txt | 001 |

Tickets execute serially in the order listed.
