#!/usr/bin/env python3
"""Apoyo de la skill session-close y de los hooks de sesión.

Uso:
  session_close.py record <raíz> <session_id> <transcript> <motivo>   (hook SessionEnd)
  session_close.py pending <raíz>                                      sesiones sin cierre
  session_close.py current <raíz>                                      transcript de la sesión en curso
  session_close.py digest <transcript> [--since AAAA-MM-DD]            resumen legible de una sesión
  session_close.py mark <raíz> <session_id>...                         marcar sesiones como cerradas

Los registros quedan en <raíz>/.harness/local/ (pending-close.tsv y closed-sessions), con un .gitignore
propio: los transcripts son locales de cada PC y no se versionan.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

MIN_TRANSCRIPT_BYTES = 60_000  # menos que esto es una sesión corta: no pide cierre
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"


def hdir(root: Path) -> Path:
    d = root / ".harness" / "local"
    d.mkdir(parents=True, exist_ok=True)
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")
    return d


def closed(root: Path) -> set[str]:
    f = hdir(root) / "closed-sessions"
    return set(f.read_text(encoding="utf-8").split()) if f.exists() else set()


def pending_rows(root: Path) -> list[list[str]]:
    f = hdir(root) / "pending-close.tsv"
    if not f.exists():
        return []
    done = closed(root)
    rows = [l.split("\t") for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in rows if len(r) >= 3 and r[1] not in done and Path(r[2]).exists()]


def record(root: Path, sid: str, transcript: str, reason: str) -> None:
    t = Path(transcript)
    if sid in closed(root) or not t.exists() or t.stat().st_size < MIN_TRANSCRIPT_BYTES:
        return
    if any(r[1] == sid for r in pending_rows(root)):
        return
    with open(hdir(root) / "pending-close.tsv", "a", encoding="utf-8", newline="\n") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M}\t{sid}\t{t}\t{reason}\n")


def project_dir(root: Path) -> Path:
    return CLAUDE_PROJECTS / re.sub(r"[^A-Za-z0-9]", "-", str(root.resolve()))


def current(root: Path) -> None:
    files = sorted(project_dir(root).glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if files:
        print(f"{files[-1].stem}\t{files[-1]}")


def text_of(content) -> list[str]:
    if isinstance(content, str):
        return [content]
    out = []
    for b in content or []:
        if b.get("type") == "text":
            out.append(b.get("text", ""))
    return out


def digest(transcript: Path, since: str = "") -> None:
    """Pedidos del usuario, commits, escrituras externas y el último mensaje de Claude de cada turno."""
    first = last = None
    turns: list[tuple[str, str]] = []
    commits, writes = [], []
    pending_reply = ""
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = ev.get("timestamp", "")
        if since and ts and ts[:10] < since:
            continue
        if ts:
            first = first or ts
            last = ts
        msg = ev.get("message") or {}
        if ev.get("type") == "user" and not ev.get("isMeta"):
            for t in text_of(msg.get("content")):
                t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S).strip()
                if t and not t.startswith(("<command-", "<local-command", "Caveat:")):
                    if pending_reply:
                        turns.append(("claude", pending_reply))
                        pending_reply = ""
                    turns.append(("usuario", t[:600]))
        elif ev.get("type") == "assistant":
            for b in msg.get("content") or []:
                if b.get("type") == "text" and b.get("text", "").strip():
                    pending_reply = b["text"].strip()
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    cmd = str(inp.get("command", ""))
                    if "git" in cmd and "commit" in cmd:
                        m = re.search(r'-m "([^"\n]+)', cmd)
                        commits.append(m.group(1) if m else cmd[:120])
                    name = b.get("name", "")
                    if re.search(r"create_task|update_task|create_task_comment|add_time_entry|add_task_dependency", name):
                        writes.append(f"{name.split('__')[-1]} {inp.get('task_id', '')}".strip())
    if pending_reply:
        turns.append(("claude", pending_reply))
    print(f"Sesión {transcript.stem} · {first} → {last}\n")
    print("## Conversación (pedidos y última respuesta de cada turno)")
    for who, t in turns:
        print(f"- {who}: {t[:1200] if who == 'claude' else t}")
    print("\n## Commits")
    print("\n".join(f"- {c}" for c in commits) or "- ninguno")
    print("\n## Escrituras en ClickUp")
    print("\n".join(f"- {w}" for w in sorted(set(writes))) or "- ninguna")


def mark(root: Path, sids: list[str]) -> None:
    with open(hdir(root) / "closed-sessions", "a", encoding="utf-8", newline="\n") as f:
        for s in sids:
            f.write(s + "\n")
    rest = [r for r in pending_rows(root) if r[1] not in sids]
    (hdir(root) / "pending-close.tsv").write_text("".join("\t".join(r) + "\n" for r in rest), encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "record":
        record(Path(args[0]), args[1], args[2], args[3] if len(args) > 3 else "")
    elif cmd == "pending":
        for r in pending_rows(Path(args[0])):
            print("\t".join(r))
    elif cmd == "current":
        current(Path(args[0]))
    elif cmd == "digest":
        since = args[args.index("--since") + 1] if "--since" in args else ""
        digest(Path(args[0]), since)
    elif cmd == "mark":
        mark(Path(args[0]), args[1:])
    else:
        sys.exit(f"subcomando desconocido: {cmd}")


if __name__ == "__main__":
    main()
