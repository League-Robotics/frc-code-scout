---
status: done
sprint: '001'
tickets:
- 001-001
- 001-002
- 001-003
---

# Publish FRC Code Scout to the League Robotics docs hub

Get FRC Code Scout listed as an entry on the League Robotics docs hub at
robots.jointheleague.org, so visitors to the main robots site can find and reach
the FRC Code Scout web page.

Follow the hub publishing spec at <https://robots.jointheleague.org/publishing/>:

1. **`docs/wiki/_subsystem.yml`** — subsystem metadata: stable `name` key
   (`frc-code-scout`), display `title`, one-sentence `blurb`.
2. **One `docs/wiki/` page** — says what FRC Code Scout is for, why you would go
   there, and links to the published site at
   <https://league-robotics.github.io/frc-code-scout/>. Required frontmatter:
   `title` and `blurb`; optional `order`, `slug`, `updated`, `tags`.
3. **`.github/workflows/notify-docs-hub.yml`** — the hub-notify workflow from the
   publishing spec, adapted to trigger on this repo's `master` default branch
   (spec template uses `main`). Uses org-level `vars.DOCS_HUB_APP_ID` and
   `secrets.DOCS_HUB_APP_PRIVATE_KEY` via `actions/create-github-app-token@v1` —
   no repo-local secrets to create.
4. **`AGENTS.md` update** — tell future agents that `docs/wiki/` is the source of
   truth published to the hub, and point at the publishing spec.
5. **Registration** — PR to `League-Robotics/League-Robotics.github.io` adding
   this repo to `subsystems.yml` (`name: frc-code-scout`,
   `repo: League-Robotics/frc-code-scout`, `branch: master`), then merge it
   (we have admin on the hub repo).

## Acceptance

- FRC Code Scout appears as an entry on the robots.jointheleague.org hub.
- The entry's link leads to the FRC Code Scout published site.
- A push touching `docs/wiki/**` on `master` triggers the notify workflow
  successfully.
