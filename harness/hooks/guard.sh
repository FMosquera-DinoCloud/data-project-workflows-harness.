#!/usr/bin/env bash
# Entrada única de las guardas: guard.sh outbound|unattended-write|marker. Resuelve Python igual que harness-run.
WS="$HOME/claude-workspace"
PY="$WS/harness/.venv/bin/python"
[ -e "$WS/harness/.venv/Scripts/python.exe" ] && PY="$WS/harness/.venv/Scripts/python.exe"
if [ ! -x "$PY" ]; then
  PY=""
  for c in py python3 python; do "$c" -c 'pass' >/dev/null 2>&1 && { PY="$c"; break; }; done
fi
# Sin intérprete, una rutina desatendida falla cerrado; una sesión interactiva sigue.
[ -n "$PY" ] || { [ "${HARNESS_UNATTENDED:-0}" = 1 ] && { echo "[harness] sin Python para las guardas" >&2; exit 2; }; exit 0; }
exec "$PY" -X utf8 "$WS/harness/hooks/guards.py" "$1"
