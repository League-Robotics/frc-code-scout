# data/

- `manifests/` — version-controlled team lists (the source of truth). Edit these.
- `repos/`  — downloaded team code. **Gitignored, reproducible, disposable.**
- `index/`  — generated symbol + rubric-hit JSON. **Gitignored, regenerable.**

`repos/` and `index/` are rebuilt by `scripts/clone_corpus.sh` + `scripts/build_index.sh`.
Set `SCOUT_DATA` to relocate them onto local disk (recommended if this repo is on a
cloud-synced/mounted folder — git operations fail there). Safe to delete their contents
anytime.
