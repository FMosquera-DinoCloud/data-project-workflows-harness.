#!/usr/bin/env python3
"""Guardas determinísticas del harness (hooks de Claude Code). Lee el JSON del hook por stdin.

  outbound          PreToolUse  mcp__claude_ai_* que escriben afuera: bloquea credenciales y, dentro de un
                                proyecto del harness, ids internos (D-xx, T-xxx, A-xx, H-xx, Ref xx).
  unattended-write  PreToolUse  Write/Edit: con HARNESS_UNATTENDED=1 no deja tocar CLAUDE.md, .claude/,
                                project.toml ni harness/ (una rutina que lee mails no se reescribe las reglas).
  marker            PostToolUse Write de .md en un proyecto del harness: exige la marca de confidencialidad.

Bloquear = exit 2 con el motivo por stderr. Fuera de un proyecto del harness solo corre la guarda de credenciales.
"""
import json
import os
import re
import sys
from pathlib import Path

MARK = "dinocloud internal - confidential"
CREDS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"ghp_[A-Za-z0-9]{30,}", "token de GitHub"),
    (r"xox[abprs]-[A-Za-z0-9-]{10,}", "token de Slack"),
    (r"sk-ant-[A-Za-z0-9_-]{20,}", "API key de Anthropic"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "clave privada PEM"),
    (r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT"),
]
INTERNAL_IDS = re.compile(r"\b[DATH]-\d{2,3}\b|\bRef \d{1,3}\b")
WRITE_VERB = re.compile(r"_(create|update|send|reply|forward|add|schedule|share|attach|merge|move|draft)(_|$)", re.I)
OUTBOUND = re.compile(r"^mcp__claude_ai_(ClickUp|Slack|Gmail|Google_Drive|Google_Docs|Google_Slides|Notion|Outline|Claude_Docs)__")
PROTECTED_LOWER = {"claude.md", "agents.md", "project.toml", ".gitattributes", ".gitignore"}
# Sin re.I (-C no es -c). Se evalúa con el argumento de -m/--message vaciado, para que un mensaje de commit no dispare la guarda.
# Opciones globales de git (-C dir, -P, --no-pager...) pueden ir antes del subcomando; -c y --config-env no se consumen como opción.
GIT_CONFIG_CHANGE = re.compile(
    r"\bgit(?:\s+(?:-C\s+\S+|-[A-Za-bd-z]\b|--(?!config-env)[\w-]+(?:=\S+)?))*\s+(?:config\b|-c\s|--config-env\b)"
    r"|\bGIT_[A-Z_]+=")
MARK_SKIP_DIRS = {"drive", "clickup", ".claude", ".harness", "node_modules", ".git", "worktrees"}


def deny(msg: str) -> None:
    print(f"[harness] {msg}", file=sys.stderr)
    sys.exit(2)


def project_root(cwd: str) -> Path | None:
    d = Path(cwd or ".").resolve()
    for p in [d, *d.parents]:
        pt = p / "project.toml"
        if pt.is_file() and "[project]" in pt.read_text(encoding="utf-8", errors="ignore"):
            return p
    return None


def outbound(ev: dict) -> None:
    name = ev.get("tool_name", "")
    if not (OUTBOUND.match(name) and WRITE_VERB.search(name)):
        return
    text = json.dumps(ev.get("tool_input", {}), ensure_ascii=False)
    for rx, label in CREDS:
        if re.search(rx, text):
            deny(f"{name}: el contenido tiene una credencial ({label}). No se envía; usá variables de entorno o Secrets Manager.")
    if project_root(ev.get("cwd", "")) and INTERNAL_IDS.search(text):
        found = sorted(set(INTERNAL_IDS.findall(text)))[:5]
        deny(f"{name}: el texto para otras personas no lleva ids internos ({', '.join(found)}). "
             "Reescribilo con el fundamento en palabras y los términos que ve el lector en ClickUp o en el documento.")


def _norm(x) -> str:
    return os.path.normcase(os.path.realpath(str(x))).lower()


def _protected(path: str) -> bool:
    rp = Path(os.path.realpath(path))
    ws = _norm(Path.home() / "claude-workspace" / "harness")
    n = _norm(rp)
    parts = [x.lower() for x in rp.parts]
    return (rp.name.lower() in PROTECTED_LOWER or n == ws or n.startswith(ws + os.sep)
            or ".claude" in parts or ".git" in parts
            or rp.as_posix().lower().endswith(".harness/team-mirror-review.csv"))


def _sin_comillas(cmd: str) -> str:
    """Vacía el mensaje de commit (-m/--message) y quita las comillas del resto: `git "config" x` es `git config x`."""
    cmd = re.sub(r"(-m|--message)([ =])(?:'[^']*'|\"[^\"]*\")", r"msg", cmd)
    return cmd.replace('"', "").replace("'", "")


def unattended_write(ev: dict) -> None:
    """Write/Edit y, porque la rutina tiene mv/cp en su allowlist, también Bash que escriba sobre rutas protegidas."""
    if os.environ.get("HARNESS_UNATTENDED") != "1":
        return
    ti = ev.get("tool_input") or {}
    if ev.get("tool_name") == "Bash":
        cmd = ti.get("command", "")
        # La configuración de git (core.sshCommand, hooksPath, alias, credential.helper) ejecuta código en el push: no se toca.
        if GIT_CONFIG_CHANGE.search(_sin_comillas(cmd)):
            deny("rutina desatendida: no puede cambiar la configuración de git (git config, git -c, --config-env, variables GIT_*).")
        if re.search(r"\b(mv|cp|tee|sed -i|install|ln)\b|>", cmd) and re.search(
                r"CLAUDE\.md|AGENTS\.md|project\.toml|\.gitattributes|\.gitignore|\.claude|\.git[/\\]|team-mirror-review|claude-workspace[/\\]+harness", cmd, re.I):
            deny("rutina desatendida: no puede escribir por Bash sobre CLAUDE.md, project.toml, .claude/, .git/ ni el harness.")
        return
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path or _protected(path):
        deny(f"rutina desatendida: no puede modificar {Path(path).name or 'esa ruta'} ni la configuración del harness. Dejalo como propuesta en el digest.")


def marker(ev: dict) -> None:
    path = (ev.get("tool_input") or {}).get("file_path") or ""
    p = Path(path)
    if p.suffix.lower() != ".md":
        return
    root = project_root(str(p.parent))
    if not root:
        return
    try:
        rel = p.resolve().relative_to(root.resolve())
    except ValueError:
        return
    if rel.parts and rel.parts[0] in MARK_SKIP_DIRS:
        return
    head = "\n".join(p.read_text(encoding="utf-8", errors="ignore").splitlines()[:8]).lower() if p.exists() else ""
    if MARK not in head:
        deny(f"{rel.as_posix()}: falta la marca 'DinoCloud Internal - Confidential' en las primeras líneas (regla del proyecto; para el cliente, pedir destinatario y branding).")


GUARDS = {"outbound": outbound, "unattended-write": unattended_write, "marker": marker}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in GUARDS:
        sys.exit(0)
    try:
        event = json.load(sys.stdin)
    except Exception:
        # Sin poder leer el evento no se sabe qué se quiere hacer: una rutina desatendida falla cerrado.
        if os.environ.get("HARNESS_UNATTENDED") == "1":
            deny("no se pudo leer el evento del hook")
        sys.exit(0)
    GUARDS[which](event)
