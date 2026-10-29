#!/usr/bin/env python3
"""Registra las guardas del harness en ~/.claude/settings.json (idempotente, con backup al lado).

Windows no trae jq, así que este es el equivalente de `install.sh --hook` para las guardas.
Uso: install_hooks.py [--remove]
"""
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"
GUARD = 'bash "$HOME/claude-workspace/harness/hooks/guard.sh"'
WANTED = [
    ("PreToolUse", "mcp__claude_ai_.*", "outbound", "Guarda de envíos: credenciales e ids internos"),
    ("PreToolUse", "Write|Edit|MultiEdit|NotebookEdit|Bash", "unattended-write", "Guarda de rutinas desatendidas"),
    ("PostToolUse", "Write", "marker", "Marca de confidencialidad"),
]
# Hooks de sesión: (evento, comando). session-start trae el status y avisa cierres pendientes; session-end los anota.
SESSION = [
    ("SessionStart", 'bash "$HOME/claude-workspace/harness/hooks/session-start.sh"'),
    ("SessionEnd", 'bash "$HOME/claude-workspace/harness/hooks/session-end.sh"'),
]


def main() -> None:
    remove = "--remove" in sys.argv
    d = json.loads(SETTINGS.read_text(encoding="utf-8"))
    shutil.copy(SETTINGS, SETTINGS.with_name(f"settings.json.bak-harness-{dt.datetime.now():%Y%m%d%H%M%S}"))
    hooks = d.setdefault("hooks", {})
    for event, matcher, guard, msg in WANTED:
        cmd = f"{GUARD} {guard}"
        entries = hooks.setdefault(event, [])
        for e in entries:
            e["hooks"] = [h for h in e.get("hooks", []) if h.get("command") != cmd]
        hooks[event] = [e for e in entries if e.get("hooks")]
        if not remove:
            hooks[event].append({"matcher": matcher, "hooks": [{"type": "command", "command": cmd, "statusMessage": msg, "timeout": 10}]})
    for event, cmd in SESSION:
        script = cmd.rsplit("/", 1)[1].rstrip('"')
        entries = hooks.setdefault(event, [])
        for e in entries:
            e["hooks"] = [h for h in e.get("hooks", []) if script not in h.get("command", "")]
        hooks[event] = [e for e in entries if e.get("hooks")]
        if not remove:
            hooks[event].append({"hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
    SETTINGS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("guardas quitadas" if remove else "guardas registradas (reiniciar la sesión para que tomen efecto)")


if __name__ == "__main__":
    main()
