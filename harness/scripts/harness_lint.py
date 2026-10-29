#!/usr/bin/env python3
"""Chequeos determinísticos del contexto de un proyecto del harness (sin LLM).

Uso: harness_lint.py <directorio-del-proyecto> [--strict]
Sale con 1 si hay errores (con --strict, también por avisos). Es lo que habría atrapado
un índice roto, una decisión sin indexar o un archivo sin la marca de confidencialidad.
"""
import csv
import datetime as dt
import io
import os
import unicodedata
import re
import sys
from pathlib import Path

MARK = "dinocloud internal - confidential"
SKIP = {"drive", "clickup", ".claude", ".harness", ".git", "node_modules", "worktrees", "reports"}


def rows(path: Path) -> list[list[str]]:
    """Filas de un .toon tabular: la primera línea es el encabezado, el resto CSV con sangría."""
    if not path.is_file():
        return []
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()[1:] if ln.strip()]
    return list(csv.reader(io.StringIO("\n".join(lines))))


def exists(p: Path) -> bool:
    """Los archivos de Drive a veces no se resuelven por la normalización del nombre."""
    if p.exists():
        return True
    # Drive puede dejar nombres en NFD y el índice tenerlos en NFC (o al revés): se compara normalizado.
    try:
        return unicodedata.normalize("NFC", p.name) in {unicodedata.normalize("NFC", n) for n in os.listdir(p.parent)}
    except OSError:
        return False


def lint(root: Path) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    index = rows(root / "index.toon")
    indexed_text = "\n".join(",".join(r) for r in index)

    for r in index:
        if r and not (exists(root / r[0]) or exists(root / r[0].rsplit("#", 1)[0])):
            errors.append(f"index.toon: la ruta no existe: {r[0]}")

    ids = set()
    for f in [root / "docs/decisions/decisions.md", root / "docs/decisions/bitacora-tl-sa.md"]:
        if f.is_file():
            ids |= set(re.findall(r"^#{2,3} (D-\d{2,3})\b", f.read_text(encoding="utf-8"), re.M))
    missing = sorted(i for i in ids if not re.search(rf"\b{i}\b", indexed_text))
    if missing:
        warns.append(f"decisiones sin fila ni tag en index.toon: {', '.join(missing)}")

    cu = {r[0] for r in rows(root / "clickup/tasks.toon") if r}
    bl = rows(root / "backlog/backlog.toon")
    if cu and bl:
        broken = [r[0] for r in bl if len(r) > 8 and r[8] and r[8] not in cu]
        if broken:
            errors.append(f"backlog: clickup_id que no existe en la copia de ClickUp: {', '.join(broken[:8])}")

    for f in sorted(root.rglob("*.md")):
        rel = f.relative_to(root)
        if rel.parts[0] in SKIP:
            continue
        head = "\n".join(f.read_text(encoding="utf-8", errors="ignore").splitlines()[:8]).lower()
        if MARK not in head:
            warns.append(f"sin marca de confidencialidad: {rel.as_posix()}")

    for name in ("risks.md", "timeline.md"):
        f = root / "memory" / name
        if f.is_file() and len(f.read_text(encoding="utf-8")) < 400:
            warns.append(f"memory/{name} está vacío: nada lo alimenta")

    st = root / ".harness/state.toml"
    if st.is_file():
        m = re.search(r'^consolidate\s*=\s*"(\d{4}-\d{2}-\d{2})', st.read_text(encoding="utf-8"), re.M)
        if m and (dt.date.today() - dt.date.fromisoformat(m.group(1))).days > 14:
            warns.append(f"consolidate sin correr desde {m.group(1)}")
    return errors, warns


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit("uso: harness_lint.py <proyecto> [--strict]")
    errors, warns = lint(Path(args[0]).expanduser())
    for e in errors:
        print(f"ERROR  {e}")
    for w in warns:
        print(f"AVISO  {w}")
    print(f"lint: {len(errors)} errores, {len(warns)} avisos")
    sys.exit(1 if errors or (warns and "--strict" in sys.argv) else 0)


if __name__ == "__main__":
    main()
