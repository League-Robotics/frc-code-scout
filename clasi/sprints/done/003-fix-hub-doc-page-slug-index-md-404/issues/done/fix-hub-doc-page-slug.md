---
status: done
sprint: '003'
tickets:
- 003-001
---

# Fix hub doc page 404: rename docs/wiki/index.md to overview.md

Post-close verification of sprint 001 (publish to League docs hub) found the hub
lists our doc page but its URL 404s:
<https://robots.jointheleague.org/subsystems/frc-code-scout/index/> serves the
GitHub Pages 404 page.

Root cause: the page file is named `docs/wiki/index.md`; the hub's static-site
generator treats `index.*` as a directory/section index, so the rendered page
collides with the generated subsystem landing page and is dropped. Every working
subsystem (e.g. ros-deploy) uses non-index filenames like `overview.md`.

Fix forward (per sprint 001 ticket 003's post-close section):

1. `git mv docs/wiki/index.md docs/wiki/overview.md` (keep frontmatter; title,
   blurb, order, updated, tags unchanged; bump `updated` to today).
2. While editing: change the page's outbound link from
   `https://league-robotics.github.io/frc-code-scout/` (301 → http downgrade) to
   the canonical `https://robots.jointheleague.org/frc-code-scout/` (serves 200
   over https directly).
3. Push to master — the notify-docs-hub workflow re-pings the hub.

## Acceptance

- <https://robots.jointheleague.org/subsystems/frc-code-scout/overview/> returns
  200 with the page content after the hub rebuilds.
- The page links to <https://robots.jointheleague.org/frc-code-scout/>.
- The hub homepage card still lists FRC Code Scout.
