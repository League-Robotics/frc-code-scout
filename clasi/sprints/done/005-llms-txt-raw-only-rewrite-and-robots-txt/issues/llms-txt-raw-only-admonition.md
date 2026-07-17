---
status: in-progress
sprint: '005'
tickets:
- 005-001
- 005-002
---

# llms.txt: strong raw-markdown admonition, remove HTML page links

Rewrite what `scripts/generate_llms_full.py` emits for `llms.txt`:

1. **Strong admonition at the top** (right after the title/description block):
   agents should strongly prefer `llms-full.txt` (everything in one fetch) or
   the per-chapter raw markdown links below — NOT the HTML web pages. The
   markdown files contain the full content of every page; the HTML adds only
   navigation chrome. Phrase it as a direct instruction to agents.
2. **Remove HTML published-page links from the ToC entirely.** Each entry
   becomes: title linked to the raw GitHub markdown URL, then the
   description — no published-site link, no separate `(raw)` suffix.

Stakeholder's words (2026-07-17): "add a strong admonition that agents should
strongly prefer to use the raw chapters or the full llms-full, rather than
going to the web pages. In fact, I would just take llms.txt and remove
references to the HTML webpages. The full content of those is in the markdown
files, and you've got a reference to the markdown files. They don't need to
go there to get them."

Scope: `llms.txt` output only. `llms-full.txt` (including its per-page
canonical-URL headers) and the site's homepage banner / footer pointers stay
as they are.

## Acceptance

- Deployed `llms.txt` opens with the admonition and links `llms-full.txt`
  prominently.
- No `frc-code-scout.jointheleague.org` HTML page URLs remain in the ToC
  entries — every entry links only to `raw.githubusercontent.com` markdown.
- Descriptions and part/section grouping unchanged.
- `llms-full.txt` byte-format unchanged apart from regeneration.
