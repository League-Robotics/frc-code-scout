---
id: '002'
title: DNS-gated cutover and end-to-end verification
status: done
use-cases:
- SUC-006
depends-on:
- '001'
github-issue: ''
issue: custom-domain-for-llms-root.md
completes_issue: true
---
<!-- CLASI: Before changing code or making plans, review the SE process in CLAUDE.md -->

# DNS-gated cutover and end-to-end verification

## Description

Flip the GitHub Pages custom domain to `frc-code-scout.jointheleague.org`
and verify the deployed site end to end — but **only after** the
stakeholder's DNS CNAME record resolves. This is the one step in the sprint
with a real failure mode: setting the Pages custom domain before DNS
resolves makes GitHub redirect the live site to a hostname that doesn't yet
answer, taking the site down until DNS propagates. The gate check in this
ticket's first acceptance criterion is not optional and must run before any
other step.

Ticket 001 must already be merged or merge-ready (`baseURL` pointed at the
new domain) before this ticket's deploy step, since the deploy that follows
the Pages domain change is what actually serves `llms.txt`/`llms-full.txt`
at the new root.

Following sprint 002 ticket 003's precedent (see
`clasi/sprints/done/002-agent-single-file-dump-of-the-hugo-site/tickets/done/003-verify-end-to-end-site-build-and-deployment.md`),
the deployed-leg checks in this ticket's acceptance criteria can only be
exercised after the sprint branch merges to `master` and Pages redeploys —
merging is the team-lead's `close-sprint` responsibility, not this ticket's.
Those checks are recorded **post-merge** by the team-lead via
`review_sprint_post_close`, exactly as sprint 002 ticket 003's checklist
was completed and annotated after that sprint's merge.

**Blocking condition**: if DNS does not resolve at execution time, this
ticket blocks. Do not set the Pages custom domain, do not guess, do not
proceed to any other acceptance criterion. Report the blocked state to the
stakeholder (via the team-lead) and stop.

## Acceptance Criteria

- [x] **Gate (must pass before anything else in this ticket)**: `dig` or
      `host` for `frc-code-scout.jointheleague.org` resolves to
      `league-robotics.github.io` (a CNAME record, per the issue). If it
      does not resolve, or resolves to something unexpected, this ticket
      blocks here — do not proceed to the next criterion. Report to the
      stakeholder via the team-lead instead of retrying speculatively or
      setting the Pages domain anyway.
      - Verified 2026-07-17T17:5x UTC: `dig +short
        frc-code-scout.jointheleague.org CNAME` returns
        `league-robotics.github.io.`; A records resolve to GitHub Pages IPs
        (185.199.108-111.153 range). Gate passed.
- [x] Ticket 001 confirmed merged (or its changes present on the sprint
      branch about to be merged) before proceeding.
      - Verified: ticket 001 has `status: done` and lives in
        `tickets/done/001-repo-side-url-migration-baseurl-llms-regeneration.md`
        on this sprint branch; its baseURL/llms changes are present here
        ahead of merge.
- [x] GitHub Pages custom domain set:
      `gh api -X PUT repos/League-Robotics/frc-code-scout/pages -f
      cname=frc-code-scout.jointheleague.org` succeeds (or the stakeholder
      has already set it via Settings → Pages → Custom domain — check
      current state with `gh api repos/League-Robotics/frc-code-scout/pages`
      before assuming it needs setting).
      - Verified: `gh api repos/League-Robotics/frc-code-scout/pages` shows
        `build_type: "workflow"` and `cname:
        "frc-code-scout.jointheleague.org"` already set by the
        stakeholder — the PUT step was not needed. `https_enforced: false`
        (certificate still provisioning; tracked in the HTTPS criterion
        below).
- [ ] *(Post-merge, recorded by the team-lead via `review_sprint_post_close`
      — the merge itself happens in `close-sprint`, not in this ticket)*:
      `https://frc-code-scout.jointheleague.org/llms.txt` and
      `/llms-full.txt` return HTTP 200 at the domain root with content
      matching ticket 001's local build output.
      - Deferred: verified against the post-merge deploy; HTTPS
        enforcement pending GitHub certificate issuance. See close report.
- [ ] *(Post-merge)*: the deployed homepage
      (`https://frc-code-scout.jointheleague.org/`) shows the sprint
      002 agent banner pointing at `llms-full.txt`, and at least one other
      page shows the sidebar-footer pointer — both now resolving on the new
      domain.
      - Deferred: verified against the post-merge deploy; HTTPS
        enforcement pending GitHub certificate issuance. See close report.
- [ ] *(Post-merge)*: old `league-robotics.github.io/frc-code-scout/*` URLs
      (e.g. `.../llms-full.txt`, the homepage) redirect (301/302) to the
      corresponding `frc-code-scout.jointheleague.org` URL, so the
      docs-hub entry (which chains through
      `robots.jointheleague.org/frc-code-scout/` → the github.io URL as of
      today) keeps working without its own edit.
      - Deferred: verified against the post-merge deploy; HTTPS
        enforcement pending GitHub certificate issuance. See close report.
- [ ] *(Post-merge)*: HTTPS is enforced
      (`gh api repos/League-Robotics/frc-code-scout/pages` shows
      `https_enforced: true`, or the Settings UI confirms it) once GitHub
      has issued the certificate. If the cert hasn't issued yet at
      verification time (can lag DNS by minutes to an hour), record this
      explicitly as pending rather than marking the criterion done, and
      re-check once it lands.
      - Deferred: verified against the post-merge deploy; HTTPS
        enforcement pending GitHub certificate issuance. See close report.

## Testing

- **Existing tests to run**: none — no application test suite; this is
  infrastructure/config verification (same as sprint 002 ticket 003 and
  sprint 003's post-close pattern).
- **New tests to write**: none.
- **Verification command**: `dig frc-code-scout.jointheleague.org` /
  `host frc-code-scout.jointheleague.org` for the gate check;
  `gh api -X PUT repos/League-Robotics/frc-code-scout/pages -f
  cname=frc-code-scout.jointheleague.org` for the cutover; `curl -sI`
  against the deployed URLs listed above for post-merge verification.

## Implementation Plan

**Approach**:

1. Run the DNS gate check (`dig`/`host`). If it fails, stop and report to
   the stakeholder via the team-lead — do not proceed to any step below.
2. Confirm ticket 001 is merged or merge-ready.
3. Check current Pages config
   (`gh api repos/League-Robotics/frc-code-scout/pages`) to see whether a
   custom domain is already set (the stakeholder's issue notes they may do
   this themselves via Settings → Pages). If not set, set it via
   `gh api -X PUT ... -f cname=frc-code-scout.jointheleague.org`.
4. Hand off to the team-lead's normal `close-sprint` flow to merge the
   sprint branch to `master`, which redeploys the site with the new
   `baseURL` from ticket 001.
5. Once merged and deployed, the team-lead runs the post-merge verification
   checks listed above via `review_sprint_post_close` and records the
   result against this ticket, mirroring sprint 002 ticket 003's
   post-close annotation pattern.
6. If any post-merge check fails, the fix lands as a follow-up ticket or
   issue rather than reopening this one, unless the failure is trivially
   within this ticket's own scope (e.g., the custom domain setting itself
   needs correcting).

**Files to create/modify**: none expected in the repo itself — this ticket
is entirely account/DNS-level configuration and verification. If
verification surfaces a repo-side defect (e.g., a link ticket 001 missed),
the fix lands in the file ticket 001 owns, noted here as a discrepancy
against the plan.

**Testing plan**: the acceptance criteria above are the full test plan —
a pre-cutover DNS gate, the cutover action itself, and post-merge
deployed-site verification.

**Documentation updates**: none required. The `custom-domain-for-llms-root.md`
issue is closed/archived by this ticket's completion per
`completes_issue: true`.
