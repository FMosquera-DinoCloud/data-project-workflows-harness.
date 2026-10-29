#!/usr/bin/env python
"""Chequea si un diagrama SVG se lee una vez colocado en un documento.

Un diagrama se escala para entrar en el ancho útil de la página. La letra que ve
el lector es el tamaño de fuente del SVG multiplicado por esa escala. Un diagrama
de 2000 pt de ancho en una página Letter vertical (6,5" = 468 pt) se reduce al
23 %: un label de 11 pt queda en 2,6 pt, ilegible aunque el PNG tenga 300 dpi.

Uso:
    check_legibility.py diagrama.svg [más.svg ...] [--width-in 6.5] [--min-pt 7]

--width-in  ancho útil de la página en pulgadas (Letter vertical con márgenes de
            1" = 6.5; horizontal = 9; A4 vertical con 2,5 cm = 6.3)
--min-pt    tamaño mínimo aceptable de la letra impresa (default 7 pt)

Sale con código 1 si algún diagrama no pasa. Funciona con los SVG de graphviz
(unidades en pt) y con SVG escritos a mano (viewBox en px; 1 px = 0,75 pt).
"""

import argparse
import re
import sys
try:  # parser endurecido si está disponible; los SVG suelen ser propios, pero puede llegar uno de afuera
    import defusedxml.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

UNIT_TO_PT = {"pt": 1.0, "px": 0.75, "in": 72.0, "cm": 28.3465, "mm": 2.83465, "": 0.75}


def _length_pt(value: str) -> float | None:
    m = re.match(r"^\s*([\d.]+)\s*([a-z]*)\s*$", value or "")
    if not m:
        return None
    return float(m.group(1)) * UNIT_TO_PT.get(m.group(2), 0.75)


def measure(path: str) -> tuple[float, float]:
    """Devuelve (ancho del diagrama en pt, tamaño de fuente mínimo en pt)."""
    root = ET.parse(path).getroot()
    width_pt = _length_pt(root.get("width", ""))
    vb = root.get("viewBox")
    vb_w = float(vb.split()[2]) if vb else None
    if width_pt is None:
        width_pt = (vb_w or 0) * 0.75
    # Las fuentes están en unidades del viewBox; si width y viewBox difieren, escalar.
    unit_scale = (width_pt / vb_w) if vb_w else 1.0

    # graphviz con dpi != 72 escala todo con transform="scale(s s)" en el grupo raíz:
    # el ancho del SVG crece pero la letra crece igual, así que hay que aplicarlo.
    for g in root.iter():
        m = re.search(r"scale\(([\d.]+)", g.get("transform") or "")
        if m:
            unit_scale *= float(m.group(1))
            break

    sizes = []
    for el in root.iter():
        fs = el.get("font-size")
        style = el.get("style") or ""
        m = re.search(r"font-size:\s*([\d.]+)", style)
        if m:
            fs = m.group(1)
        if fs:
            try:
                sizes.append(float(re.sub(r"[a-z]+$", "", fs)) * unit_scale)
            except ValueError:
                pass
    return width_pt, (min(sizes) if sizes else 0.0)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("svg", nargs="+")
    ap.add_argument("--width-in", type=float, default=6.5)
    ap.add_argument("--min-pt", type=float, default=7.0)
    a = ap.parse_args()

    target = a.width_in * 72
    failed = False
    for path in a.svg:
        width_pt, min_font = measure(path)
        scale = min(1.0, target / width_pt) if width_pt else 1.0
        effective = min_font * scale
        ok = effective >= a.min_pt
        failed |= not ok
        need = (min_font * target / a.min_pt) if min_font else 0
        print(
            f"{'OK  ' if ok else 'FALLA'} {path}: ancho {width_pt:.0f} pt, letra mínima {min_font:.1f} pt "
            f"→ impresa a {effective:.1f} pt en {a.width_in}\""
            + ("" if ok else f" (para {a.min_pt} pt el diagrama debería medir ≤ {need:.0f} pt de ancho)")
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
