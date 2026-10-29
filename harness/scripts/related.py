#!/usr/bin/env python3
"""Todo lo relacionado con un tema, en una sola salida, para traerlo al contexto de una sesión.

Uso: related.py <proyecto> <T-012 | D-050 | id de ClickUp | palabra o frase> [--max N]

Sin archivos derivados: las relaciones se calculan al vuelo desde lo que ya existe (backlog, copia de ClickUp,
decisiones, reuniones, digests, status). Una decisión se vincula a una tarea si cita su id (T-xxx o de ClickUp)
o el nombre de la tarea de ClickUp tal cual.
"""
import csv
import io
import re
import sys
import unicodedata
from pathlib import Path

DOCS = ["docs/decisions/decisions.md", "docs/decisions/bitacora-tl-sa.md", "backlog/notes.md"]
FOLDERS = ["context/meetings", "context/digest", "status", "memory", "research"]


def rows(p: Path) -> list[list[str]]:
    if not p.is_file():
        return []
    ls = [l.strip() for l in p.read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
    return list(csv.reader(io.StringIO("\n".join(ls))))


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))


def sections(text: str, level_re: str) -> dict[str, str]:
    parts = re.split(rf"^(?={level_re} )", text, flags=re.M)
    out = {}
    for p in parts:
        m = re.match(rf"{level_re} ((?:D|T)-\d{{2,3}})\b", p)
        if m:
            out[m.group(1)] = p
    return out


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        sys.exit(__doc__)
    root, q = Path(args[0]).expanduser(), args[1].strip()
    cap = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 8

    bl = {r[0]: r for r in rows(root / "backlog/backlog.toon")}
    cu = {r[0]: r for r in rows(root / "clickup/tasks.toon")}
    by_cu = {r[8]: r[0] for r in bl.values() if len(r) > 8 and r[8]}
    decisions: dict[str, str] = {}
    for f in DOCS[:2]:
        if (root / f).is_file():
            decisions.update(sections((root / f).read_text(encoding="utf-8"), "##"))
    notes = sections((root / DOCS[2]).read_text(encoding="utf-8"), "##") if (root / DOCS[2]).is_file() else {}

    t_ids, d_ids, c_ids, terms = set(), set(), set(), []
    if re.fullmatch(r"T-\d{2,3}", q, re.I):
        t_ids.add(q.upper())
    elif re.fullmatch(r"D-\d{2,3}", q, re.I):
        d_ids.add(q.upper())
    elif q in cu:
        c_ids.add(q)
    else:
        terms = [fold(w) for w in re.findall(r"\w{4,}", q)]
        for tid, r in bl.items():
            if all(t in fold(r[1]) for t in terms):
                t_ids.add(tid)
        for cid, r in cu.items():
            if all(t in fold(r[1]) for t in terms):
                c_ids.add(cid)
        for did, body in decisions.items():
            if all(t in fold(body.split("\n", 1)[0]) for t in terms):
                d_ids.add(did)

    # Tareas -> ClickUp y al revés
    for tid in list(t_ids):
        if tid in bl and len(bl[tid]) > 8 and bl[tid][8]:
            c_ids.add(bl[tid][8])
    for cid in list(c_ids):
        if cid in by_cu:
            t_ids.add(by_cu[cid])

    # Decisiones <-> tareas por id o por nombre exacto de la tarea de ClickUp
    names = {cid: fold(r[1]) for cid, r in cu.items() if len(r[1]) >= 20}
    for did, body in decisions.items():
        fb = fold(body)
        hits_t = set(re.findall(r"\bT-\d{2,3}\b", body))
        hits_c = {cid for cid in cu if re.search(rf"\b{cid}\b", body)} | {cid for cid, n in names.items() if n in fb}
        if did in d_ids:
            t_ids |= hits_t & bl.keys()
            c_ids |= hits_c
        elif (t_ids & hits_t) or (c_ids & hits_c):
            d_ids.add(did)
    for cid in list(c_ids):
        if cid in by_cu:
            t_ids.add(by_cu[cid])

    print(f"# Relacionado con «{q}»\n")
    for tid in sorted(t_ids)[:cap]:
        r = bl.get(tid)
        if r:
            print(f"- {tid} [{r[2]}] {r[1]} · owner {r[6]} · fase {r[7]}" + (f" · ClickUp {r[8]}" if r[8] else ""))
    for cid in sorted(c_ids)[:cap]:
        r = cu[cid]
        parent = cu.get(r[3], [None, ""])[1] if r[3] else ""
        print(f"- ClickUp {cid} [{r[2]}] {r[1]} · {r[4]} · vence {r[5]}" + (f" · dentro de «{parent}»" if parent else "")
              + (f" · espera a {r[10]}" if len(r) > 10 and r[10] else "") + (f" · bloquea {r[11]}" if len(r) > 11 and r[11] else "")
              + (f" · {r[19]} comentarios" if len(r) > 19 and r[19] else "") + f" · detalle: clickup/tasks/{cid}.md")
    print()
    for did in sorted(d_ids)[:cap]:
        body = decisions[did]
        head = body.split("\n", 1)[0]
        dec = re.search(r"\*\*Decisión:\*\*(.*)", body)
        st = re.search(r"\*\*Estado:\*\*\s*(.*)", body)
        print(f"- {head.lstrip('# ')} · {st.group(1).strip() if st else 's/estado'}")
        if dec:
            print(f"    {dec.group(1).strip()[:300]}")
    for tid in sorted(t_ids)[:3]:
        if tid in notes:
            why = re.search(r"\*\*Por qué importa:\*\*(.*)", notes[tid])
            if why:
                print(f"\n- Notas de {tid}: {why.group(1).strip()[:300]}")

    # Dónde se habla: reuniones, digests, status
    keys = sorted(t_ids | d_ids | c_ids)
    pats = [re.compile(rf"\b{re.escape(k)}\b") for k in keys] + [re.compile(re.escape(t)) for t in terms]
    seen = []
    for folder in FOLDERS:
        for f in sorted((root / folder).glob("*.md"), reverse=True) if (root / folder).is_dir() else []:
            txt = f.read_text(encoding="utf-8", errors="ignore")
            n = sum(len(p.findall(fold(txt) if p.pattern in terms else txt)) for p in pats)
            if n:
                seen.append((n, f.relative_to(root).as_posix()))
    print("\n## Fuentes donde aparece (más menciones primero)")
    for n, f in sorted(seen, reverse=True)[:cap]:
        print(f"- {f} ({n})")


if __name__ == "__main__":
    main()
