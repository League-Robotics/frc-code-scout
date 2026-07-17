---
status: in-progress
sprint: '005'
tickets:
- 005-001
- 005-002
---

# Add robots.txt advertising the agent dump

Serve a `robots.txt` at the site root. Currently it 404s (crawler default:
allow all), so this is additive discovery, not a policy fix:

- Enable Hugo's `enableRobotsTXT = true` in `site/hugo.toml` and add a
  `site/layouts/robots.txt` template so the domain comes from `baseURL` —
  never hardcoded a second time (same rule the llms generator follows).
- Contents: `User-agent: *` / `Allow: /`; a `Sitemap:` line pointing at the
  generated `sitemap.xml`; comment lines telling agents the whole site is
  available at `/llms-full.txt` (index at `/llms.txt`) — robots.txt is often
  an agent's first fetch, making it another conspicuous pointer.

Stakeholder approved 2026-07-17 ("all right", following the robots.txt
recommendation; confirmed "Do that and then re-publish").

## Acceptance

- Deployed `https://frc-code-scout.jointheleague.org/robots.txt` returns 200
  with Allow-all, the Sitemap line, and the llms pointers.
- Domain appears only via Hugo's `baseURL` templating, not hardcoded.
- `sitemap.xml` still serves 200.
