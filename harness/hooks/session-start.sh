#!/usr/bin/env bash
# SessionStart: si la sesión arranca dentro de un proyecto del harness, trae el último status y avisa de problemas.
input="$(cat)"
# Git Bash en Windows no trae jq: se usa el python del sistema para leer y escribir el JSON.
PYJ=""
# En Windows, python3 suele ser el stub de la Store: se prueba que corra de verdad.
command -v jq >/dev/null 2>&1 || for c in py python3 python; do "$c" -c 'pass' >/dev/null 2>&1 && { PYJ="$c"; break; }; done
field() {  # $1 campo del JSON de entrada
  if [ -z "$PYJ" ]; then jq -r --arg k "$1" '.[$k] // empty' <<<"$input" 2>/dev/null
  else "$PYJ" -c 'import json,sys; print(json.load(sys.stdin).get(sys.argv[1],""))' "$1" <<<"$input" 2>/dev/null | tr -d '\r'; fi
}
cwd="$(field cwd)"
# source=compact: la sesión sigue después de compactar; transcript_path conserva la conversación completa.
source="$(field source)"
transcript="$(field transcript_path)"
command -v cygpath >/dev/null 2>&1 && [ -n "$cwd" ] && cwd="$(cygpath -u "$cwd")"
[ -n "$cwd" ] || cwd="$PWD"

emit() {  # $1 contexto para Claude, $2 mensaje para el usuario
  if [ -z "$PYJ" ]; then
    jq -n --arg ctx "$1" --arg msg "$2" \
      '{systemMessage: $msg, hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
  else
    CTX="$1" MSG="$2" PYTHONIOENCODING=utf-8 "$PYJ" -c 'import json,os; print(json.dumps({"systemMessage": os.environ["MSG"], "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": os.environ["CTX"]}}, ensure_ascii=False))'
  fi
}

root=""; d="$cwd"
while [ "$d" != "/" ] && [ -n "$d" ]; do
  if [ -f "$d/project.toml" ] && grep -q '^\[project\]' "$d/project.toml"; then root="$d"; break; fi
  d="$(dirname "$d")"
done
if [ -z "$root" ]; then
  # La auto memory se guarda por carpeta: lo que se aprenda de un proyecto acá queda fuera de su repo.
  case "${cwd%/}" in
    "${HOME%/}"|"${HOME%/}/dino-projects")
      emit "La sesión no está dentro de un proyecto del harness. Si el trabajo es de un proyecto, lo que surja (decisiones, pendientes, contexto) se anota en el repo de ese proyecto, no en la auto memory; la auto memory es solo para preferencias personales." \
        "Fuera de un proyecto del harness: para trabajar uno, abrí Claude en ~/dino-projects/<proyecto>." ;;
  esac
  exit 0
fi

name="$(basename "$root")"
today="$(date +%F)"; dow="$(date +%u)"
latest="$(ls -1 "$root"/status/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md 2>/dev/null | sort | tail -1)"
notes=()

if [ -n "$latest" ]; then
  head_txt="$(head -n 14 "$latest")"
  [ "$(basename "$latest" .md)" = "$today" ] || { [ "$dow" -le 5 ] && notes+=("El último status es del $(basename "$latest" .md): la rutina de hoy no corrió o falló."); }
else
  head_txt=""; notes+=("Todavía no hay status: correr project-status.")
fi

if [ -f "$root/.harness/run-status" ]; then
  rc="$(sed -n 's/^exit=//p' "$root/.harness/run-status")"
  grep -q '^dm=fallo' "$root/.harness/run-status" && notes+=("El DM de Slack de la última rutina no se mandó: revisar que el conector de Slack de claude.ai esté conectado.")
  [ "${rc:-0}" = "0" ] || notes+=("La última rutina terminó con error (exit $rc). Log: $(sed -n 's/^log=//p' "$root/.harness/run-status")")
fi
[ "$dow" = "5" ] && notes+=("Es viernes: revisar y cargar horas con weekly-hours.")

pending="$(grep -c '^- ' "$root"/context/digest/"$today".md 2>/dev/null || true)"

# Sesiones que terminaron sin session-close (las anota session-end.sh). Las rutinas desatendidas no las cierran.
unclosed=""
if [ "${HARNESS_UNATTENDED:-0}" != 1 ]; then
  SC_PY="$PYJ"; [ -n "$SC_PY" ] || for c in py python3 python; do "$c" -c 'pass' >/dev/null 2>&1 && { SC_PY="$c"; break; }; done
  sc_root="$root"; command -v cygpath >/dev/null 2>&1 && sc_root="$(cygpath -w "$root")"
  [ -n "$SC_PY" ] && unclosed="$("$SC_PY" -X utf8 "$HOME/claude-workspace/harness/scripts/session_close.py" pending "$sc_root" 2>/dev/null | tr -d '\r')"
fi
if [ -n "$unclosed" ]; then
  n_unclosed="$(printf '%s\n' "$unclosed" | grep -c .)"
  notes=("Hay $n_unclosed sesión(es) que terminaron sin cierre: antes de seguir, ejecutá la skill session-close sobre esos transcripts (fecha · id · transcript):
$(printf '%s\n' "$unclosed" | awk -F'\t' '{print "  - " $1 " · " $2 " · " $3}')" "${notes[@]}")
fi

# El resumen de la compactación pierde detalle: antes de seguir se rescata lo que no quedó guardado.
if [ "$source" = "compact" ]; then
  notes=("La conversación se acaba de compactar. Antes de seguir con el pedido, revisá si quedó algo sin guardar en el proyecto (ver \"Al compactar\" en las convenciones) y guardalo; si hace falta un detalle que el resumen perdió, buscalo en el transcript ($transcript). Avisá en una línea qué guardaste, o que no había nada." "${notes[@]}")
fi

ctx="Proyecto del harness: $name ($root). Reglas: ~/claude-workspace/harness/reference/conventions.md. Buscar primero en index.toon."
[ -n "$head_txt" ] && ctx="$ctx

Último status ($latest):
$head_txt"
if [ "${#notes[@]}" -gt 0 ]; then
  ctx="$ctx

Avisos del harness:"
  for n in "${notes[@]}"; do ctx="$ctx
- $n"; done
fi

msg="[$name] $( [ -n "$latest" ] && sed -n 's/.*\*\*Salud:\*\* *\([A-Z]*\).*/salud \1/p' "$latest" | head -1 )"
[ "${#notes[@]}" -gt 0 ] && msg="$msg · ${notes[0]}"
[ "${pending:-0}" -gt 0 ] && msg="$msg · $pending ítems nuevos hoy en el digest"

emit "$ctx" "$msg"
