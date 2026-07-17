---
id: '002'
title: Deploy verification for llms.txt and robots.txt
status: done
use-cases:
- SUC-007
- SUC-008
depends-on:
- '001'
github-issue: ''
issue:
- llms-txt-raw-only-admonition.md
- add-robots-txt.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# Deploy verification for llms.txt and robots.txt

## Description

Both linked issues' acceptance criteria are phrased against the **deployed**
site, not the local build — `llms.txt` "Deployed... opens with the
admonition..." and robots.txt "Deployed
`https://frc-code-scout.jointheleague.org/robots.txt` returns 200...". Those
checks can only be exercised after the sprint branch merges to `master` and
GitHub Pages redeploys.

Following sprint 004 ticket 002's precedent (see
`clasi/sprints/done/004-custom-domain-frc-code-scout-jointheleague-org-for-llms-root-discovery/tickets/done/002-dns-gated-cutover-and-end-to-end-verification.md`),
the deployed-leg checks in this ticket's acceptance criteria are recorded
**post-merge** by the team-lead via `review_sprint_post_close` — merging is
the team-lead's `close-sprint` responsibility, not this ticket's own step.

Unlike sprint 004, there is no DNS or account-level external gate here: both
of ticket 001's changes are pure repo-side content/config, so this ticket
has no blocking condition analogous to sprint 004's DNS check — it is purely
post-merge verification, plus the stakeholder's explicit follow-up
instruction to re-publish once the changes land ("Do that and then
re-publish").

`completes_issue: true` — this ticket's post-merge verification is what
actually satisfies both linked issues' acceptance criteria, so both issues
archive when this ticket completes.

## Acceptance Criteria

- [x] Ticket 001 confirmed merged (or its changes present on the sprint
      branch about to be merged) before proceeding.
      - Verified: ticket 001 has `status: done` and lives in
        `tickets/done/001-llms-txt-raw-only-rewrite-and-robots-txt-template.md`
        on this sprint branch; its llms.txt/robots.txt changes are present
        here ahead of merge.
- [ ] *(Post-merge, recorded by the team-lead via `review_sprint_post_close`)*:
      `https://frc-code-scout.jointheleague.org/llms.txt` returns HTTP 200,
      opens with the admonition immediately after the title/description
      block, and every Table of Contents entry links only to
      `raw.githubusercontent.com` — zero
      `frc-code-scout.jointheleague.org` HTML page URLs remain anywhere in
      the ToC.
      - Deferred: verified against the post-merge deploy per sprint-004
        precedent. See close report.
- [ ] *(Post-merge)*: `https://frc-code-scout.jointheleague.org/llms-full.txt`
      returns HTTP 200 with content matching ticket 001's local build
      output (same per-page structure, unchanged apart from the
      regeneration pass).
      - Deferred: verified against the post-merge deploy per sprint-004
        precedent. See close report.
- [ ] *(Post-merge)*: `https://frc-code-scout.jointheleague.org/robots.txt`
      returns HTTP 200 with an allow-all rule, a `Sitemap:` line, and
      comment pointers to `/llms-full.txt` and `/llms.txt`.
      - Deferred: verified against the post-merge deploy per sprint-004
        precedent. See close report.
- [ ] *(Post-merge)*: `https://frc-code-scout.jointheleague.org/sitemap.xml`
      still returns HTTP 200 (non-regression check for the robots.txt
      change).
      - Deferred: verified against the post-merge deploy per sprint-004
        precedent. See close report.
- [ ] *(Post-merge)*: the site has been re-published per the stakeholder's
      explicit follow-up instruction ("Do that and then re-publish").
      - Deferred: verified against the post-merge deploy per sprint-004
        precedent. See close report.
- [ ] If any post-merge check fails, the fix lands as a follow-up ticket or
      issue rather than reopening this one, unless the failure is trivially
      within this ticket's own scope.
      - Deferred: verified against the post-merge deploy per sprint-004
        precedent. See close report.

## Testing

- **Existing tests to run**: none — no application test suite; this is
  infrastructure/content verification (same precedent as sprint 002 ticket
  003 and sprint 004 ticket 002's post-close pattern).
- **New tests to write**: none.
- **Verification command**: `curl -sI` against each deployed URL listed
  above (`llms.txt`, `llms-full.txt`, `robots.txt`, `sitemap.xml`); fetch
  and inspect `llms.txt`'s body for the admonition and entry format.

## Implementation Plan

**Approach**:

1. Confirm ticket 001 is merged or merge-ready.
2. Hand off to the team-lead's normal `close-sprint` flow to merge the
   sprint branch to `master`, which redeploys the site with ticket 001's
   changes.
3. Once merged and deployed, the team-lead runs the post-merge verification
   checks listed above via `review_sprint_post_close` and records the
   result against this ticket, mirroring sprint 004 ticket 002's post-close
   annotation pattern.
4. If any post-merge check fails, the fix lands as a follow-up ticket or
   issue rather than reopening this one, unless the failure is trivially
   within this ticket's own scope (e.g., a missed entry in the `llms.txt`
   rewrite).

**Files to create/modify**: none expected in the repo itself — this ticket
is entirely deployed-site verification. If verification surfaces a
repo-side defect, the fix lands in the file ticket 001 owns, noted here as
a discrepancy against the plan.

**Testing plan**: the acceptance criteria above are the full test plan —
confirm ticket 001 merged, then post-merge deployed-site verification of
all four URLs plus the re-publish confirmation.

**Documentation updates**: none required beyond the deployed artifacts
themselves. Both `llms-txt-raw-only-admonition.md` and `add-robots-txt.md`
are closed/archived by this ticket's completion per `completes_issue: true`.
