#!/usr/bin/env python3
"""Activa solo los grupos de plugins que un proyecto necesita (config.toml [plugin_groups]).

  apply_profile.py <proyecto> --list                 grupos, costo y si el repo sugiere activarlos
  apply_profile.py <proyecto> --groups code,iac      aplica (vacío = ninguno)
  apply_profile.py <proyecto> --recommend            aplica lo que sugieren las señales del repo

Escribe enabledPlugins en <proyecto>/.claude/settings.local.json (fusiona, no pisa lo demás; está fuera de git)
y deja la elección en project.toml [claude] plugin_groups para repetirla en otra PC.
"""
import json
import re
import sys
import tomllib
from pathlib import Path

CFG = Path.home() / "claude-workspace" / "harness" / "config.toml"


def groups() -> dict:
    return tomllib.loads(CFG.read_text(encoding="utf-8")).get("plugin_groups", {})


def suggested(root: Path, spec: dict) -> bool:
    for pat in spec.get("recommend", []):
        if any(root.rglob(pat)) if pat.startswith("*") else (root / pat).exists():
            return True
    return False


def apply(root: Path, chosen: list[str]) -> None:
    g = groups()
    unknown = [c for c in chosen if c not in g]
    if unknown:
        sys.exit(f"grupos desconocidos: {unknown}; hay: {list(g)}")
    wanted = {p for c in chosen for p in g[c]["plugins"]}
    every = {p for spec in g.values() for p in spec["plugins"]}
    f = root / ".claude" / "settings.local.json"
    cur = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    cur["enabledPlugins"] = {p: (p in wanted) for p in sorted(every)}
    f.parent.mkdir(exist_ok=True)
    f.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pt = root / "project.toml"
    if pt.is_file():
        s = pt.read_text(encoding="utf-8")
        line = "plugin_groups = [" + ", ".join(f'"{c}"' for c in chosen) + "]"
        if re.search(r"^plugin_groups\s*=", s, re.M):
            s = re.sub(r"^plugin_groups\s*=.*$", line, s, flags=re.M)
        elif re.search(r"^\[claude\]", s, re.M):
            s = re.sub(r"^\[claude\]\s*$", "[claude]\n" + line, s, count=1, flags=re.M)
        else:
            s = s.rstrip("\n") + "\n\n[claude]\n" + line + "\n"
        pt.write_text(s, encoding="utf-8")
    print(f"activos: {chosen or 'ninguno'}; desactivados: {sorted(set(g) - set(chosen))}")


def main() -> None:
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    root = Path(a[0]).expanduser().resolve()
    g = groups()
    if "--list" in a:
        for name, spec in g.items():
            print(f"{name:6} {'SUGERIDO' if suggested(root, spec) else '        '} {spec['why']} ({', '.join(spec['plugins'])})")
    elif "--recommend" in a:
        apply(root, [n for n, s in g.items() if suggested(root, s)])
    elif "--groups" in a:
        raw = a[a.index("--groups") + 1] if a.index("--groups") + 1 < len(a) else ""
        apply(root, [x for x in raw.split(",") if x])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
