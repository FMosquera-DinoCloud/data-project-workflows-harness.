"""Lee asignaciones del Resource Planner (solo pestañas permitidas) y las deja en TOON.

Uso:
  allocations.py login
  allocations.py fetch --project "Nombre en la planilla" [--project ...] --out memory/allocations.toon
"""

import argparse
import datetime as dt
import json
import os
import sys
import tomllib
from pathlib import Path
from urllib.parse import quote

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CONFIG = Path.home() / "claude-workspace/harness/config.toml"
RANGES = {
    "Assignations": "A1:J",
    "Team": "A1:L",  # la columna M (email) queda afuera a propósito
}


def load_config() -> dict:
    cfg = tomllib.loads(CONFIG.read_text())["allocation"]
    for key in ("google_client_secret", "token_path"):
        cfg[key] = Path(os.path.expanduser(cfg[key]))
    return cfg


def login(cfg: dict) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    secret = cfg["google_client_secret"]
    if not secret.exists():
        sys.exit(
            f"Falta {secret}.\n"
            "  console.cloud.google.com (proyecto interno DinoCloud) → APIs & Services → habilitar Google Sheets API\n"
            "  → Credentials → Create credentials → OAuth client ID → tipo 'Desktop app' → Download JSON\n"
            f"  → guardarlo como {secret} (chmod 600) y volver a correr login."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(port=0)
    cfg["token_path"].parent.mkdir(parents=True, exist_ok=True)
    cfg["token_path"].write_text(creds.to_json())
    os.chmod(cfg["token_path"], 0o600)
    print(f"ok: token en {cfg['token_path']}")


def session(cfg: dict):
    from google.auth.transport.requests import AuthorizedSession, Request
    from google.oauth2.credentials import Credentials

    if not cfg["token_path"].exists():
        sys.exit("falta login: correr `allocations.py login` (lo hace el usuario con ! en el prompt)")
    creds = Credentials.from_authorized_user_file(str(cfg["token_path"]), SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        cfg["token_path"].write_text(creds.to_json())
    return AuthorizedSession(creds)


def fetch_tabs(cfg: dict) -> dict[str, list[list[str]]]:
    allowed = set(cfg["allowed_tabs"])
    if not set(RANGES) <= allowed:
        sys.exit(f"pestañas no permitidas por config: {set(RANGES) - allowed}")
    params = "&".join(f"ranges={quote(f'{tab}!{rng}')}" for tab, rng in RANGES.items())
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{cfg['spreadsheet_id']}/values:batchGet"
        f"?{params}&valueRenderOption=FORMATTED_VALUE"
    )
    resp = session(cfg).get(url, timeout=60)
    if not resp.ok:
        try:
            err = resp.json().get("error", {})
            reason = err.get("message", "") + " " + " ".join(d.get("reason", "") for d in err.get("details", []) if isinstance(d, dict))
        except ValueError:
            reason = resp.text[:300]
        sys.exit(f"Google respondió {resp.status_code}: {reason.strip()}")
    out = {}
    for vr in resp.json().get("valueRanges", []):
        tab = vr["range"].split("!")[0].strip("'")
        out[tab] = vr.get("values", [])
    return out


def iso(value: str) -> str:
    value = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def num(value: str) -> float:
    try:
        return float((value or "0").replace(",", "."))
    except ValueError:
        return 0.0


def fmt_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def cell(row: list[str], i: int) -> str:
    return row[i].strip() if i < len(row) else ""


def toon_value(v) -> str:
    s = "" if v is None else str(v)
    if any(c in s for c in ',:"') or s != s.strip():
        s = '"' + s.replace('"', '\\"') + '"'
    return s


def toon_block(name: str, fields: list[str], rows: list[list]) -> str:
    lines = [f"{name}[{len(rows)}]{{{','.join(fields)}}}:"]
    lines += ["  " + ",".join(toon_value(v) for v in r) for r in rows]
    return "\n".join(lines)


def fetch(cfg: dict, projects: list[str], out: Path) -> None:
    tabs = fetch_tabs(cfg)
    today = dt.date.today()
    wanted = [p.strip().casefold() for p in projects]

    capacity = {}
    for r in tabs.get("Team", [])[1:]:
        name = cell(r, 0)
        if name and cell(r, 5).upper() == "TRUE":
            capacity[name.casefold()] = num(cell(r, 9)) or 160.0

    rows, load = [], {}
    for r in tabs.get("Assignations", [])[1:]:
        project, person = cell(r, 0), cell(r, 4)
        if not project or not person:
            continue
        start, end, hours = iso(cell(r, 5)), iso(cell(r, 6)), num(cell(r, 7))
        now = today.isoformat()
        state = "upcoming" if start and start > now else "ended" if end and end < now else "active"
        if state == "active":
            load[person.casefold()] = load.get(person.casefold(), 0.0) + hours
        if any(project.casefold() == w or project.casefold().startswith(w) for w in wanted):
            billable = "true" if cell(r, 8).upper() == "TRUE" else "false"
            rows.append([person, cell(r, 1), cell(r, 3), start, end, fmt_num(hours), billable, project, state])

    order = {"active": 0, "upcoming": 1, "ended": 2}
    rows.sort(key=lambda x: (order[x[8]], x[0].casefold(), x[3]))
    people = sorted({r[0] for r in rows if r[8] != "ended"}, key=str.casefold)
    loads = []
    for p in people:
        total, cap = load.get(p.casefold(), 0.0), capacity.get(p.casefold(), 160.0)
        loads.append([p, fmt_num(total), fmt_num(cap), round(100 * total / cap) if cap else ""])

    body = "\n".join([
        toon_block("allocations", ["person", "role", "seniority", "start", "end", "monthly_hours", "billable", "sheet_project", "state"], rows),
        toon_block("load", ["person", "assigned_hours_all_projects", "available_hours", "load_pct"], loads),
    ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body + "\n")
    print(json.dumps({"out": str(out), "as_of": today.isoformat(), "assignments": len(rows), "active_people": len(people),
                      "unmatched_projects": [] if rows else projects}))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    f = sub.add_parser("fetch")
    f.add_argument("--project", action="append", required=True)
    f.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    cfg = load_config()
    if args.cmd == "login":
        login(cfg)
    else:
        fetch(cfg, args.project, args.out)


if __name__ == "__main__":
    main()
