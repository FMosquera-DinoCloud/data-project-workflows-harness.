"""Copia local central de solo lectura de las asignaciones del Resource Planner (planner.dinocloud.com).

Una sola copia para todos los proyectos del harness. El alcance son los proyectos activos de projects.toon: se juntan
los [allocation].sheet_projects de cada project.toml (nombres o prefijos del proyecto tal como figuran en el planner) y
se escribe en ~/claude-workspace/planner/:
  allocations.toon   allocations[N]{person,role,seniority,start,end,monthly_hours,billable,sheet_project,state}
                     load[N]{person,assigned_hours_all_projects,available_hours,load_pct}
                     absences[N]{person,start,end}   (licencias de las personas de esos proyectos)
  .fetched_at        momento de la copia (ISO 8601)

Cada proyecto lee de ahí las filas cuyo sheet_project coincide con el suyo. Mismo esquema que allocations.py (la
planilla de Sheets, que queda de respaldo). Sin emails, tarifas ni costos. La copia no se versiona: cada PC la regenera.

Token: variable RP_TOKEN o el archivo de [planner].token_file de ~/claude-workspace/harness/config.toml. Nunca se
guarda en el repo ni se imprime. Vence a los 90 días: ante un 401 hay que generar uno nuevo en API access del planner.

Uso: planner_mirror.py [--project "Nombre o prefijo"]...   (--project suma proyectos al alcance, ad hoc)
Solo usa la biblioteca estándar.
"""

import datetime as dt
import json
import os
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WORKSPACE = Path.home() / "claude-workspace"
CONFIG = WORKSPACE / "harness/config.toml"
HEADER = "> **DinoCloud Internal - Confidential**"
PAST_DAYS = 60  # lo terminado hace poco sirve para detectar trabajo después del fin de la asignación
FUTURE_DAYS = 365
BASE_CAPACITY = 160.0


def planner_cfg() -> dict:
    return tomllib.loads(CONFIG.read_text(encoding="utf-8")).get("planner", {})


def token(cfg: dict) -> str:
    tok = os.environ.get("RP_TOKEN", "").strip()
    if tok:
        return tok
    path = cfg.get("token_file", "")
    p = Path(os.path.expanduser(path)) if path else None
    if p and p.exists():
        return p.read_text(encoding="utf-8-sig").strip()
    sys.exit("Falta el token del planner: definí RP_TOKEN o [planner].token_file en config.toml.")


def get(cfg: dict, tok: str, path: str, **params):
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{cfg.get('url', 'https://planner.dinocloud.com/api')}{path}{'?' + q if q else ''}"
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            return data["items"] if isinstance(data, dict) and "items" in data else data
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            if e.code == 401:
                sys.exit("Token del planner vencido o revocado: generá uno nuevo en API access.")
            sys.exit(f"Planner {path}: HTTP {e.code}")
    sys.exit(f"Planner {path}: sin respuesta")


def cell(v) -> str:
    v = ("" if v is None else str(v)).replace("\n", " ")
    if any(c in v for c in ',:"') or v != v.strip():
        return '"' + v.replace('"', '\\"') + '"'
    return v


def fmt_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def block(name: str, fields: list[str], rows: list[list]) -> str:
    return "\n".join([f"{name}[{len(rows)}]{{{','.join(fields)}}}:"] + ["  " + ",".join(cell(v) for v in r) for r in rows])


def team_projects() -> list[str]:
    """sheet_projects de los proyectos activos de projects.toon."""
    names = []
    for line in (WORKSPACE / "projects.toon").read_text(encoding="utf-8").splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3 or parts[2] != "true":
            continue
        toml = Path(os.path.expanduser(parts[1])) / "project.toml"
        if toml.exists():
            names += tomllib.loads(toml.read_text(encoding="utf-8")).get("allocation", {}).get("sheet_projects", [])
    return names


def main() -> None:
    args = sys.argv[1:]
    extra = [args[i + 1] for i, a in enumerate(args) if a == "--project" and i + 1 < len(args)]
    wanted = list(dict.fromkeys(p.strip().casefold() for p in team_projects() + extra if p.strip()))
    if not wanted:
        print("Ningún proyecto activo tiene [allocation].sheet_projects: se saltea el planner.")
        return

    cfg = planner_cfg()
    tok = token(cfg)
    today = dt.date.today()
    now = today.isoformat()
    first = today.replace(day=1)
    last = (first + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)

    roles = {r["id"]: r["name"] for r in get(cfg, tok, "/catalogs/role")}
    assignments = get(cfg, tok, "/assignments", **{"from": (today - dt.timedelta(days=PAST_DAYS)).isoformat(),
                                                   "to": (today + dt.timedelta(days=FUTURE_DAYS)).isoformat()})
    avail = get(cfg, tok, "/persons/availability", **{"from": first.isoformat(), "to": last.isoformat()})
    off = get(cfg, tok, "/time-off", **{"from": (today - dt.timedelta(days=30)).isoformat(),
                                        "to": (today + dt.timedelta(days=60)).isoformat()})

    full = max((p["availableHours"] for p in avail), default=0)
    capacity = {p["name"].casefold(): round(BASE_CAPACITY * p["availableHours"] / full)
                for p in avail if full and p["availableHours"]}

    rows, load = [], {}
    for a in assignments:
        project, person = a["project"]["name"], a["person"]["name"]
        if a["project"].get("status") == "abandoned":
            continue
        start, end, hours = a.get("startDate") or "", a.get("endDate") or "", float(a.get("monthlyHours") or 0)
        state = "upcoming" if start and start > now else "ended" if end and end < now else "active"
        if state == "active":
            load[person.casefold()] = load.get(person.casefold(), 0.0) + hours
        if any(project.casefold() == w or project.casefold().startswith(w) for w in wanted):
            rows.append([person, roles.get(a.get("soldRoleId") or "", ""), "", start, end, fmt_num(hours),
                         "true" if a.get("billable") else "false", project, state])

    order = {"active": 0, "upcoming": 1, "ended": 2}
    rows.sort(key=lambda r: (order[r[8]], r[0].casefold(), r[3]))
    people = sorted({r[0] for r in rows if r[8] != "ended"}, key=str.casefold)
    loads = []
    for p in people:
        total, cap = load.get(p.casefold(), 0.0), capacity.get(p.casefold(), BASE_CAPACITY)
        loads.append([p, fmt_num(total), fmt_num(cap), round(100 * total / cap)])
    team = {r[0].casefold() for r in rows}
    absences = sorted(([o["person"]["name"], o["startDate"], o["endDate"]] for o in off
                       if o["person"]["name"].casefold() in team), key=lambda r: (r[0].casefold(), r[1]))

    out = WORKSPACE / "planner"
    out.mkdir(exist_ok=True)
    stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    body = [HEADER, "", "Copia de solo lectura. La genera harness/scripts/planner_mirror.py; no editar a mano.", "",
            block("allocations", ["person", "role", "seniority", "start", "end", "monthly_hours", "billable", "sheet_project", "state"], rows),
            block("load", ["person", "assigned_hours_all_projects", "available_hours", "load_pct"], loads),
            block("absences", ["person", "start", "end"], absences)]
    (out / "allocations.toon").write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    (out / ".fetched_at").write_text(stamp + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"out": str(out / "allocations.toon"), "as_of": now, "assignments": len(rows),
                      "active_people": len(people), "absences": len(absences),
                      "unmatched_projects": [] if rows else wanted}, ensure_ascii=False))


if __name__ == "__main__":
    main()
