---
name: update-corpus
description: Refresh the dataset so scores reflect current code - re-pull every tracked repo, re-discover each team's repos on GitHub (catching new season repos), and flag teams whose latest season repo changed. Use at the start of a new season or when the user says "update", "refresh the data", or "is this still current".
---

# Update / self-refresh the corpus

Keep scores current as teams push new code and start new seasons.

## Steps
1. **Refresh tracked code** — re-pull every repo in the manifest. Easiest: delete
   `$SCOUT_DATA/repos` (or `data/repos`) and re-run `scripts/clone_corpus.sh`
   (it skips existing dirs, so to force-refresh, remove first). Use `--budget` to chunk.
2. **Re-discover per team** — for each `github_owner` in `data/manifests/frc-teams.tsv`,
   run `scripts/discover_repos.sh --owner <owner>` and diff the returned repo list against
   the manifest's `repos` column. Append newly-found season repos (e.g. a fresh
   `Rebuilt2027`) to the manifest.
3. **Find brand-new teams** — `scripts/discover_repos.sh --search "<region> FRC 20XX"`.
4. **Re-index** — `scripts/build_index.sh`.
5. **Flag changes** — report which teams have a newer latest-season repo than last run, so
   `analyze-team` / the survey can be re-run only where it matters.

The manifest is the source of truth. Downloaded code and indexes are disposable and always
rebuildable from it — never edit them by hand.
