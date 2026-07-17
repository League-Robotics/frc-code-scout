---
status: in-progress
sprint: '004'
tickets:
- 004-001
- 004-002
---

# Move the site to frc-code-scout.jointheleague.org so llms.txt sits at the domain root

An agent testing the published site completely missed `llms.txt`/`llms-full.txt`.
Root cause: agents probe for `llms.txt` at the **domain root** (`/llms.txt`), and
as a GitHub Pages *project* site the files live under a path
(`robots.jointheleague.org/frc-code-scout/llms.txt`), where the convention never
looks. Giving the repo its own hostname puts them at the root.

Target: `https://frc-code-scout.jointheleague.org/` via a DNS CNAME
`frc-code-scout.jointheleague.org → league-robotics.github.io`.

## Division of work

- **Stakeholder (external, in progress)**: create the DNS CNAME record in
  jointheleague.org's DNS. Instructions were provided 2026-07-17.
- **Repo side** (safe to stage before DNS exists, on the sprint branch):
  - `site/hugo.toml` — `baseURL = "https://frc-code-scout.jointheleague.org/"`.
    The llms generator reads baseURL from this file, so `llms.txt` /
    `llms-full.txt` links update automatically; verify by regenerating.
  - `docs/wiki/overview.md` — update published-site links to the new domain
    (grep confirmed these are the only two files hardcoding the old URLs
    outside archived sprint docs and generated outputs).
- **Cutover** (gated on the DNS record resolving; check with `dig`/`host`):
  - Set the Pages custom domain on the repo:
    `gh api -X PUT repos/League-Robotics/frc-code-scout/pages -f cname=frc-code-scout.jointheleague.org`
    (or stakeholder does Settings → Pages → Custom domain).
  - Merge the sprint branch to master (fires the normal deploy).
  - Verify: site serves at the new root; `https://frc-code-scout.jointheleague.org/llms.txt`
    and `/llms-full.txt` return 200 with correct self-referencing URLs; old
    `league-robotics.github.io/frc-code-scout/*` URLs redirect to the new
    domain (keeps hub links working); Enforce HTTPS enabled once GitHub's
    cert is issued (may lag DNS by minutes to an hour).

## Constraints

- **Do not set the Pages custom domain before DNS resolves** — GitHub starts
  redirecting the live site to the new hostname immediately, which would take
  the site down until DNS lands.
- Stakeholder has approved and instructed execution ("give me instructions
  for my end, then you do the work on your end"); only the DNS record itself
  is on the stakeholder.

## Acceptance

- `https://frc-code-scout.jointheleague.org/llms.txt` and `/llms-full.txt`
  return HTTP 200 at the domain root, with entries linking to the new domain.
- The homepage banner and sidebar-footer pointers resolve on the new domain.
- Old published URLs redirect to the new domain (hub entry keeps working).
- HTTPS enforced once the certificate is provisioned.
