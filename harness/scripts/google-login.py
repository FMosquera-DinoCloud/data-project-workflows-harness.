# -*- coding: utf-8 -*-
"""Primer consentimiento OAuth de Google: abre el navegador y guarda el token.

Uso: <python del venv> google-login.py --scopes drive.readonly [documents ...]
Scopes cortos: drive.readonly, drive.file, drive, documents, documents.readonly,
spreadsheets.readonly, spreadsheets. Pedí el mínimo que necesites.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import google_auth  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--scopes", nargs="+", required=True)
args = ap.parse_args()
print(f"ok: token en {google_auth.login(args.scopes)}")
