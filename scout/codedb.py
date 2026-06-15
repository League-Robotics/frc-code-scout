"""Parse the corpus with tree-sitter and load it into a single DuckDB database.

Builds a queryable warehouse of the corpus:
  - analysis tables (files / symbols / imports), each row DENORMALIZED with
    team, year, repo, source_file and the full file path (per the requirement);
  - metadata tables (teams / epa / repos / commits / commit_files) from the
    JSON the corpus builder already produced, so code can be joined to EPA.

Only imported lazily (from scout.cli.cmd_index_db), so the stdlib-only `build`
command keeps working without duckdb / tree-sitter installed.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import duckdb
from tree_sitter import Parser
from tree_sitter_language_pack import get_language

from . import config

# --- tree-sitter parser cache ----------------------------------------------
_PARSERS: dict[str, Parser] = {}


def _parser(lang: str) -> Parser:
    p = _PARSERS.get(lang)
    if p is None:
        p = Parser(get_language(lang))
        _PARSERS[lang] = p
    return p


# Node type -> normalized symbol kind, per language.
_KINDS = {
    "java": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "record_declaration": "record",
        "annotation_type_declaration": "annotation",
        "method_declaration": "method",
        "constructor_declaration": "constructor",
        "field_declaration": "field",
    },
    "kotlin": {
        "class_declaration": "class",  # refined to interface/enum below
        "object_declaration": "object",
        "function_declaration": "function",  # -> method if inside a type
        "property_declaration": "property",
    },
    "cpp": {
        "class_specifier": "class",
        "struct_specifier": "struct",
        "enum_specifier": "enum",
        "namespace_definition": "namespace",
        "function_definition": "function",  # -> method if inside a class/struct
    },
    "python": {
        "class_definition": "class",
        "function_definition": "function",  # -> method if inside a class
    },
}

_IMPORT_TYPES = {
    "java": {"import_declaration"},
    "kotlin": {"import_header"},
    "cpp": {"preproc_include"},
    "python": {"import_statement", "import_from_statement"},
}

# Annotation / decorator nodes (the rubric needs @AutoLog, @Logged, @Test, @state).
_ANNOTATION_TYPES = {
    "java": {"marker_annotation", "annotation"},
    "kotlin": {"annotation"},
    "cpp": set(),
    "python": {"decorator"},
}

# Call nodes (the rubric needs addVisionMeasurement, processInputs, assertEquals, ...).
_CALL_TYPES = {
    "java": {"method_invocation"},
    "kotlin": {"call_expression"},
    "cpp": {"call_expression"},
    "python": {"call"},
}

# Declaration kinds that make an enclosed function a "method".
_TYPELIKE = {"class", "interface", "enum", "record", "struct", "object", "annotation"}
_IDENT = {"type_identifier", "simple_identifier", "identifier"}


def _txt(src: bytes, n) -> str:
    return src[n.start_byte:n.end_byte].decode("utf-8", "replace")


def _name(lang: str, n, src: bytes) -> str | None:
    nm = n.child_by_field_name("name")
    if nm is not None:
        return _txt(src, nm)
    if lang == "kotlin":
        for c in n.children:  # class/function: direct identifier child
            if c.type in _IDENT:
                return _txt(src, c)
        for c in n.children:  # property: identifier under variable_declaration
            for gc in c.children:
                if gc.type in _IDENT:
                    return _txt(src, gc)
    if lang == "cpp" and n.type == "function_definition":
        d = n.child_by_field_name("declarator")
        for _ in range(6):
            if d is None:
                break
            if d.type in ("identifier", "field_identifier", "qualified_identifier",
                          "destructor_name", "operator_name", "type_identifier"):
                return _txt(src, d)
            nxt = d.child_by_field_name("declarator")
            if nxt is None:
                nxt = next((c for c in d.children
                            if "declarator" in c.type or c.type in _IDENT), None)
            d = nxt
    return None


def _kotlin_refine(n) -> str | None:
    """Kotlin class_declaration is class/interface/enum — disambiguate by token."""
    types = {c.type for c in n.children}
    if "interface" in types:
        return "interface"
    mods = next((c for c in n.children if c.type == "modifiers"), None)
    if mods and any(c.type == "enum" for c in mods.children):
        return "enum"
    return "class"


def _import_target(lang: str, n, src: bytes) -> tuple[str, str]:
    raw = _txt(src, n).strip().splitlines()[0][:200]
    if lang == "java":
        t = raw.removeprefix("import").strip().removeprefix("static").strip().rstrip(";").strip()
    elif lang == "kotlin":
        t = raw.removeprefix("import").strip()
    elif lang == "cpp":
        t = next((_txt(src, c).strip() for c in n.children
                  if c.type in ("system_lib_string", "string_literal")),
                 raw.removeprefix("#include").strip())
    elif lang == "python":
        t = raw[5:].split(" import ")[0].strip() if raw.startswith("from ") \
            else raw.removeprefix("import").strip()
    else:
        t = raw
    return t, raw


def _annotation_name(lang: str, n, src: bytes) -> str | None:
    """Name of an annotation / decorator (last component, no '@' or args)."""
    if lang == "java":
        nm = n.child_by_field_name("name")
        return _txt(src, nm).split(".")[-1] if nm else None
    if lang == "python":  # decorator wraps identifier / attribute / call
        for c in n.children:
            if c.type == "identifier":
                return _txt(src, c)
            if c.type == "attribute":
                a = c.child_by_field_name("attribute")
                return _txt(src, a) if a else _txt(src, c).split(".")[-1]
            if c.type == "call":
                return _callee_name("python", c, src)
        return None
    if lang == "kotlin":  # best-effort: first type_identifier descendant
        def find(node, d=0):
            if d > 3:
                return None
            if node.type == "type_identifier":
                return _txt(src, node)
            for c in node.children:
                r = find(c, d + 1)
                if r:
                    return r
            return None
        return find(n)
    return None


def _callee_name(lang: str, n, src: bytes) -> str | None:
    """The called method/function name (no receiver, no args)."""
    if lang == "java":
        nm = n.child_by_field_name("name")
        return _txt(src, nm) if nm else None
    if lang == "python":
        f = n.child_by_field_name("function")
        if f is None:
            return None
        if f.type == "identifier":
            return _txt(src, f)
        if f.type == "attribute":
            a = f.child_by_field_name("attribute")
            return _txt(src, a) if a else None
        return None
    if lang == "cpp":
        f = n.child_by_field_name("function")
        if f is None:
            return None
        if f.type == "identifier":
            return _txt(src, f)
        if f.type == "field_expression":
            a = f.child_by_field_name("field")
            return _txt(src, a) if a else None
        if f.type == "qualified_identifier":
            nm = f.child_by_field_name("name")
            return _txt(src, nm) if nm else _txt(src, f).split("::")[-1]
        return None
    if lang == "kotlin":
        if not n.children:
            return None
        head = n.children[0]
        if head.type == "simple_identifier":
            return _txt(src, head)
        if head.type == "navigation_expression":
            sufs = [c for c in head.children if c.type == "navigation_suffix"]
            tail = sufs[-1] if sufs else head
            si = next((g for g in tail.children if g.type == "simple_identifier"), None)
            return _txt(src, si) if si else None
        return None
    return None


def extract(lang: str, src: bytes):
    """Parse source bytes; return (symbols, imports, annotations, calls, lines, ok).

    annotations/calls are {name: count} dicts aggregated per file.
    """
    tree = _parser(lang).parse(src)
    root = tree.root_node
    symbols: list[dict] = []
    imports: list[tuple[str, str]] = []
    annotations: dict[str, int] = {}
    calls: dict[str, int] = {}
    kinds = _KINDS[lang]
    imp_types = _IMPORT_TYPES[lang]
    ann_types = _ANNOTATION_TYPES[lang]
    call_types = _CALL_TYPES[lang]
    stack: list[tuple[str, str | None]] = []

    def visit(n):
        pushed = False
        if n.type in imp_types:
            imports.append(_import_target(lang, n, src))
        elif n.type in ann_types:
            name = _annotation_name(lang, n, src)
            if name:
                annotations[name] = annotations.get(name, 0) + 1
        elif n.type in call_types:
            callee = _callee_name(lang, n, src)
            if callee:
                calls[callee] = calls.get(callee, 0) + 1
        elif n.type in kinds:
            kind = kinds[n.type]
            if lang == "kotlin" and n.type == "class_declaration":
                kind = _kotlin_refine(n)
            if kind in ("function",) and any(p[0] in _TYPELIKE for p in stack):
                kind = "method"
            parent_kind, parent_name = stack[-1] if stack else (None, None)
            if lang == "java" and n.type == "field_declaration":
                # one symbol per declared variable
                for vd in n.children:
                    if vd.type == "variable_declarator":
                        nm = vd.child_by_field_name("name")
                        symbols.append(_sym("field", _txt(src, nm) if nm else None,
                                            n, parent_kind, parent_name))
            else:
                symbols.append(_sym(kind, _name(lang, n, src), n, parent_kind, parent_name))
                stack.append((kind, symbols[-1]["name"]))
                pushed = True
        for c in n.children:
            visit(c)
        if pushed:
            stack.pop()

    visit(root)
    line_count = src.count(b"\n") + 1
    return symbols, imports, annotations, calls, line_count, not root.has_error


def _sym(kind, name, n, parent_kind, parent_name) -> dict:
    return {
        "kind": kind, "name": name,
        "start_line": n.start_point[0] + 1, "end_line": n.end_point[0] + 1,
        "parent_kind": parent_kind, "parent_name": parent_name,
    }


# --- DuckDB schema ---------------------------------------------------------
_DDL = """
CREATE TABLE teams (
  team INTEGER PRIMARY KEY, name VARCHAR, owners VARCHAR[], sources VARCHAR[],
  skipped_count INTEGER
);
CREATE TABLE epa (
  team INTEGER, year INTEGER, status VARCHAR, norm_epa DOUBLE, epa_points DOUBLE,
  unitless_epa DOUBLE, state_pctile DOUBLE, winrate DOUBLE,
  wins INTEGER, losses INTEGER, ties INTEGER, PRIMARY KEY (team, year)
);
CREATE TABLE repos (
  repo_id VARCHAR PRIMARY KEY, team INTEGER, year INTEGER, repo VARCHAR, bucket VARCHAR,
  url VARCHAR, local_path VARCHAR, detected_via VARCHAR, cloned BOOLEAN,
  fork BOOLEAN, archived BOOLEAN, suppressed_files INTEGER,
  commits INTEGER, first_commit TIMESTAMP, last_commit TIMESTAMP,
  contributors INTEGER, insertions BIGINT, deletions BIGINT, files_touched INTEGER
);
CREATE TABLE commits (
  repo_id VARCHAR, hash VARCHAR, author VARCHAR, email VARCHAR, committed_at TIMESTAMP,
  subject VARCHAR, files_changed INTEGER, insertions INTEGER, deletions INTEGER
);
CREATE TABLE commit_files (
  repo_id VARCHAR, hash VARCHAR, path VARCHAR, ins INTEGER, dels INTEGER, is_binary BOOLEAN
);
CREATE TABLE files (
  file_id VARCHAR PRIMARY KEY, repo_id VARCHAR, team INTEGER, team_name VARCHAR,
  year INTEGER, repo VARCHAR, source_file VARCHAR, file_path VARCHAR, rel_path VARCHAR,
  lang VARCHAR, ext VARCHAR, size_bytes BIGINT, line_count INTEGER,
  parse_ok BOOLEAN, symbol_count INTEGER
);
CREATE TABLE symbols (
  file_id VARCHAR, repo_id VARCHAR, team INTEGER, year INTEGER, repo VARCHAR,
  source_file VARCHAR, file_path VARCHAR, lang VARCHAR, kind VARCHAR, name VARCHAR,
  parent_kind VARCHAR, parent_name VARCHAR, start_line INTEGER, end_line INTEGER
);
CREATE TABLE imports (
  file_id VARCHAR, repo_id VARCHAR, team INTEGER, year INTEGER, repo VARCHAR,
  source_file VARCHAR, file_path VARCHAR, lang VARCHAR, target VARCHAR, raw VARCHAR
);
CREATE TABLE annotations (
  file_id VARCHAR, repo_id VARCHAR, team INTEGER, year INTEGER, repo VARCHAR,
  source_file VARCHAR, file_path VARCHAR, lang VARCHAR, name VARCHAR, n INTEGER
);
CREATE TABLE calls (
  file_id VARCHAR, repo_id VARCHAR, team INTEGER, year INTEGER, repo VARCHAR,
  source_file VARCHAR, file_path VARCHAR, lang VARCHAR, callee VARCHAR, n INTEGER
);
CREATE TABLE deploy_files (
  repo_id VARCHAR, team INTEGER, year INTEGER, repo VARCHAR,
  rel_path VARCHAR, file_path VARCHAR, kind VARCHAR
);
"""

_TABLES = ["teams", "epa", "repos", "commits", "commit_files", "files", "symbols",
           "imports", "annotations", "calls", "deploy_files"]

# Non-source corpus files the rubric cares about (PathPlanner/Choreo/CI/swerve).
def _deploy_kind(rel_path: str, ext: str) -> str | None:
    low = "/" + rel_path.lower().replace("\\", "/")
    if ext in (".traj", ".chor"):
        return "choreo"
    if ext == ".path":
        return "pathplanner_path"
    if ext == ".auto":
        return "pathplanner_auto"
    if "/deploy/swerve" in low:
        return "swerve_config"
    if "/.github/workflows/" in low and ext in (".yml", ".yaml"):
        return "ci_workflow"
    return None


def _log(msg: str) -> None:
    print(f"[scout:index] {msg}", file=sys.stderr, flush=True)


def _repo_id(team: int, year, repo: str) -> str:
    return f"{team}/{year if year else 'library'}/{repo}"


def run_index(args) -> int:
    output_root = config.resolve_output_root(getattr(args, "output_root", None))
    db_path = Path(args.db) if getattr(args, "db", None) else config.DEFAULT_CODE_DB
    master_path = config.DEFAULT_MASTER_JSON
    if not master_path.exists():
        _log(f"missing {master_path}; run `python3 main.py build` first")
        return 2

    master = json.loads(master_path.read_text())
    teams = master["teams"]
    want = set(args.team) if getattr(args, "team", None) else None
    langs = set(args.lang) if getattr(args, "lang", None) else None
    if want:
        teams = [t for t in teams if t["team"] in want]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    if args.rebuild:
        for t in _TABLES:
            con.execute(f"DROP TABLE IF EXISTS {t}")
    _ensure_schema(con)

    # Metadata tables (teams/epa always reloaded; small).
    con.execute("DELETE FROM teams" + (_in("team", want) if want else ""))
    con.execute("DELETE FROM epa" + (_in("team", want) if want else ""))
    _load_teams_epa(con, teams)

    start = time.time()
    n_repos = n_files = n_syms = 0
    for t in teams:
        for r in t["repos"]:
            rid = _repo_id(t["team"], r.get("year"), r["repo"])
            if not args.rebuild:  # incremental: clear this repo's prior rows
                for tbl in ("repos", "commits", "commit_files", "files", "symbols",
                            "imports", "annotations", "calls", "deploy_files"):
                    con.execute(f"DELETE FROM {tbl} WHERE repo_id=?", [rid])
            _load_repo_row(con, t, r, rid)
            repo_dir = output_root / r["local_path"]
            if r.get("cloned") and repo_dir.is_dir():
                _load_history(con, rid, repo_dir)
                fc, sc = _index_repo_source(con, t, r, rid, repo_dir, output_root, langs)
                n_files += fc
                n_syms += sc
            n_repos += 1
        _log(f"team {t['team']} {t['name']} done ({n_files} files, {n_syms} symbols so far)")

    con.close()
    _log(f"indexed {n_repos} repos, {n_files} files, {n_syms} symbols in "
         f"{time.time()-start:.0f}s -> {db_path}")
    return 0


def _in(col, vals):
    return f" WHERE {col} IN ({','.join(str(int(v)) for v in vals)})"


def _ensure_schema(con) -> None:
    existing = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if not set(_TABLES) <= existing:
        con.execute(_DDL)


def _load_teams_epa(con, teams) -> None:
    con.executemany(
        "INSERT INTO teams VALUES (?,?,?,?,?)",
        [(t["team"], t["name"], t["owners"], t["sources"], t.get("skipped_count"))
         for t in teams],
    )
    rows = []
    for t in teams:
        for e in t.get("epa", []):
            rows.append((t["team"], e.get("year"), e.get("status"),
                         e.get("norm_EPA"), e.get("epa_points"), e.get("unitless_epa"),
                         e.get("state_pctile"), e.get("winrate"),
                         e.get("wins"), e.get("losses"), e.get("ties")))
    if rows:
        con.executemany("INSERT INTO epa VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)


def _load_repo_row(con, t, r, rid) -> None:
    hs = r.get("history_summary") or {}
    con.execute(
        "INSERT INTO repos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [rid, t["team"], r.get("year"), r["repo"],
         "library" if r.get("year") is None else "season",
         r.get("url"), r.get("local_path"), r.get("detected_via"), r.get("cloned"),
         r.get("fork"), r.get("archived"), r.get("suppressed_files"),
         hs.get("commits"), hs.get("first"), hs.get("last"), hs.get("contributors"),
         hs.get("insertions"), hs.get("deletions"), hs.get("files_touched")],
    )


def _load_history(con, rid, repo_dir: Path) -> None:
    hf = repo_dir / "history.json"
    if not hf.exists():
        return
    try:
        hist = json.loads(hf.read_text())
    except (json.JSONDecodeError, OSError):
        return
    crows, frows = [], []
    for c in hist.get("commits", []):
        crows.append((rid, c.get("hash"), c.get("author"), c.get("email"),
                      c.get("date"), c.get("subject"), c.get("files_changed"),
                      c.get("insertions"), c.get("deletions")))
        for f in c.get("files", []):
            frows.append((rid, c.get("hash"), f.get("path"),
                          f.get("ins"), f.get("del"), bool(f.get("binary"))))
    if crows:
        con.executemany("INSERT INTO commits VALUES (?,?,?,?,?,?,?,?,?)", crows)
    if frows:
        con.executemany("INSERT INTO commit_files VALUES (?,?,?,?,?,?)", frows)


def _index_repo_source(con, t, r, rid, repo_dir, output_root, langs):
    file_rows, sym_rows, imp_rows = [], [], []
    ann_rows, call_rows, deploy_rows = [], [], []
    team, year, repo, team_name = t["team"], r.get("year"), r["repo"], t["name"]
    for dirpath, dirnames, filenames in os.walk(repo_dir):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".sup"):
                continue
            ext = os.path.splitext(fn)[1].lower()
            full = Path(dirpath) / fn
            rel_path = str(full.relative_to(repo_dir))
            file_path = str(full.relative_to(output_root))
            # Non-source files the rubric cares about (PathPlanner/Choreo/CI/swerve).
            dk = _deploy_kind(rel_path, ext)
            if dk:
                deploy_rows.append((rid, team, year, repo, rel_path, file_path, dk))
            lang = config.LANG_BY_EXT.get(ext)
            if not lang or (langs and lang not in langs):
                continue
            try:
                size = full.stat().st_size
                if size > config.SUPPRESS_SIZE_BYTES:
                    continue
                src = full.read_bytes()
            except OSError:
                continue
            file_id = f"{rid}/{rel_path}"
            try:
                symbols, imports, anns, calls, loc, ok = extract(lang, src)
            except Exception:
                symbols, imports, anns, calls, loc, ok = [], [], {}, {}, src.count(b"\n") + 1, False
            file_rows.append((file_id, rid, team, team_name, year, repo, fn,
                              file_path, rel_path, lang, ext, size, loc, ok, len(symbols)))
            for s in symbols:
                sym_rows.append((file_id, rid, team, year, repo, fn, file_path, lang,
                                 s["kind"], s["name"], s["parent_kind"], s["parent_name"],
                                 s["start_line"], s["end_line"]))
            for target, raw in imports:
                imp_rows.append((file_id, rid, team, year, repo, fn, file_path, lang,
                                 target, raw))
            for name, cnt in anns.items():
                ann_rows.append((file_id, rid, team, year, repo, fn, file_path, lang, name, cnt))
            for callee, cnt in calls.items():
                call_rows.append((file_id, rid, team, year, repo, fn, file_path, lang, callee, cnt))
    if file_rows:
        con.executemany("INSERT INTO files VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", file_rows)
    if sym_rows:
        con.executemany("INSERT INTO symbols VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sym_rows)
    if imp_rows:
        con.executemany("INSERT INTO imports VALUES (?,?,?,?,?,?,?,?,?,?)", imp_rows)
    if ann_rows:
        con.executemany("INSERT INTO annotations VALUES (?,?,?,?,?,?,?,?,?,?)", ann_rows)
    if call_rows:
        con.executemany("INSERT INTO calls VALUES (?,?,?,?,?,?,?,?,?,?)", call_rows)
    if deploy_rows:
        con.executemany("INSERT INTO deploy_files VALUES (?,?,?,?,?,?,?)", deploy_rows)
    return len(file_rows), len(sym_rows)
