#!/usr/bin/env python3
"""
embed_svg_assets — vuelve autocontenido el SVG que genera graphviz.

Por qué existe: `diagrams` dibuja cada servicio AWS como un PNG externo, y el SVG
resultante lo referencia por **path absoluto del disco**:

    <image xlink:href="/Users/.../site-packages/resources/aws/compute/lambda.png" .../>

Ese SVG se ve bien localmente y se rompe en cualquier otro lado: dentro de un
Artifact (el CSP bloquea hosts externos y el path local no existe), en un README
de GitHub, o en un doc compartido. Este script reemplaza cada referencia por un
data URI base64, dejando un único archivo que se puede pegar en cualquier HTML.

Seguridad: la salida de este script se publica (Artifact, README, mail), así que
sólo se embeben **imágenes** — extensión en IMAGE_SUFFIXES y mime `image/*` — y
con topes de tamaño. Un `href` a un `.env`, a una key o a cualquier otro archivo
se deja intacto y se reporta por stderr: base64 no es cifrado, y un archivo
horneado acá sale publicado en texto claro para cualquiera que abra el link.

Uso:
    python embed_svg_assets.py diagrama.svg                 # → diagrama.inline.svg
    python embed_svg_assets.py diagrama.svg -o salida.svg
    python embed_svg_assets.py diagrama.svg --for-html      # sin <?xml?> ni DOCTYPE
    python embed_svg_assets.py diagrama.svg --stdout        # a stdout, para pipes
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path

# href o xlink:href, comillas simples o dobles.
HREF_RE = re.compile(r"""(?P<attr>(?:xlink:)?href)\s*=\s*(?P<q>["'])(?P<url>[^"']+)(?P=q)""")

SKIP_PREFIXES = ("data:", "http://", "https://", "#")

# Lo único que se embebe. Sin esta lista, cualquier path que apareciera en un
# href terminaba en base64 dentro de un archivo que se publica.
IMAGE_SUFFIXES = {".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp"}

MAX_FILE_BYTES = 4 * 1024 * 1024   # un ícono de arquitectura pesa ~5 KB
MAX_TOTAL_BYTES = 12 * 1024 * 1024  # el techo de un Artifact es 16 MB


def _diagrams_resources() -> list[Path]:
    """Directorios de íconos del paquete `diagrams`, si está importable.

    `Node._load_icon()` los resuelve como `<dir del paquete>/../<_icon_dir>`, o sea
    `site-packages/resources/...` — un nivel arriba del paquete. Se devuelven las
    dos variantes para no depender del layout de una versión puntual.
    """
    try:
        import diagrams
    except Exception:
        return []
    pkg = Path(diagrams.__file__).parent
    return [(d / "resources").resolve() for d in (pkg.parent, pkg) if (d / "resources").is_dir()]


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def to_data_uri(path: Path, mime: str) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def inline(svg_text: str, base_dir: Path) -> tuple[str, int, list[str], list[str], list[str]]:
    """Devuelve (svg, embebidos, no_resueltos, rechazados_por_politica, fuera_del_proyecto)."""
    embedded = 0
    total_bytes = 0
    missing: list[str] = []
    skipped: list[str] = []
    outside: list[str] = []

    expected_roots = [base_dir.resolve(), Path.cwd().resolve(), *_diagrams_resources()]

    def repl(match: re.Match) -> str:
        nonlocal embedded, total_bytes
        url = match.group("url")
        if url.startswith(SKIP_PREFIXES):
            return match.group(0)

        candidate = Path(url)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        # resolve() colapsa `..` y symlinks: lo que se lee es lo que se ve.
        candidate = candidate.expanduser().resolve()

        if not candidate.is_file():
            missing.append(url)
            return match.group(0)

        mime = mimetypes.guess_type(candidate.name)[0] or ""
        if candidate.suffix.lower() not in IMAGE_SUFFIXES or not mime.startswith("image/"):
            skipped.append(f"{url} (no es una imagen — sólo se embeben imágenes)")
            return match.group(0)

        size = candidate.stat().st_size
        if size > MAX_FILE_BYTES:
            skipped.append(f"{url} ({size // 1024} KB > {MAX_FILE_BYTES // 1024} KB)")
            return match.group(0)
        if total_bytes + size > MAX_TOTAL_BYTES:
            skipped.append(f"{url} (se pasa el tope acumulado de {MAX_TOTAL_BYTES // 1024} KB)")
            return match.group(0)

        if not any(_inside(candidate, root) for root in expected_roots):
            outside.append(str(candidate))

        embedded += 1
        total_bytes += size
        return f'{match.group("attr")}="{to_data_uri(candidate, mime)}"'

    return HREF_RE.sub(repl, svg_text), embedded, missing, skipped, outside


def strip_prolog(svg_text: str) -> str:
    """Deja sólo el <svg>...</svg>, listo para inyectar en un documento HTML."""
    svg_text = re.sub(r"<\?xml[^>]*\?>\s*", "", svg_text)
    svg_text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg_text, flags=re.IGNORECASE)
    svg_text = re.sub(r"<!--.*?-->\s*", "", svg_text, flags=re.DOTALL)
    start = svg_text.find("<svg")
    return svg_text[start:] if start >= 0 else svg_text


def make_responsive(svg_text: str) -> str:
    """Cambia el ancho fijo por 100% conservando el viewBox (necesario en Artifacts).

    La altura se saca y no se reemplaza: `height="auto"` no es una longitud SVG
    válida. Con el viewBox presente, el alto lo resuelve el aspect ratio y el CSS
    del contenedor (`.canvas svg { height: auto }` en artifact-shell.html).
    """
    head_match = re.search(r"<svg\b[^>]*>", svg_text)
    if not head_match:
        return svg_text
    head = head_match.group(0)
    if "viewBox" not in head:
        return svg_text
    new_head = re.sub(r'\s(width|height)="[^"]*"', "", head)
    new_head = new_head.replace("<svg", '<svg width="100%"', 1)
    return svg_text.replace(head, new_head, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description="Embebe los PNG de un SVG de graphviz como data URIs.")
    ap.add_argument("svg", type=Path, help="SVG de entrada (el que generó diagrams)")
    ap.add_argument("-o", "--output", type=Path, help="destino (default: <nombre>.inline.svg)")
    ap.add_argument("--for-html", action="store_true", help="sin prólogo XML y con ancho responsive")
    ap.add_argument("--stdout", action="store_true", help="escribe a stdout en vez de a un archivo")
    args = ap.parse_args()

    if not args.svg.is_file():
        print(f"error: no existe {args.svg}", file=sys.stderr)
        return 1

    text = args.svg.read_text(encoding="utf-8")
    text, embedded, missing, skipped, outside = inline(text, args.svg.resolve().parent)

    if args.for_html:
        text = make_responsive(strip_prolog(text))

    for url in missing:
        print(f"aviso: no pude resolver {url}", file=sys.stderr)
    for item in skipped:
        print(f"AVISO DE SEGURIDAD: no embebí {item}", file=sys.stderr)
    for path in outside:
        print(f"aviso: embebido desde fuera del proyecto: {path}", file=sys.stderr)

    if args.stdout:
        sys.stdout.write(text)
    else:
        out = args.output or args.svg.with_suffix(".inline.svg")
        out.write_text(text, encoding="utf-8")
        print(f"{embedded} imagen(es) embebida(s) → {out}")

    if embedded == 0 and not missing and not skipped:
        print("aviso: el SVG no referenciaba imágenes externas", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
