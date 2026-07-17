---
id: '001'
title: Generate llms-full.txt and llms.txt at build time
status: in-progress
use-cases:
- SUC-003
- SUC-004
depends-on: []
github-issue: ''
issue: agent-single-file-site-dump.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Generate llms-full.txt and llms.txt at build time

## Description

Add a stdlib-only Python build step, `scripts/generate_llms_full.py`, that
walks `docs/elite-arch/` recursively and produces two generated files in
`site/static/` (so Hugo's normal static-file copy carries them into
`site/public/` with no template wiring):

- **`llms-full.txt`** — every page's raw Markdown content, each prefixed
  with a `title` + canonical published-URL header, concatenated in full
  recursive book order (top-level section weight, then page/subsection
  weight, recursing into nested sections).
- **`llms.txt`** — site title + description at the top, a prominent link to
  `/llms-full.txt` ("everything in one file") first, then a full table of
  contents: every page listed under its part/section heading with a link to
  the published page, a secondary `(raw)` link to that page's raw GitHub
  Markdown, and a one-line description that is never hand-written
  (frontmatter `description` if present, otherwise derived from the page's
  first prose paragraph).

Wire the script into `.github/workflows/deploy-pages.yml` as a new step,
run before "Build Hugo" (alongside the existing "Render D2 diagrams" step),
so both files are regenerated on every build with no manual step.

Full rationale — including why this is a build script rather than a Hugo
custom output format, the frontmatter-parsing approach, the
description-derivation rule, and the link-target decision — is in
`clasi/sprints/002-agent-single-file-dump-of-the-hugo-site/sprint.md`
(Architecture → Design Rationale).

## Acceptance Criteria

- [ ] `scripts/generate_llms_full.py` exists, is stdlib-only (no new
      `pyproject.toml` dependency — no `yaml` import), and runs standalone:
      `python3 scripts/generate_llms_full.py`.
- [ ] Running it writes `site/static/llms-full.txt` containing every `.md`
      file under `docs/elite-arch/` (including nested subsections, e.g.
      `appendices/how-we-developed-this/*`,
      `appendices/lessons-from-outside/*`), each entry prefixed with a
      header carrying the page's `title` and its canonical published-site
      URL (`baseURL` + relative path + trailing slash).
- [ ] Pages appear in **full recursive book order**: top-level sections
      sorted by frontmatter `weight`, and within each section, pages and
      nested subsections sorted by `weight` and recursed into in that
      order — not just the two-level depth the existing sidebar nav in
      `baseof.html` walks (that logic misses pages nested under
      subsections and must not be copied as-is).
- [ ] Running it also writes `site/static/llms.txt` containing, in order:
      (a) site title + description sourced from `site/hugo.toml`
      (`title`, `params.description`); (b) a prominently placed link to
      `/llms-full.txt` labeled clearly (e.g. "everything in one file"),
      positioned before the table of contents; (c) a full table of
      contents below that, grouped under part/section headings matching
      book order (nested subsections get their own sub-heading), one entry
      per page.
- [ ] Each `llms.txt` page entry has: a link to the page's published-site
      URL, a secondary `(raw)` link to
      `https://raw.githubusercontent.com/<owner>/<repo>/master/docs/elite-arch/<relpath>`,
      and a one-line description.
- [ ] Each entry's description uses frontmatter `description` if the page
      has one, otherwise is derived from the page's first non-blank,
      non-heading prose paragraph: Markdown emphasis/link syntax stripped
      to plain text, whitespace collapsed, truncated to roughly 160
      characters at a word boundary with a trailing `…` if truncated.
- [ ] The owner/repo (for raw GitHub URLs) and `baseURL` (for published
      URLs) are both read out of `site/hugo.toml` (`params.repoUrl`,
      `baseURL`) via a small regex-based extractor — not hardcoded a
      second time anywhere in the script. The branch is hardcoded to
      `master` with a comment pointing at `deploy-pages.yml`'s
      `branches: [main, master]` trigger as the precedent.
- [ ] Frontmatter is parsed with a small stdlib parser (split on the `---`
      delimiters, parse simple `key: value` lines) — no `pyyaml` or other
      new dependency added to `pyproject.toml`.
- [ ] `.github/workflows/deploy-pages.yml` has a new step running
      `python3 scripts/generate_llms_full.py`, positioned after checkout
      and before the "Build Hugo" step.
- [ ] After running `hugo --minify --source site` locally,
      `site/public/llms-full.txt` and `site/public/llms.txt` exist and
      match what the script wrote to `site/static/` (Hugo's verbatim
      static-file copy).

## Testing

- **Existing tests to run**: none apply — no Python test suite currently
  covers `scripts/` build tooling (`scripts/render_diagrams.py`, the
  closest precedent, has no test file either). Do not add a `pytest`
  dependency for this ticket.
- **New tests to write**: none — verification is direct output inspection
  (see Verification command / Implementation Plan below), consistent with
  how `render_diagrams.py` is developed and checked today.
- **Verification command**:
  `python3 scripts/generate_llms_full.py && hugo --minify --source site`
  (Hugo v0.157.0+extended is already installed locally, matching what
  `deploy-pages.yml` installs via `peaceiris/actions-hugo@v3` with
  `hugo-version: "latest"`), then inspect `site/static/llms-full.txt`,
  `site/static/llms.txt`, `site/public/llms-full.txt`, and
  `site/public/llms.txt` directly.

## Implementation Plan

**Approach**:

1. Write a small stdlib frontmatter parser: split a file's text on the
   `---` delimiters, parse the `title:`/`weight:`/`description:` lines
   (simple `key: value`, no nested structures needed for this corpus).
2. Write a recursive directory walker over `docs/elite-arch/`: for each
   directory, read its `_index.md` (if present) as that section's own
   entry; list child entries (files and subdirectories), each carrying a
   `weight` (from its own frontmatter for files, from its `_index.md`
   frontmatter for subdirectories); sort by `weight`; recurse into
   subdirectories in that sorted order. This assembles one ordered list of
   `(title, relpath, weight, raw_body)` tuples covering every page and
   section landing, depth-first — deliberately more thorough than
   `baseof.html`'s existing two-level `$allPages` construction.
3. Add a tiny `site/hugo.toml` extractor: regex-match `baseURL = "..."`
   and the `repoUrl = "..."` line under `[params]`.
4. From the ordered list, compute each entry's published URL (`baseURL` +
   relpath with `.md` stripped + trailing slash, matching the site's
   existing pretty-URL convention — verify against
   `site/public/part-1/01-baseline-and-shape/` as the known-good pattern)
   and raw GitHub URL (`raw.githubusercontent.com/<owner>/<repo>/master/docs/elite-arch/<relpath>`).
5. Write `llms-full.txt`: for each entry, a header line (title + published
   URL) then the entry's raw Markdown body, separated by a divider line.
6. Write `llms.txt`: site title/description block, the prominent
   `llms-full.txt` link, then the table of contents grouped by heading
   (mirroring the recursive section hierarchy, with a nested heading level
   for nested subsections like `appendices/how-we-developed-this`).
7. For each ToC entry's description: frontmatter `description` if present,
   else derive from the first non-blank, non-heading paragraph per the
   truncation rule above.
8. Add the new step to `deploy-pages.yml`, before "Build Hugo".

**Files to create/modify**:
- Create: `scripts/generate_llms_full.py`
- Modify: `.github/workflows/deploy-pages.yml` (one new step)

**Testing plan**: see Testing section above — script-level standalone run,
then a local Hugo build, both inspected directly; no automated test suite
applies to this docs-publishing tooling.

**Documentation updates**: none beyond an inline module docstring at the
top of `scripts/generate_llms_full.py` describing purpose, inputs, and
outputs, following `scripts/render_diagrams.py`'s existing docstring
convention.
