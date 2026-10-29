# -*- coding: utf-8 -*-
"""Credenciales OAuth de Google para los scripts del harness.

El cliente OAuth (tipo "Desktop app") y los tokens viven fuera del repo, en
~/.config/claude-harness/. Hay un token por login; cada script usa el de menos
scopes que le alcance.
"""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "claude-harness"
CLIENT_FILE = CONFIG_DIR / "google-client.json"

SCOPE_ALIASES = {
    "drive.readonly": "https://www.googleapis.com/auth/drive.readonly",
    "drive.file": "https://www.googleapis.com/auth/drive.file",
    "drive": "https://www.googleapis.com/auth/drive",
    "documents": "https://www.googleapis.com/auth/documents",
    "documents.readonly": "https://www.googleapis.com/auth/documents.readonly",
    "spreadsheets.readonly": "https://www.googleapis.com/auth/spreadsheets.readonly",
    "spreadsheets": "https://www.googleapis.com/auth/spreadsheets",
}


def resolve(scopes):
    return sorted(SCOPE_ALIASES.get(s, s) for s in scopes)


def token_path(scopes):
    short = "+".join(sorted(s.rsplit("/", 1)[-1] for s in resolve(scopes)))
    return CONFIG_DIR / f"token-{short}.json"


def find_token(scopes):
    """El token con menos scopes que cubra los pedidos, para no usar uno de escritura si alcanza uno de lectura."""
    need = set(resolve(scopes))
    candidates = []
    for path in CONFIG_DIR.glob("token-*.json"):
        try:
            have = set(json.loads(path.read_text(encoding="utf-8")).get("scopes", []))
        except (OSError, ValueError):
            continue
        if need <= have:
            candidates.append((len(have), path))
    return min(candidates)[1] if candidates else None


def _client_missing():
    raise SystemExit(
        f"Falta el cliente OAuth en {CLIENT_FILE}.\n"
        "  Google Cloud Console (tu proyecto, creado con tu cuenta @dinocloud.com) → APIs y servicios → Credenciales\n"
        "  → Crear credenciales → ID de cliente de OAuth → tipo 'App de escritorio' → Descargar JSON\n"
        f"  y guardalo como {CLIENT_FILE}. No lo commitees ni lo compartas por chat."
    )


def login(scopes):
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CLIENT_FILE.exists():
        _client_missing()
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), resolve(scopes))
    creds = flow.run_local_server(port=0)
    path = token_path(scopes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def get_creds(scopes):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    path = find_token(scopes)
    if path is None:
        raise SystemExit(
            f"No hay token para {' '.join(scopes)}. Corré primero:\n"
            f"  <python del venv> ~/claude-workspace/harness/scripts/google-login.py --scopes {' '.join(scopes)}"
        )
    creds = Credentials.from_authorized_user_file(str(path), json.loads(path.read_text(encoding="utf-8"))["scopes"])
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            path.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise SystemExit(f"El token {path} no es válido: borralo y volvé a correr google-login.py.")
    return creds
