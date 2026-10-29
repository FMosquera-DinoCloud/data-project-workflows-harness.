---
name: google-api
description: "Lee y edita archivos de Google Drive, Docs y Sheets por API directa (OAuth propio): listar una carpeta, leer un Doc como Markdown o una Sheet como CSV, reemplazar texto en un Google Doc, subir o reemplazar un archivo en Drive. Usar cuando se pida leer, resumir, editar, actualizar o subir un Google Doc, Sheet, .docx, PNG o PDF en Drive, o cuando el conector de Drive no alcance (escritura, rutinas desatendidas, planillas por rango). Use to read/edit Google Docs/Sheets or upload files to Drive via the Google APIs."
---

# google-api

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`. Para mantener el espejo `drive/` de un proyecto se usa `drive-mirror`; esta skill es para leer o escribir un archivo puntual.

## Antes de empezar

- Python del venv del harness: `PY=~/claude-workspace/harness/.venv/Scripts/python.exe` (Windows) o `~/claude-workspace/harness/.venv/bin/python` (macOS).
- Script: `$PY ~/claude-workspace/harness/skills/google-api/gapi.py <comando>` (ver `--help`).
- Si falta el cliente OAuth o el token, el script lo dice con el paso a seguir. El login lo corre el usuario (abre el navegador): `$PY ~/claude-workspace/harness/scripts/google-login.py --scopes <scope>`.
- El ID de un archivo sale de su URL: `docs.google.com/document/d/<ID>/…`, `drive.google.com/drive/folders/<ID>`.

| Comando | Scope | Escribe |
|---|---|---|
| `ls <folder_id>` | `drive.readonly` | no |
| `read <file_id> [--out f]` | `drive.readonly` | no |
| `sheet <id> --range "Hoja!A1:F50"` | `spreadsheets.readonly` | no |
| `replace <doc_id> --find X --replace Y` | `documents` | solo con `--apply` |
| `upload <archivo> --folder <id>` | `drive.file` | sí, crea |
| `upload <archivo> --update <file_id>` | `drive` | sí, reemplaza |

## Reglas

- **Escritura solo con OK explícito.** `replace` primero sin `--apply` y se le muestran al usuario las coincidencias; `upload` se anuncia con el destino antes de correrlo. En modo desatendido no se escribe nunca.
- Material del cliente: solo si el proyecto tiene `scope_confirmed = true`.
- No guardar en el repo el contenido crudo de un archivo leído: se resume, se cita lo necesario y se linkea.
- Los tokens y el cliente OAuth viven en `~/.config/claude-harness/` y nunca se copian, se muestran ni se commitean.

## Errores comunes

| Error | Qué hacer |
|---|---|
| `Falta el cliente OAuth` | Seguir el paso que imprime el script (tu proyecto de Google Cloud, app de escritorio). |
| `No hay token para …` | El usuario corre `google-login.py --scopes …` con ese scope. |
| `access_denied` en el navegador | Cuenta fuera de dinocloud.com, o pantalla de consentimiento no Internal. |
| `403 … has not been used in project` | Habilitar la API (Drive, Docs o Sheets) en el proyecto de Google Cloud. |
| `404 File not found` | El archivo no está compartido con la cuenta del usuario. |
| `invalid_grant` | Token vencido o revocado: borrar `~/.config/claude-harness/token-*.json` y volver a loguear. |
