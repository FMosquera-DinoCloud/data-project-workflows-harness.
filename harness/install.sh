#!/usr/bin/env bash
# Instala el harness en esta Mac. Es idempotente.
# Uso: harness/install.sh [--skills] [--sa] [--hook] [--launchd] [--all] [--status]
#   --skills   symlinks de harness/skills/* en ~/.claude/skills/ (no pisa skills ajenas)
#   --sa       con --skills o --all, suma las skills del perfil SA/TL (harness/skills-sa/*)
#   --hook     registra los hooks de sesión y las guardas en ~/.claude/settings.json (scripts/install_hooks.py, con backup)
#   --launchd  instala y carga las rutinas diaria/semanal/viernes
#   --python   crea harness/.venv con las dependencias de harness/scripts (PyPI)
#   --status   muestra qué está instalado
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DST="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"
AGENTS="$HOME/Library/LaunchAgents"
SA=0

ok()   { printf '  ok   %s\n' "$*"; }
warn() { printf '  !!   %s\n' "$*"; }

install_skills() {
  echo "Skills → $SKILLS_DST"
  mkdir -p "$SKILLS_DST"
  local dirs=("$WS"/harness/skills/*/); [ "$SA" = 1 ] && dirs+=("$WS"/harness/skills-sa/*/)
  for src in "${dirs[@]}"; do
    name="$(basename "$src")"; dst="$SKILLS_DST/$name"
    if [ -L "$dst" ]; then ln -sfn "${src%/}" "$dst"; ok "$name (actualizado)"
    elif [ -e "$dst" ]; then warn "$name: ya existe una skill con ese nombre que no es del harness, no se toca"
    else ln -s "${src%/}" "$dst"; ok "$name"; fi
  done
}

install_hook() {
  echo "Hooks → $SETTINGS"
  local py; py="$(command -v python3 || command -v py || true)"
  [ -n "$py" ] || { warn "falta Python"; return 1; }
  [ -f "$SETTINGS" ] || echo '{}' >"$SETTINGS"
  "$py" "$WS/harness/scripts/install_hooks.py" && ok "hooks de sesión y guardas"
}

install_python() {
  echo "Python → $WS/harness/.venv"
  [ -x "$WS/harness/.venv/bin/python" ] || python3 -m venv "$WS/harness/.venv"
  "$WS/harness/.venv/bin/python" -m pip install -q --upgrade pip
  "$WS/harness/.venv/bin/python" -m pip install -q -r "$WS/harness/requirements.txt" && ok "dependencias desde PyPI"
}

install_launchd() {
  echo "Rutinas → $AGENTS"
  mkdir -p "$AGENTS" "$WS/logs"
  chmod +x "$WS/harness/bin/harness-run"
  for tpl in "$WS"/harness/launchd/*.plist; do
    label="$(basename "$tpl" .plist)"; dst="$AGENTS/$label.plist"
    sed "s#__HOME__#$HOME#g" "$tpl" >"$dst"
    plutil -lint -s "$dst"
    launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$dst" && ok "$label"
  done
}

status() {
  echo "Skills:"; for s in "$WS"/harness/skills/*/ "$WS"/harness/skills-sa/*/; do n="$(basename "$s")"; if [ -L "$SKILLS_DST/$n" ]; then ok "$n"; elif [[ "$s" == */skills-sa/* ]]; then :; else warn "$n no instalada"; fi; done
  echo "Hook:"; grep -q "session-start.sh" "$SETTINGS" 2>/dev/null && ok "SessionStart" || warn "no instalado"
  grep -q "guard.sh" "$SETTINGS" 2>/dev/null && ok "guardas" || warn "guardas no registradas"
  echo "Rutinas:"; for t in "$WS"/harness/launchd/*.plist; do l="$(basename "$t" .plist)"; launchctl print "gui/$(id -u)/$l" >/dev/null 2>&1 && ok "$l" || warn "$l no cargada"; done
}

[ $# -gt 0 ] || { sed -n '2,10p' "$0"; exit 0; }
for arg in "$@"; do [ "$arg" = --sa ] && SA=1; done
for arg in "$@"; do
  case "$arg" in
    --sa) ;;
    --skills) install_skills ;;
    --hook) install_hook ;;
    --launchd) install_launchd ;;
    --python) install_python ;;
    --all) install_skills; install_python; install_hook; install_launchd ;;
    --status) status ;;
    *) echo "opción desconocida: $arg"; exit 2 ;;
  esac
done
