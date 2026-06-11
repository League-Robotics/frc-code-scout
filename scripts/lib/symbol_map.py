#!/usr/bin/env python3
"""Emit {file: [ {kind,name,line} ]} for a repo using ast-grep per-language patterns."""
import json, subprocess, sys, os
ROOT = sys.argv[1]
LANGS = {
    "java":   [("class","class_declaration"),("interface","interface_declaration"),("enum","enum_declaration"),("method","method_declaration")],
    "kotlin": [("class","class_declaration"),("function","function_declaration"),("object","object_declaration")],
    "cpp":    [("class","class_specifier"),("function","function_definition")],
    "python": [("class","class_definition"),("function","function_definition")],
}
EXT = {".java":"java",".kt":"kotlin",".cpp":"cpp",".cc":"cpp",".h":"cpp",".hpp":"cpp",".py":"python"}
out = {}
def ag(lang, kind, path):
    try:
        r = subprocess.run(["ast-grep","run","-l",lang,"-p",f"$$$","--json"],capture_output=True,text=True,timeout=30)
    except Exception: return []
    return []
# Simpler & robust: walk files, run ast-grep scan with a tiny inline rule per kind is overkill.
# Use ctags-style heuristic: ast-grep 'kind' via rule stdin.
import tempfile
def find(lang, kind, path):
    rule = f"id: m\nlanguage: {lang}\nrule:\n  kind: {kind}\n"
    try:
        p = subprocess.run(["ast-grep","scan","--inline-rules",rule,path,"--json"],
                           capture_output=True,text=True,timeout=60)
        data = json.loads(p.stdout or "[]")
    except Exception:
        return []
    res=[]
    for m in data:
        txt = m.get("text","").splitlines()[0][:80]
        res.append({"line": m.get("range",{}).get("start",{}).get("line",0)+1, "text": txt})
    return res
for dirpath,_,files in os.walk(ROOT):
    for f in files:
        ext=os.path.splitext(f)[1].lower()
        lang=EXT.get(ext)
        if not lang: continue
        full=os.path.join(dirpath,f); rel=os.path.relpath(full,ROOT)
        syms=[]
        for kname,kind in LANGS[lang]:
            for hit in find(lang,kind,full):
                syms.append({"kind":kname,**hit})
        if syms: out[rel]=syms
print(json.dumps(out,indent=1))
