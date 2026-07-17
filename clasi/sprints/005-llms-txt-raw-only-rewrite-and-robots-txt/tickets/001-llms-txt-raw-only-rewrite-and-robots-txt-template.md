---
id: '001'
title: llms.txt raw-only rewrite and robots.txt template
status: in-progress
use-cases:
- SUC-007
- SUC-008
depends-on: []
github-issue: ''
issue:
- llms-txt-raw-only-admonition.md
- add-robots-txt.md
completes_issue: false
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# llms.txt raw-only rewrite and robots.txt template

## Description

Two independent, disjoint-file changes to the site's agent-discoverability
surface, landed together because both are small and both regenerate/rebuild
through the same local verification pass:

1. **`llms.txt` raw-only rewrite** (`scripts/generate_llms_full.py`): add a
   strong, agent-directed admonition right after the title/description
   block, and drop the HTML published-page link from every table-of-contents
   entry.
2. **`robots.txt`**: enable Hugo's built-in generator and supply a project
   template that derives the domain from `{{ .Site.BaseURL }}`.

`completes_issue: false` — this ticket lands the repo-side content/config
changes, but both linked issues' acceptance criteria are phrased against the
**deployed** site ("Deployed `llms.txt` opens with...", "Deployed
`https://frc-code-scout.jointheleague.org/robots.txt` returns 200...").
Ticket 002 is the one that verifies those deployed criteria post-merge and
completes the issues, following sprint 004's ticket 001/002 split precedent.

### Current state (verified during planning)

- `scripts/generate_llms_full.py`'s `toc_entry_line()` currently emits:
  `- [{title}]({published_url}) ([raw]({raw_url})){description}` — the
  published-site URL first, raw markdown as a secondary `(raw)` suffix.
  `render_llms()` places the `**Everything in one file:** [...llms-full.txt]`
  pointer line immediately after the title/description block, before the
  Table of Contents.
- `render_llms_full()`/`llms-full.txt`'s per-page format (`# {title}` +
  canonical published URL + raw body, divided by an HTML-comment divider) is
  untouched by this ticket — it has no HTML-page reference to remove in the
  first place. Regenerating it (a side effect of running the script) must
  not change its structure.
- `site/hugo.toml` has no `enableRobotsTXT` line today.
- `site/layouts/` contains only `_default/baseof.html` and `index.html` — no
  existing `robots.txt` layout to conflict with.
- `site/themes/hugo-theme-voidmain` has no `robots.txt` file anywhere
  (confirmed via `find site/themes -iname "*robots*"` — zero hits) — nothing
  for a new project-level `site/layouts/robots.txt` to shadow or conflict
  with. Re-verify this at execution time in case the vendored theme changed.

## Acceptance Criteria

**llms.txt rewrite:**

- [ ] A strong, agent-directed admonition appears in `llms.txt` immediately
      after the title/description block — before, or combined with, the
      existing `**Everything in one file:** [...llms-full.txt]` pointer
      line. Phrase it as a direct instruction to agents (per the
      stakeholder's words, quoted in sprint.md's Solution section and the
      stakeholder_approval gate notes): strongly prefer `llms-full.txt`
      (everything in one fetch) or the per-chapter raw markdown links below,
      not the HTML web pages, since the markdown files already contain the
      full content of every page.
- [ ] Every Table of Contents entry is rewritten from
      `- [title](published-url) ([raw](raw-url)): description` to
      `- [title](raw-url): description` — the raw GitHub markdown URL
      becomes the entry's only link; no published-site URL and no separate
      `(raw)` suffix remain anywhere in `llms.txt`.
- [ ] Descriptions and part/section (`##`/`###`) heading grouping are
      unchanged from current output — only the per-entry link format and the
      new admonition change.
- [ ] `llms-full.txt`'s structure is unchanged apart from the regeneration
      pass itself: same `# {title}` + canonical published-URL header + raw
      body per page, same `PAGE_DIVIDER`, same book order. Spot-check a
      regenerated copy against the current `site/static/llms-full.txt` to
      confirm no unintended drift.
- [ ] `python3 scripts/generate_llms_full.py` run standalone regenerates
      `site/static/llms.txt` and `site/static/llms-full.txt` with the above
      changes.

**robots.txt:**

- [ ] `site/hugo.toml` sets `enableRobotsTXT = true`.
- [ ] New `site/layouts/robots.txt` template exists and renders:
      `User-agent: *` / `Allow: /`; a `Sitemap:` line pointing at the site's
      generated `sitemap.xml`; comment lines telling agents the whole site
      is available at `/llms-full.txt` (index at `/llms.txt`).
- [ ] The domain in the rendered output comes only from
      `{{ .Site.BaseURL }}` (or equivalent Hugo templating) — never a second
      hardcoded literal, matching the rule `generate_llms_full.py` already
      follows for `hugo.toml`'s `baseURL`.
- [ ] Confirmed (re-verified at execution time, not just from planning) that
      `site/themes/hugo-theme-voidmain` has no competing `robots.txt` layout
      that would shadow the new project-level template.

**Local build verification (both changes):**

- [ ] `hugo --minify --source site` builds cleanly with no new errors or
      warnings.
- [ ] `site/public/llms.txt` reflects the rewritten format and admonition;
      `site/public/llms-full.txt` is unchanged in structure.
- [ ] `site/public/robots.txt` exists and matches the expected content.
- [ ] `site/public/sitemap.xml` still builds (non-regression check — this
      ticket must not disturb Hugo's existing sitemap generation).
- [ ] Changes committed on the sprint branch; no files touched outside
      `scripts/generate_llms_full.py`, `site/static/llms.txt`,
      `site/static/llms-full.txt`, `site/hugo.toml`, and the new
      `site/layouts/robots.txt`.

## Testing

- **Existing tests to run**: none — no application test suite covers this
  docs-publishing pipeline (same precedent as sprints 002–004).
- **New tests to write**: none; this is generator-output and Hugo-config
  changes, verified by direct inspection of generated/built output rather
  than an automated test suite.
- **Verification command**:
  `python3 scripts/generate_llms_full.py && hugo --minify --source site`,
  then inspect `site/public/llms.txt`, `site/public/llms-full.txt`,
  `site/public/robots.txt`, and `site/public/sitemap.xml`.

## Implementation Plan

**Approach**:

1. In `scripts/generate_llms_full.py`, change `toc_entry_line()` to drop the
   published-site URL and the `(raw)` suffix, linking each entry directly to
   `raw_url(entry, ...)`:
   `- [{entry.title}]({raw})` + description, in place of the current
   `- [{title}]({url}) ([raw]({raw})){description}`.
2. In `render_llms()`, add the admonition paragraph immediately after the
   title/description lines and before (or merged into) the existing
   `**Everything in one file:**` pointer line. Keep it short but
   unambiguous — a direct instruction to agents, not a soft suggestion.
3. Leave `render_llms_full()` and `raw_url()`/`published_url()` themselves
   untouched — `llms-full.txt`'s format and the URL-computation helpers
   `toc_entry_line()` calls are not changing, only which of their outputs
   `toc_entry_line()` uses.
4. Run `python3 scripts/generate_llms_full.py` standalone; inspect
   `site/static/llms.txt` for the new admonition and entry format across
   several entries (spot-check more than one part); confirm
   `site/static/llms-full.txt`'s structure is unchanged.
5. Add `enableRobotsTXT = true` to `site/hugo.toml`.
6. Create `site/layouts/robots.txt` using Hugo's text-template syntax
   (`{{ .Site.BaseURL }}`, `{{ "sitemap.xml" | absURL }}` or equivalent) to
   render the `User-agent`/`Allow`/`Sitemap`/comment-pointer content.
7. Re-run the `find site/themes -iname "*robots*"` check to confirm no
   theme-side conflict still holds.
8. Run `hugo --minify --source site`; inspect `site/public/llms.txt`,
   `site/public/llms-full.txt`, `site/public/robots.txt`, and
   `site/public/sitemap.xml`.
9. Commit on the sprint branch.

**Files to create/modify**:
- `scripts/generate_llms_full.py` (`toc_entry_line()`, `render_llms()`).
- `site/static/llms.txt`, `site/static/llms-full.txt` (regenerated output;
  checked in as the "current" static copy per sprint 002's approach).
- `site/hugo.toml` (`enableRobotsTXT = true`).
- `site/layouts/robots.txt` (new file).

**Testing plan**: script-level and build-level verification as described
above; no automated test suite applies (same as sprints 002–004's
docs-publishing precedent).

**Documentation updates**: none beyond the regenerated `llms.txt`/
`llms-full.txt` and the new `robots.txt`, which are themselves generated/
templated documentation artifacts.
