---
id: '002'
title: Advertise the dump on the homepage and site-wide footer
status: done
use-cases:
- SUC-003
depends-on:
- '001'
github-issue: ''
issue: agent-single-file-site-dump.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Advertise the dump on the homepage and site-wide footer

## Description

Add two site-local Hugo layout overrides so the published homepage, and
every page's persistent sidebar footer, conspicuously tell AI agents where
to fetch `/llms-full.txt` and `/llms.txt` (produced by ticket 001) instead
of crawling the site page by page.

The vendored theme (`site/themes/hugo-theme-voidmain/`) has no `partial`
hook for its sidebar footer, so the footer pointer requires a full
site-local override of `_default/baseof.html` rather than a small partial
edit — this is a deliberate, documented trade-off (see sprint.md → Design
Rationale → "override the vendored theme's `_default/baseof.html`
wholesale"). Do not edit the vendored theme files directly.

## Acceptance Criteria

- [x] `site/layouts/index.html` exists (a site-local override of the
      theme's `layouts/index.html`) and renders a conspicuous banner at
      the top of the homepage — before or immediately alongside the
      existing `session-header` block — with wording along the lines of
      "Agents: download this single file instead — it has everything",
      linking to `/llms-full.txt`, plus a secondary mention of `/llms.txt`
      for agents that want to fetch one page instead of everything.
- [x] The banner's links are built with Hugo's `relURL`/`absURL` (not a
      hardcoded path string), so they resolve correctly under the site's
      `baseURL` subpath (`https://league-robotics.github.io/frc-code-scout/`).
- [x] `site/layouts/_default/baseof.html` exists (a site-local override of
      the theme's `_default/baseof.html`) and adds one line inside the
      persistent `.sidebar-footer` block — present on every rendered
      page — pointing to `/llms-full.txt`, using the same
      `relURL`/`absURL` convention.
- [x] The override is the vendored theme's current `baseof.html` plus
      exactly the one added footer line — no unrelated behavior change
      (sidebar nav, prev/next buttons, the about-modal, and the mobile
      header all still work identically to before this ticket).
- [x] No file under `site/themes/hugo-theme-voidmain/` is modified —
      overrides live only under `site/layouts/`.
- [x] After `python3 scripts/generate_llms_full.py && hugo --minify
      --source site`, `site/public/index.html` contains the homepage
      banner text and a working link to `llms-full.txt`, and at least one
      non-home rendered page (e.g.
      `site/public/part-1/01-baseline-and-shape/index.html`) contains the
      sidebar-footer pointer line.

## Testing

- **Existing tests to run**: none — no automated test suite covers Hugo
  templates in this repo; verification is rendered-HTML inspection.
- **New tests to write**: none — see Verification command.
- **Verification command**:
  `hugo --minify --source site && grep -o "llms-full.txt" site/public/index.html site/public/part-1/01-baseline-and-shape/index.html`
  (both files should match; run ticket 001's generator first so the
  linked files actually exist for a full local check).

## Implementation Plan

**Approach**:

1. Copy `site/themes/hugo-theme-voidmain/layouts/index.html` to
   `site/layouts/index.html`; add a banner immediately inside
   `{{ define "main" }}`, before or as part of the existing
   `session-header` section.
2. Copy `site/themes/hugo-theme-voidmain/layouts/_default/baseof.html` to
   `site/layouts/_default/baseof.html`; add one line inside
   `.sidebar-footer-meta` (or an adjacent new line within
   `.sidebar-footer`) linking to `/llms-full.txt`.
3. Build both links with `{{ "llms-full.txt" | relURL }}` (and
   `{{ "llms.txt" | relURL }}` for the secondary mention) so they resolve
   correctly under the `baseURL` subpath — do not hand-write the full
   `https://league-robotics.github.io/frc-code-scout/llms-full.txt` path.
4. Style the banner minimally, reusing existing theme CSS patterns (e.g.
   the `callout` shortcode's markup as a visual reference) rather than
   introducing a large new CSS surface for a one-line banner.
5. Diff the two new files against their theme originals after editing to
   confirm the only change is the intended addition.

**Files to create/modify**:
- Create: `site/layouts/index.html`
- Create: `site/layouts/_default/baseof.html`

**Testing plan**: local Hugo build, then grep/visual-inspect
`site/public/index.html` and one non-home page's rendered HTML for the
pointer text and a resolvable link; confirm sidebar nav / prev-next /
about-modal still render by comparing structure against the pre-change
theme output.

**Documentation updates**: none beyond the banner/footer copy itself,
which is self-documenting on the page.
