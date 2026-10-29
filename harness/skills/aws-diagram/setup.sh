#!/usr/bin/env bash
# claude/skills/aws-diagram/setup.sh
#
# Bootstrap idempotente del entorno de diagramas AWS:
#   graphviz (binario `dot`) + venv dedicado + mingrammer/diagrams + catálogo de nodos.
#
# Uso:
#   bash setup.sh          # instala lo que falte
#   bash setup.sh --check  # sólo diagnostica, no instala (exit 1 si falta algo)
#
# Todo vive en ~/.dino/aws-diagram/ para no ensuciar ningún proyecto ni el
# Python del sistema (que en macOS es 3.9 y está bloqueado por PEP 668).

set -euo pipefail

DINO_HOME="${HOME}/.dino/aws-diagram"
VENV="${DINO_HOME}/.venv"
CATALOG="${DINO_HOME}/aws-nodes.txt"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

# Versión pineada a propósito: `pip install diagrams` sin pin hace que un script
# que se anuncia idempotente traiga una release distinta en cada corrida. 0.25.1
# es la versión con la que se validó la skill.
DIAGRAMS_VERSION="${DINO_DIAGRAMS_VERSION:-0.25.1}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓${NC} $*"; }
warn() { echo -e "${YELLOW}  ⚠${NC} $*"; }
err()  { echo -e "${RED}  ✗${NC} $*"; }
info() { echo -e "  →  $*"; }
section() { echo -e "\n${GREEN}▶ $*${NC}"; }

missing=0

# Git Bash en Windows: el venv usa Scripts/python.exe y el python nativo no
# entiende paths /c/..., así que todo path que se le pasa va por topy().
IS_WINDOWS=0
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) IS_WINDOWS=1; export PYTHONIOENCODING=utf-8 ;; esac
topy() { if [[ ${IS_WINDOWS} -eq 1 ]]; then cygpath -w "$1"; else echo "$1"; fi; }
venv_python() { if [[ ${IS_WINDOWS} -eq 1 ]]; then echo "${VENV}/Scripts/python.exe"; else echo "${VENV}/bin/python"; fi; }

# winget instala graphviz pero no lo agrega al PATH de la sesión actual.
GRAPHVIZ_WIN="/c/Program Files/Graphviz/bin"
if [[ ${IS_WINDOWS} -eq 1 && -x "${GRAPHVIZ_WIN}/dot.exe" ]]; then
  export PATH="${GRAPHVIZ_WIN}:${PATH}"
fi

# ── 1. graphviz ───────────────────────────────────────────────────────────────
section "graphviz"
if command -v dot >/dev/null 2>&1; then
  ok "dot $(dot -V 2>&1 | sed 's/^dot - //')"
else
  missing=1
  if [[ ${CHECK_ONLY} -eq 1 ]]; then
    err "graphviz no instalado"
  elif [[ ${IS_WINDOWS} -eq 1 ]] && command -v winget >/dev/null 2>&1; then
    info "instalando graphviz vía winget (puede pedir confirmación de UAC)..."
    winget install --id Graphviz.Graphviz -e --silent --accept-package-agreements --accept-source-agreements
    export PATH="${GRAPHVIZ_WIN}:${PATH}"
    command -v dot >/dev/null 2>&1 || { err "winget terminó pero no encuentro dot en ${GRAPHVIZ_WIN}"; exit 1; }
    ok "graphviz instalado"
  elif command -v brew >/dev/null 2>&1; then
    info "instalando graphviz vía Homebrew (puede tardar unos minutos)..."
    brew install graphviz
    ok "graphviz instalado"
  elif command -v apt-get >/dev/null 2>&1; then
    # El sudo se anuncia: este script viene de un repo compartido y escalar
    # privilegios en silencio no es aceptable.
    info "voy a correr, con sudo: apt-get update && apt-get install -y graphviz"
    sudo apt-get update -qq && sudo apt-get install -y graphviz
    ok "graphviz instalado"
  else
    err "No encontré winget, brew ni apt-get. Instalá graphviz a mano: https://graphviz.org/download/"
    exit 1
  fi
fi

# ── 2. Intérprete Python ──────────────────────────────────────────────────────
# diagrams necesita >= 3.10; el python3 del sistema en macOS suele ser 3.9.
section "Python"
# No alcanza con chequear la versión: una instalación de Homebrew a medio
# actualizar deja intérpretes que importan pero cuyo pyexpat/ssl no linkea, y
# ahí `python -m venv` explota recién en el ensurepip. Probamos de verdad.
py_healthy() {
  "$1" -c 'import sys
if sys.version_info < (3, 10):
    raise SystemExit(1)
import ctypes, pyexpat, ssl, venv, zlib  # noqa: F401
' >/dev/null 2>&1
}

PYBIN=""
BROKEN=()
# En Windows el launcher `py` es la vía confiable; python3 suele ser el stub de la Store.
if [[ ${IS_WINDOWS} -eq 1 ]] && command -v py >/dev/null 2>&1; then
  winpy="$(py -3 -c 'import sys; print(sys.executable)' 2>/dev/null | tr -d '\r')" || winpy=""
  if [[ -n "${winpy}" ]] && py_healthy "$(cygpath -u "${winpy}")"; then
    PYBIN="$(cygpath -u "${winpy}")"
  fi
fi
for candidate in python3.12 python3.13 python3.11 python3.14 python3.10 python3; do
  [[ -n "${PYBIN}" ]] && break
  bin="$(command -v "${candidate}" 2>/dev/null)" || continue
  [[ -z "${bin}" ]] && continue
  if py_healthy "${bin}"; then
    PYBIN="${bin}"
    break
  fi
  "${bin}" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null && BROKEN+=("${bin}")
done

for b in "${BROKEN[@]:-}"; do
  [[ -n "${b}" ]] && warn "descartado ${b} — instalación rota (pyexpat/ssl no linkea). Arreglalo con: brew reinstall ${b##*/}"
done

if [[ -z "${PYBIN}" ]]; then
  err "No encontré un Python >= 3.10 sano. Instalá uno con: brew install python@3.12 (macOS) o winget install Python.Python.3.12 (Windows)"
  exit 1
fi
ok "$("${PYBIN}" --version) → ${PYBIN}"

# ── 3. venv ───────────────────────────────────────────────────────────────────
section "venv"
mkdir -p "${DINO_HOME}"
PY="$(venv_python)"
if [[ -x "${PY}" ]]; then
  ok "venv ya existe → ${VENV}"
else
  missing=1
  if [[ ${CHECK_ONLY} -eq 1 ]]; then
    err "venv no existe"
  else
    info "creando venv en ${VENV}..."
    "${PYBIN}" -m venv "$(topy "${VENV}")"
    "${PY}" -m pip install --quiet --upgrade pip
    ok "venv creado"
  fi
fi

installed_diagrams() {
  [[ -x "${PY}" ]] || return 1
  "${PY}" -c 'from importlib.metadata import version; print(version("diagrams"))' 2>/dev/null
}

# ── 4. diagrams (PyPI oficial, versión pineada) ───────────────────────────────
section "mingrammer/diagrams"
have="$(installed_diagrams || true)"
if [[ "${have}" == "${DIAGRAMS_VERSION}" ]]; then
  ok "diagrams ${have}"
else
  missing=1
  if [[ ${CHECK_ONLY} -eq 1 ]]; then
    if [[ -z "${have}" ]]; then
      err "diagrams no instalado (esperado ${DIAGRAMS_VERSION})"
    else
      err "diagrams ${have} instalado, la skill está validada con ${DIAGRAMS_VERSION}"
    fi
  else
    info "pip install diagrams==${DIAGRAMS_VERSION} (PyPI oficial)..."
    "${PY}" -m pip install --quiet "diagrams==${DIAGRAMS_VERSION}"
    ok "diagrams $(installed_diagrams)"
  fi
fi

# ── 5. Instalar el theme como módulo importable del venv ──────────────────────
# Se refresca en cada corrida para que un `git pull` del toolkit se propague.
section "theme"
if [[ ${CHECK_ONLY} -eq 1 ]]; then
  if [[ -x "${PY}" ]] && "${PY}" -c "import aws_diagram_theme" 2>/dev/null; then
    ok "aws_diagram_theme importable"
    # Una copia vieja en el venv importa igual pero no tiene los cambios de la skill
    # (así pasó con el preset for_doc). Comparar contra la fuente.
    SP_CHECK="$("${PY}" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' | tr -d '')"
    [[ ${IS_WINDOWS} -eq 1 ]] && SP_CHECK="$(cygpath -u "${SP_CHECK}")"
    for pair in "aws_diagram_theme.py:${SP_CHECK}" "embed_svg_assets.py:${DINO_HOME}" "check_legibility.py:${DINO_HOME}"; do
      f="${pair%%:*}"; dest="${pair#*:}"
      if ! cmp -s "${SCRIPT_DIR}/${f}" "${dest}/${f}"; then
        missing=1
        err "${f} instalado está desactualizado o falta → corré: bash setup.sh"
      fi
    done
  else
    missing=1
    err "aws_diagram_theme no importable desde el venv"
  fi
else
  SITE_PACKAGES="$("${PY}" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' | tr -d '\r')"
  [[ ${IS_WINDOWS} -eq 1 ]] && SITE_PACKAGES="$(cygpath -u "${SITE_PACKAGES}")"
  cp "${SCRIPT_DIR}/aws_diagram_theme.py" "${SITE_PACKAGES}/aws_diagram_theme.py"
  ok "aws_diagram_theme → ${SITE_PACKAGES}"

  # El módulo se llamaba dino_diagram_theme. Si queda la copia vieja en el venv,
  # un script con el import viejo sigue andando en silencio contra un archivo que
  # ya nadie actualiza. Mejor que falle con ModuleNotFoundError y se corrija.
  if [[ -f "${SITE_PACKAGES}/dino_diagram_theme.py" ]]; then
    rm -f "${SITE_PACKAGES}/dino_diagram_theme.py"
    warn "removido el módulo viejo dino_diagram_theme del venv"
    info "si algún diagrama todavía lo importa: cambiá el import por aws_diagram_theme"
  fi

  cp "${SCRIPT_DIR}/embed_svg_assets.py" "${DINO_HOME}/embed_svg_assets.py"
  ok "embed_svg_assets.py → ${DINO_HOME}"
  cp "${SCRIPT_DIR}/check_legibility.py" "${DINO_HOME}/check_legibility.py"
  ok "check_legibility.py → ${DINO_HOME}"
fi

# ── 6. Catálogo de nodos AWS ──────────────────────────────────────────────────
# Se GENERA desde el paquete instalado. Es la defensa contra imports inventados:
# la skill grepea este archivo antes de escribir cualquier `from diagrams.aws...`.
section "catálogo de nodos AWS"
if [[ ${CHECK_ONLY} -eq 1 ]]; then
  if [[ -s "${CATALOG}" ]]; then
    ok "catálogo con $(grep -vc '^#' "${CATALOG}") nodos → ${CATALOG}"
  else
    missing=1
    err "catálogo ausente o vacío → ${CATALOG}"
  fi
else
  "${PY}" - "$(topy "${CATALOG}")" <<'PYEOF'
import importlib
import inspect
import pkgutil
import sys

import diagrams.aws as aws
from diagrams import Node

rows = set()
for mod_info in pkgutil.iter_modules(aws.__path__):
    mod_name = f"diagrams.aws.{mod_info.name}"
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        continue
    for attr, obj in vars(mod).items():
        if attr.startswith("_"):
            continue
        if inspect.isclass(obj) and issubclass(obj, Node) and obj.__module__ == mod_name:
            rows.add(f"{mod_name}.{attr}")

out = sys.argv[1]
with open(out, "w", encoding="utf-8") as fh:
    fh.write("# Catálogo generado por setup.sh — NO editar a mano.\n")
    fh.write("# Cada línea es un import válido: from <modulo> import <Clase>\n")
    for row in sorted(rows):
        fh.write(row + "\n")
print(f"  {len(rows)} nodos AWS → {out}")
PYEOF
  ok "catálogo listo"
fi

# ── Resumen ───────────────────────────────────────────────────────────────────
# El veredicto de --check va acá, al final: chequear graphviz/venv/diagrams y
# salir antes dejaba pasar un "entorno completo" sin el theme y sin el catálogo,
# que son justo las dos piezas que usan los Pasos 3 y 4 de la SKILL.md.
echo ""
if [[ ${CHECK_ONLY} -eq 1 ]]; then
  if [[ ${missing} -eq 0 ]]; then
    ok "Entorno completo."
    exit 0
  fi
  err "Faltan piezas — corré: bash setup.sh"
  exit 1
fi

section "aws-diagram — entorno listo"
info "python   : ${PY}"
info "catálogo : ${CATALOG}"
info "templates: ${SCRIPT_DIR}/templates/"
echo ""
info "Probalo:  OUTDIR=/tmp/d ${PY} ${SCRIPT_DIR}/templates/serverless-api.py"
echo ""
