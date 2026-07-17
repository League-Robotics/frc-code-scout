---
status: pending
sprint: '002'
---

# Agent-oriented single-file dump of the whole Hugo site

When the Hugo site builds (`site/`, content mounted from `docs/elite-arch/`),
also produce one big concatenated document containing every page of the site
in reading order, published to the web alongside the site (e.g.
`/llms-full.txt` or similar — this is the emerging llms.txt convention for
agent-friendly site dumps).

The main site must conspicuously advertise the dump to AI agents: at the top
of the homepage and in other conspicuous places, text along the lines of
"Agents: download this single file instead — it has everything" with the URL,
so agents that land on the main site URL don't have to crawl page links.

Requirements:

- **Programmatically generated at build time** — produced by the same build
  that publishes the Hugo site, never hand-maintained, so it cannot drift
  from the published content.
- **One document, whole site** — all pages collected into a single file in
  a sensible reading order (book order: parts, then chapters).
- **Discoverable by agents from the main URL** — a conspicuous pointer at
  the top of the homepage, plus other conspicuous placements (e.g. site
  footer/nav on every page).
- **Hosting is flexible** — served from the published site itself (e.g.
  `https://league-robotics.github.io/frc-code-scout/llms-full.txt`) or a
  file committed/generated in the GitHub repo and linked from the site;
  either is acceptable as long as it is generated, current, and linked.

Implementation note (candidate approach, not binding): Hugo custom output
formats can render an additional plain-text/markdown output for the home
page that concatenates all site content at build time, which keeps the dump
inside the existing `deploy-pages.yml` publish pipeline with no extra steps.

## Acceptance

- Building the site produces the single-file dump automatically.
- The dump contains the full content of every published page.
- The published homepage conspicuously tells agents where to fetch it.
- The pointer appears in at least one site-wide location (footer or nav)
  in addition to the homepage.
