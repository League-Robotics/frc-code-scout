#!/usr/bin/env python3
"""Generate llms-full.txt and llms.txt for the Hugo site, in full book order.

Two outputs, both written to site/static/ so Hugo's normal static-file copy
carries them verbatim into site/public/ with no template wiring:

  llms-full.txt — every page's raw Markdown under docs/elite-arch/, each
                   prefixed with a title + canonical published-URL header,
                   concatenated in full recursive book order.
  llms.txt      — site title + description, a "For agents" admonition
                   instructing agents to fetch /llms-full.txt or a chapter's
                   raw-Markdown link rather than crawl the HTML pages, then a
                   full table of contents grouped by part/section headings:
                   one entry per page linking directly to its raw-GitHub-
                   markdown URL (no published-site HTML link) plus a
                   one-line description (frontmatter `description` if
                   present, otherwise derived from the page's first prose
                   paragraph).

"Book order" here is a fully recursive depth-first walk of docs/elite-arch/,
sorted by frontmatter `weight` at every level and recursing into nested
subsections (e.g. appendices/how-we-developed-this/,
appendices/lessons-from-outside/) — deeper than the two-level
$allPages construction in site/themes/hugo-theme-voidmain's baseof.html,
which only walks top-level section -> its direct .Pages and would miss
pages nested under a subsection.

Frontmatter is parsed with a small stdlib parser (split on the `---`
delimiters, parse simple `key: value` lines) — no `pyyaml` or other new
dependency. baseURL and the GitHub owner/repo are read out of
site/hugo.toml via a small regex extractor, never hardcoded a second time.

Run standalone: `python3 scripts/generate_llms_full.py`
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "docs/elite-arch"
HUGO_TOML = REPO / "site/hugo.toml"
DST = REPO / "site/static"

DESCRIPTION_MAX = 160

# The raw-GitHub-markdown link is pinned to `master`, matching this repo's
# default branch and deploy-pages.yml's `on: push: branches: [main, master]`
# trigger as the precedent (see clasi/sprints/002-.../sprint.md, Design
# Rationale: "each llms.txt entry links to the published page...").
RAW_BRANCH = "master"


# ── hugo.toml extraction ──────────────────────────────────────────────────

def extract_toml_value(text: str, key: str) -> str | None:
    """Regex-extract a scalar `key = "value"` line from hugo.toml.

    Handles both top-level and [params]-nested keys; this corpus's hugo.toml
    only defines each of baseURL/title/description/repoUrl once, so a plain
    first-match search (not TOML-section-aware) is sufficient and avoids a
    TOML-parsing dependency for four scalar keys.
    """
    m = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return m.group(1) if m else None


def load_site_config() -> dict:
    text = HUGO_TOML.read_text()
    base_url = extract_toml_value(text, "baseURL")
    title = extract_toml_value(text, "title")
    description = extract_toml_value(text, "description")
    repo_url = extract_toml_value(text, "repoUrl")
    if not base_url or not repo_url:
        raise SystemExit(f"could not extract baseURL/repoUrl from {HUGO_TOML}")
    if not base_url.endswith("/"):
        base_url += "/"
    owner, _, repo = repo_url.rstrip("/").rpartition("/")
    owner = owner.rsplit("/", 1)[-1]
    return {
        "base_url": base_url,
        "title": title or "",
        "description": description or "",
        "owner": owner,
        "repo": repo,
    }


# ── frontmatter parsing ───────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split `---\\n<frontmatter>\\n---\\n<body>` into (frontmatter dict, body).

    Only simple `key: value` scalar lines are parsed (title, weight,
    description) — this corpus's frontmatter has no nested structures.
    Matching double- or single-quoted values have the quotes stripped.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            frontmatter: dict = {}
            for raw_line in lines[1:i]:
                line = raw_line.rstrip("\n")
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                frontmatter[key] = value
            body = "".join(lines[i + 1:])
            return frontmatter, body
    return {}, text


def get_weight(frontmatter: dict) -> float:
    """Sort key for book order.

    Pages/sections with no explicit `weight` (only
    appendices/lessons-from-outside/_index.md, in the current corpus) sort
    after their weighted siblings rather than at Hugo's int-zero default —
    that page's own content (and appendices/_index.md's own listing) frames
    it as a closing, "shelved with the appendices" section, not an opener.
    """
    raw = frontmatter.get("weight")
    if raw is None or raw == "":
        return float("inf")
    try:
        return float(raw)
    except ValueError:
        return float("inf")


# ── markdown -> description ───────────────────────────────────────────────

_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_STAR_RE = re.compile(r"\*([^*]+)\*")
_BOLD_UNDER_RE = re.compile(r"__([^_]+)__")
_ITALIC_UNDER_RE = re.compile(r"_([^_]+)_")


def strip_markdown(text: str) -> str:
    text = _LINK_RE.sub(r"\1", text)
    text = _CODE_RE.sub(r"\1", text)
    text = _BOLD_RE.sub(r"\1", text)
    text = _ITALIC_STAR_RE.sub(r"\1", text)
    text = _BOLD_UNDER_RE.sub(r"\1", text)
    text = _ITALIC_UNDER_RE.sub(r"\1", text)
    return text


def truncate(text: str, limit: int = DESCRIPTION_MAX) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    boundary = cut.rfind(" ")
    if boundary > 0:
        cut = cut[:boundary]
    return cut.rstrip(" .,;:") + "…"


def first_prose_paragraph(body: str) -> str:
    """First non-blank, non-heading, non-rule paragraph of a page's body."""
    buf: list[str] = []
    in_fence = False
    for raw_line in body.split("\n"):
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            if buf:
                break
            continue
        if stripped.startswith("#"):
            continue
        if stripped in ("---", "***", "___"):
            continue
        buf.append(stripped)
    return " ".join(buf)


def derive_description(frontmatter: dict, body: str) -> str:
    explicit = frontmatter.get("description")
    if explicit:
        return explicit
    paragraph = first_prose_paragraph(body)
    if not paragraph:
        return ""
    plain = strip_markdown(paragraph)
    plain = " ".join(plain.split())
    return truncate(plain)


# ── recursive book-order walk ─────────────────────────────────────────────

class Entry:
    def __init__(self, path: Path, kind: str, depth: int, frontmatter: dict, body: str):
        self.path = path
        self.relpath = path.relative_to(SRC).as_posix()
        self.kind = kind  # "home" | "section" | "page"
        self.depth = depth
        self.frontmatter = frontmatter
        self.body = body
        self.title = frontmatter.get("title") or self.relpath
        self.description = derive_description(frontmatter, body)


def make_entry(path: Path, kind: str, depth: int) -> Entry:
    frontmatter, body = parse_frontmatter(path.read_text())
    return Entry(path, kind, depth, frontmatter, body)


def walk_dir(dir_path: Path, depth: int) -> list[Entry]:
    """Depth-first walk of dir_path's children, sorted by frontmatter weight.

    For each directory: its own _index.md becomes a "section" entry (the
    section landing), then its child files ("page" entries) and child
    subdirectories (recursed into, sorted alongside the files) are appended
    in weight order. This is deliberately deeper than baseof.html's
    two-level $allPages sidebar construction — it recurses into nested
    subsections such as appendices/how-we-developed-this/.
    """
    dirs = []
    files = []
    for child in dir_path.iterdir():
        if child.name == "_index.md":
            continue
        if child.is_dir():
            index_path = child / "_index.md"
            if not index_path.exists():
                continue
            frontmatter, _ = parse_frontmatter(index_path.read_text())
            dirs.append((get_weight(frontmatter), child.name, child))
        elif child.suffix == ".md":
            frontmatter, _ = parse_frontmatter(child.read_text())
            files.append((get_weight(frontmatter), child.name, child))

    children = sorted(dirs + files, key=lambda t: (t[0], t[1]))

    entries: list[Entry] = []
    for weight, name, child in children:
        if child.is_dir():
            entries.append(make_entry(child / "_index.md", "section", depth))
            entries.extend(walk_dir(child, depth + 1))
        else:
            entries.append(make_entry(child, "page", depth))
    return entries


def build_book_order() -> list[Entry]:
    home_index = SRC / "_index.md"
    entries = [make_entry(home_index, "home", 0)]
    entries.extend(walk_dir(SRC, 1))
    return entries


# ── URL computation ───────────────────────────────────────────────────────

def published_url(entry: Entry, base_url: str) -> str:
    relpath = entry.relpath
    if relpath == "_index.md":
        url_path = ""
    elif relpath.endswith("/_index.md"):
        url_path = relpath[: -len("_index.md")]
    else:
        url_path = relpath[: -len(".md")] + "/"
    return base_url + url_path


def raw_url(entry: Entry, owner: str, repo: str) -> str:
    return (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{RAW_BRANCH}"
        f"/docs/elite-arch/{entry.relpath}"
    )


# ── llms-full.txt ─────────────────────────────────────────────────────────

# A plain `---` line is Markdown's own thematic-break syntax and appears
# verbatim inside many pages' bodies (169 occurrences across the corpus at
# last count), so it cannot double as an unambiguous per-page divider. An
# HTML comment does not collide with anything in the corpus (no page uses
# HTML comments) and stays out of the way of a reader just reading top to
# bottom.
PAGE_DIVIDER = "\n\n<!-- ============================================================ -->\n\n"


def render_llms_full(entries: list[Entry], config: dict) -> str:
    parts = []
    for entry in entries:
        url = published_url(entry, config["base_url"])
        parts.append(f"# {entry.title}\n\n{url}\n\n{entry.body.strip()}\n")
    return PAGE_DIVIDER.join(parts) + "\n"


# ── llms.txt ───────────────────────────────────────────────────────────────

def toc_entry_line(entry: Entry, config: dict) -> str:
    raw = raw_url(entry, config["owner"], config["repo"])
    description = f": {entry.description}" if entry.description else ""
    return f"- [{entry.title}]({raw}){description}"


def render_llms(entries: list[Entry], config: dict) -> str:
    home = entries[0]
    rest = entries[1:]

    lines = [f"# {config['title']}", ""]
    if config["description"]:
        lines.append(config["description"])
        lines.append("")

    llms_full_url = config["base_url"] + "llms-full.txt"
    lines.append("## For agents")
    lines.append("")
    lines.append(
        f"**Fetch [{llms_full_url}]({llms_full_url}) — it contains the complete "
        "content of every page below in a single request.** If you only need one "
        "chapter, follow that entry's raw-Markdown link in the Table of Contents "
        "below instead. **Do not crawl the HTML pages on this site**: every page's "
        "full content already lives in the raw Markdown these links point to, so "
        "the HTML adds nothing but site navigation on top of content you already "
        "have a direct link to."
    )
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    lines.append(toc_entry_line(home, config))
    lines.append("")

    def ensure_blank_line() -> None:
        if lines[-1] != "":
            lines.append("")

    prev_depth = 0
    for entry in rest:
        if entry.kind == "section" and entry.depth == 1:
            ensure_blank_line()
            lines.append(f"## {entry.title}")
            lines.append("")
            lines.append(toc_entry_line(entry, config))
        elif entry.kind == "section" and entry.depth >= 2:
            ensure_blank_line()
            lines.append(f"### {entry.title}")
            lines.append("")
            lines.append(toc_entry_line(entry, config))
        else:
            if entry.depth < prev_depth:
                ensure_blank_line()
            lines.append(toc_entry_line(entry, config))
        prev_depth = entry.depth

    return "\n".join(lines) + "\n"


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    config = load_site_config()
    entries = build_book_order()

    DST.mkdir(parents=True, exist_ok=True)

    llms_full_path = DST / "llms-full.txt"
    llms_full_path.write_text(render_llms_full(entries, config))

    llms_path = DST / "llms.txt"
    llms_path.write_text(render_llms(entries, config))

    print(f"{len(entries)} page(s) -> {llms_full_path.relative_to(REPO)}")
    print(f"{len(entries)} page(s) -> {llms_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
