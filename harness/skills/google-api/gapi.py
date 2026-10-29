# -*- coding: utf-8 -*-
"""Drive, Docs y Sheets por API directa, con los tokens de google-login.py.

Uso (siempre con el python del venv del harness):
  gapi.py ls <folder_id>                                  drive.readonly
  gapi.py read <file_id> [--out archivo]                  drive.readonly  (Doc → Markdown, Sheet → CSV, resto binario)
  gapi.py sheet <sheet_id> --range "Hoja!A1:F50"          spreadsheets.readonly
  gapi.py replace <doc_id> --find X --replace Y [--apply] documents       (sin --apply solo muestra las coincidencias)
  gapi.py upload <archivo> --folder <folder_id>           drive.file      (crea un archivo nuevo)
  gapi.py upload <archivo> --update <file_id>             drive           (reemplaza el contenido de uno existente)
"""
import argparse
import csv
import io
import mimetypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "claude-workspace" / "harness" / "scripts"))
import google_auth  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPORTS = {
    "application/vnd.google-apps.document": ("text/markdown", ".md"),
    "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
    "application/vnd.google-apps.presentation": ("text/plain", ".txt"),
}


def service(name, version, scopes):
    from googleapiclient.discovery import build

    return build(name, version, credentials=google_auth.get_creds(scopes), cache_discovery=False)


def cmd_ls(a):
    drive = service("drive", "v3", ["drive.readonly"])
    q = f"'{a.folder_id}' in parents and trashed = false"
    page = None
    while True:
        r = drive.files().list(q=q, fields="nextPageToken, files(id,name,mimeType,modifiedTime)",
                               pageToken=page, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        for f in r.get("files", []):
            print(f"{f['id']}\t{f['modifiedTime'][:10]}\t{f['mimeType'].rsplit('.', 1)[-1]}\t{f['name']}")
        page = r.get("nextPageToken")
        if not page:
            break


def cmd_read(a):
    from googleapiclient.http import MediaIoBaseDownload

    drive = service("drive", "v3", ["drive.readonly"])
    meta = drive.files().get(fileId=a.file_id, fields="name,mimeType", supportsAllDrives=True).execute()
    if meta["mimeType"] in EXPORTS:
        mime, _ = EXPORTS[meta["mimeType"]]
        req = drive.files().export_media(fileId=a.file_id, mimeType=mime)
    else:
        req = drive.files().get_media(fileId=a.file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    if a.out:
        Path(a.out).write_bytes(buf.getvalue())
        print(f"ok: {meta['name']} → {a.out}")
    elif meta["mimeType"] in EXPORTS:
        print(buf.getvalue().decode("utf-8"))
    else:
        raise SystemExit(f"{meta['name']} es binario ({meta['mimeType']}): usá --out <archivo>.")


def cmd_sheet(a):
    sheets = service("sheets", "v4", ["spreadsheets.readonly"])
    rows = sheets.spreadsheets().values().get(spreadsheetId=a.sheet_id, range=a.range).execute().get("values", [])
    csv.writer(sys.stdout).writerows(rows)


def doc_text(doc):
    out = []
    for el in doc.get("body", {}).get("content", []):
        for pe in el.get("paragraph", {}).get("elements", []):
            out.append(pe.get("textRun", {}).get("content", ""))
    return "".join(out)


def cmd_replace(a):
    docs = service("docs", "v1", ["documents"])
    doc = docs.documents().get(documentId=a.doc_id).execute()
    lines = [ln for ln in doc_text(doc).splitlines() if a.find in ln]
    print(f"{doc['title']}: {len(lines)} párrafo(s) con '{a.find}'")
    for ln in lines[:20]:
        print(f"  - {ln.strip()[:160]}")
    if not a.apply:
        print("dry-run: no se cambió nada. Repetí con --apply después del OK.")
        return
    body = {"requests": [{"replaceAllText": {"containsText": {"text": a.find, "matchCase": True}, "replaceText": a.replace}}]}
    r = docs.documents().batchUpdate(documentId=a.doc_id, body=body).execute()
    n = r["replies"][0].get("replaceAllText", {}).get("occurrencesChanged", 0)
    print(f"ok: {n} reemplazo(s)")


def cmd_upload(a):
    from googleapiclient.http import MediaFileUpload

    path = Path(a.file)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    media = MediaFileUpload(str(path), mimetype=mime, resumable=True)
    if a.update:
        drive = service("drive", "v3", ["drive"])
        f = drive.files().update(fileId=a.update, media_body=media, fields="id,name,webViewLink",
                                 supportsAllDrives=True).execute()
    else:
        drive = service("drive", "v3", ["drive.file"])
        f = drive.files().create(body={"name": path.name, "parents": [a.folder]}, media_body=media,
                                 fields="id,name,webViewLink", supportsAllDrives=True).execute()
    print(f"ok: {f['name']} → {f['webViewLink']}")


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sp = ap.add_subparsers(dest="cmd", required=True)
p = sp.add_parser("ls"); p.add_argument("folder_id"); p.set_defaults(fn=cmd_ls)
p = sp.add_parser("read"); p.add_argument("file_id"); p.add_argument("--out"); p.set_defaults(fn=cmd_read)
p = sp.add_parser("sheet"); p.add_argument("sheet_id"); p.add_argument("--range", required=True); p.set_defaults(fn=cmd_sheet)
p = sp.add_parser("replace"); p.add_argument("doc_id"); p.add_argument("--find", required=True)
p.add_argument("--replace", required=True); p.add_argument("--apply", action="store_true"); p.set_defaults(fn=cmd_replace)
p = sp.add_parser("upload"); p.add_argument("file"); g = p.add_mutually_exclusive_group(required=True)
g.add_argument("--folder"); g.add_argument("--update"); p.set_defaults(fn=cmd_upload)
args = ap.parse_args()
args.fn(args)
