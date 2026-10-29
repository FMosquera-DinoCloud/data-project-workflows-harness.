#!/usr/bin/env bash
# SessionEnd: si la sesión era de un proyecto del harness y terminó sin session-close, la anota para que la
# próxima sesión arme el cierre (session-start.sh lo avisa). No llama al modelo ni escribe en git.
[ "${HARNESS_UNATTENDED:-0}" = 1 ] && exit 0
input="$(cat)"
PY=""
for c in py python3 python; do "$c" -c 'pass' >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || exit 0
read -r sid transcript reason cwd < <(INPUT="$input" "$PY" -c '
import json, os
d = json.loads(os.environ["INPUT"])
print(d.get("session_id",""), d.get("transcript_path","").replace(" ", "\x1f"), d.get("reason",""), d.get("cwd","").replace(" ", "\x1f"))
' 2>/dev/null | tr -d '\r')
transcript="${transcript//$'\x1f'/ }"; cwd="${cwd//$'\x1f'/ }"
[ -n "$sid" ] && [ -n "$transcript" ] || exit 0
command -v cygpath >/dev/null 2>&1 && cwd="$(cygpath -u "$cwd")"
root=""; d="$cwd"
while [ "$d" != "/" ] && [ -n "$d" ]; do
  if [ -f "$d/project.toml" ] && grep -q '^\[project\]' "$d/project.toml"; then root="$d"; break; fi
  d="$(dirname "$d")"
done
[ -n "$root" ] || exit 0
command -v cygpath >/dev/null 2>&1 && root="$(cygpath -w "$root")"
"$PY" -X utf8 "$HOME/claude-workspace/harness/scripts/session_close.py" record "$root" "$sid" "$transcript" "$reason" 2>/dev/null
exit 0
