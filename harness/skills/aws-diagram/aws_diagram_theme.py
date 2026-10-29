"""
aws_diagram_theme — tema para diagramas de arquitectura AWS (mingrammer/diagrams).

Instalado por `setup.sh` en el site-packages del venv de la skill `aws-diagram`,
de modo que cualquier script de diagrama pueda hacer simplemente:

    from aws_diagram_theme import diagram, cluster, edge

**Un solo tema, sin branding**: look AWS estándar (Squid Ink + grises), el mismo
que usa el Architecture Icons style guide. Sirve igual para un entregable a
cliente, un ARCHITECTURE.md, un PRD, un README o una pieza interna — un diagrama
sin marca funciona en todos los contextos.
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata

from diagrams import Cluster, Diagram, Edge, Node

__all__ = [
    "step",
    "TONES",
    "tone",
    "row",
    "flow",
    "box",
    "group",
    "render",
    "GRAPH_ATTR",
    "NODE_ATTR",
    "EDGE_ATTR",
    "CLUSTER_ATTR",
    "CAPTION_COLOR",
    "CONFIDENTIAL",
    "diagram",
    "cluster",
    "edge",
    "attrs",
    "slug",
]

# ── Paleta AWS (Architecture Icons style guide) ───────────────────────────────
SQUID_INK = "#232F3E"
AWS_GREY = "#879196"
AWS_LINE = "#5A6B78"
AWS_CLUSTER_BG = "#FAFAFA"
AWS_CLUSTER_LINE = "#B7C0C7"

CAPTION_COLOR = AWS_GREY
CONFIDENTIAL = "DinoCloud Internal - Confidential"

_FONT = "Helvetica"

GRAPH_ATTR = {
    "bgcolor": "transparent",
    "fontname": _FONT,
    "fontsize": "20",
    "fontcolor": SQUID_INK,
    "pad": "0.6",
    # "spline", no "ortho": con ortho graphviz avisa `Orthogonal edges do not
    # currently handle edge labels` y no reserva espacio para los labels de las
    # flechas, que terminan encima de las líneas.
    "splines": "spline",
    "nodesep": "0.7",
    "ranksep": "1.1",
    "labelloc": "t",
    "margin": "0",
}

NODE_ATTR = {
    "fontname": _FONT,
    "fontsize": "12",
    "fontcolor": SQUID_INK,
}

EDGE_ATTR = {
    "color": AWS_LINE,
    "fontname": _FONT,
    "fontsize": "10",
    "fontcolor": AWS_GREY,
    "penwidth": "1.4",
}

CLUSTER_ATTR = {
    "bgcolor": AWS_CLUSTER_BG,
    "pencolor": AWS_CLUSTER_LINE,
    "fontname": _FONT,
    "fontsize": "13",
    "fontcolor": SQUID_INK,
    "style": "rounded,dashed",
    "penwidth": "1.6",
    "margin": "20",
}

# Preset para diagramas que se insertan en documentos (for_doc=True). Un diagrama
# de graphviz mide cientos o miles de pt; en una página Letter vertical entra en
# 468 pt. Con la letra por defecto (10-12 pt) el texto impreso queda en 2-4 pt.
# Este preset sube la letra y compacta rangos y separaciones; aun así, un diagrama
# con muchos rangos puede necesitar dirección TB, partirse o ir en página horizontal.
# ranksep/nodesep dejan lugar a labels más anchos que el ícono (si no, se pisan entre nodos vecinos).
DOC_GRAPH_ATTR = {"fontsize": "28", "nodesep": "0.55", "ranksep": "1.0", "pad": "0.3", "dpi": "220"}
# Íconos más chicos: el ancho del diagrama lo fijan los íconos (1,4" por defecto), no la letra.
DOC_NODE_ATTR = {"fontsize": "22", "width": "0.8", "height": "0.8", "imagepos": "tc"}  # ícono arriba: el label no se le encima
DOC_ICON_HEIGHT = 1.25  # alto de la caja del nodo (ícono + label); diagrams usa 1.9
_DEFAULT_ICON_HEIGHT = Node._height
DOC_EDGE_ATTR = {"fontsize": "19", "penwidth": "2.2", "arrowsize": "1.2"}
DOC_CLUSTER_ATTR = {"fontsize": "22", "margin": "16"}

# diagram(for_doc=True) lo prende para que cluster() y edge() del mismo diagrama
# usen la letra del preset sin tener que pasar for_doc a cada uno.
_doc_mode = False

# Hubo un tema `dino` con branding, que se removió: los diagramas van siempre sin
# marca. Si alguien todavía tiene la env var en el shell o en un Makefile, que se
# entere en vez de preguntarse por qué no pasa nada.
if os.environ.get("DINO_DIAGRAM_THEME"):
    print(
        "aviso: DINO_DIAGRAM_THEME ya no hace nada — la skill aws-diagram tiene un "
        "único tema, sin branding.",
        file=sys.stderr,
    )


def _esc(text: str) -> str:
    """Escapa para labels HTML-like de graphviz."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slug(text: str) -> str:
    """'Kinesis → ECS Relay' → 'kinesis-ecs-relay'. 'Año 2' → 'ano-2'."""
    ascii_text = (
        text.replace("→", " ").replace("—", " ").replace("/", " ").replace("&", " and ")
    )
    # NFKD + drop de los combining marks: sin esto "año" queda "a-o" y el
    # nombre de archivo de cualquier título con acento sale roto.
    ascii_text = "".join(
        ch for ch in unicodedata.normalize("NFKD", ascii_text) if not unicodedata.combining(ch)
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "diagram"


def attrs() -> dict:
    """graph/node/edge/cluster attrs crudos, por si necesitás armar el Diagram a mano."""
    return {
        "graph": dict(GRAPH_ATTR),
        "node": dict(NODE_ATTR),
        "edge": dict(EDGE_ATTR),
        "cluster": dict(CLUSTER_ATTR),
    }


def diagram(
    title: str,
    outdir: str = "docs/diagrams",
    filename: str | None = None,
    direction: str = "LR",
    formats: tuple[str, ...] = ("png", "svg"),
    show: bool = False,
    caption: str | None = None,
    confidential: bool = False,
    graph_attr: dict | None = None,
    for_doc: bool = False,
    show_title: bool = True,
) -> Diagram:
    """
    Devuelve un Diagram ya temado, para usar como context manager.

        with diagram("Ingesta near-real-time") as d:
            ...

    formats: se generan todos en una sola pasada (png para .docx/.pptx, svg para
    web y para el modo Artifact).
    caption / confidential: se muestran como subtítulo debajo del título
    (graphviz sólo soporta un label por grafo).
    for_doc: para diagramas que van dentro de un .docx/.pdf/.pptx. Sube la letra y
    compacta el espaciado para que, una vez escalado al ancho de la página, el texto
    siga legible, y renderiza el PNG a 220 dpi. Después de renderizar, verificar con
    check_legibility.py (ver SKILL.md, Paso 4b).
    """
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, filename or slug(title))

    global _doc_mode
    _doc_mode = for_doc
    Node._height = DOC_ICON_HEIGHT if for_doc else _DEFAULT_ICON_HEIGHT
    g = dict(GRAPH_ATTR)
    node_attr = dict(NODE_ATTR)
    edge_attr = dict(EDGE_ATTR)
    if for_doc:
        g.update(DOC_GRAPH_ATTR)
        node_attr.update(DOC_NODE_ATTR)
        edge_attr.update(DOC_EDGE_ATTR)

    note = caption
    if confidential:
        note = f"{caption} · {CONFIDENTIAL}" if caption else CONFIDENTIAL
    if note:
        # Graphviz admite UN solo label por grafo y `xlabel` a nivel grafo lo
        # ignora, así que título y nota van juntos en un label HTML-like: el
        # título en negrita y la nota debajo, más chica y apagada.
        g["label"] = (
            f"<<B>{_esc(title)}</B>"
            f'<BR/><FONT POINT-SIZE="{16 if for_doc else 11}" COLOR="{CAPTION_COLOR}">{_esc(note)}</FONT>>'
        )

    if not show_title:
        # En un documento el título y la marca van en el pie y en el encabezado de la página:
        # repetirlos dentro de la imagen la achica y duplica información.
        g["label"] = ""

    if graph_attr:
        g.update(graph_attr)

    return Diagram(
        title,
        filename=base,
        outformat=list(formats),
        direction=direction,
        show=show,
        graph_attr=g,
        node_attr=node_attr,
        edge_attr=edge_attr,
    )


def cluster(label: str, graph_attr: dict | None = None, for_doc: bool = False) -> Cluster:
    """Cluster temado — VPC, subnets, cuentas AWS, límites de servicio.
    for_doc=True usa la letra del preset de documentos (igual que en diagram())."""
    a = dict(CLUSTER_ATTR)
    if for_doc or _doc_mode:
        a.update(DOC_CLUSTER_ATTR)
    if graph_attr:
        a.update(graph_attr)
    return Cluster(label, graph_attr=a)


def edge(label: str | None = None, **kwargs) -> Edge:
    """Edge temada.

    Poné siempre un label con el protocolo o el formato del hop: un diagrama sin
    labels en las flechas obliga a adivinar cómo se comunican dos cajas.
    """
    # fontsize incluido a propósito: Edge trae su propio default (13) que pisa
    # al edge_attr del grafo, y el diagrama termina con dos tamaños de label.
    opts = {
        "color": EDGE_ATTR["color"],
        "fontcolor": EDGE_ATTR["fontcolor"],
        "fontname": EDGE_ATTR["fontname"],
        "fontsize": DOC_EDGE_ATTR["fontsize"] if _doc_mode else EDGE_ATTR["fontsize"],
    }
    if _doc_mode:
        opts["penwidth"] = DOC_EDGE_ATTR["penwidth"]
    opts.update(kwargs)
    return Edge(label=label, **opts)


# ── Color por etapa ────────────────────────────────────────────────────────────
# Tonos tomados de los colores de categoría de los íconos de AWS, para que un grupo se
# lea del mismo color que los servicios que contiene. (relleno de caja, borde, fondo de grupo)
TONES = {
    "integracion": ("#FDECF3", "#C7265F", "#FEF6F9"),   # EventBridge, SQS, Step Functions
    "ia": ("#E3F5F1", "#01A88D", "#F2FAF8"),            # Bedrock, Rekognition, Transcribe
    "datos": ("#E8EDFC", "#3B48CC", "#F4F6FE"),         # DynamoDB, catálogo
    "red": ("#F0E9FD", "#8C4FFF", "#F8F4FE"),           # CloudFront, API Gateway, consola
    "computo": ("#FFF0E3", "#ED7100", "#FFF8F1"),       # Lambda, ECS, MediaConvert, salida
    "almacen": ("#E8F4E1", "#3F8624", "#F4FAF0"),       # S3
    "clave": ("#FFF5DB", "#C77700", "#FFFBF0"),         # decisión, validación, lo que importa
    "neutro": ("#F3F5F7", "#5A6B78", "#FAFBFC"),
}


def tone(name: str) -> dict:
    """graph_attr para cluster(): fondo y borde del tono. cluster("Ingesta", graph_attr=tone("integracion"))."""
    _, stroke, bg = TONES[name]
    return {"bgcolor": bg, "pencolor": stroke, "fontcolor": stroke, "style": "rounded,dashed"}


def row(*nodes) -> None:
    """Pone los nodos en la misma fila (TB) o columna (LR). Es la forma de que un flujo
    largo entre en el ancho de la página: en vez de 7 rangos en línea, dos filas de 3-4."""
    from diagrams import getdiagram

    d = getdiagram()
    d.dot.graph_attr["newrank"] = "true"
    with d.dot.subgraph() as s:
        s.attr(rank="same")
        for n in nodes:
            s.node(n._id)


# ── Flujos sin íconos (pasos, estados, decisiones) para documentos ───────────
# Mismo look y paleta que los de arquitectura. Para un README alcanza mermaid; para un
# .docx/.pdf hace falta PNG, y esto lo genera con graphviz sin herramientas extra.
FLOW_GREY = "#6B7B88"


def flow(name: str, title: str, outdir: str = "docs/diagrams", direction: str = "TB",
         caption: str | None = None, confidential: bool = True, show_title: bool = True):
    """Digraph temado para flujos de documento (PNG a 220 dpi y SVG). Usar con box(), group() y render()."""
    import graphviz

    g = graphviz.Digraph(name)
    note = caption
    if confidential:
        note = f"{caption} · {CONFIDENTIAL}" if caption else CONFIDENTIAL
    label = f"<<B>{_esc(title)}</B>"
    if note:
        label += f'<BR/><FONT POINT-SIZE="15" COLOR="{FLOW_GREY}">{_esc(note)}</FONT>'
    g.attr(rankdir=direction, bgcolor="white", fontname=_FONT, fontcolor=SQUID_INK, fontsize="26",
           labelloc="t", pad="0.3", nodesep="0.35", ranksep="0.55", splines="spline", dpi="220",
           newrank="true", label=(label + ">") if show_title else "")
    fill, stroke, _ = TONES["neutro"]
    g.attr("node", shape="box", style="rounded,filled", fillcolor=fill, color=stroke, penwidth="2",
           fontname=_FONT, fontsize="20", fontcolor=SQUID_INK, margin="0.18,0.10")
    g.attr("edge", color=AWS_LINE, penwidth="1.8", arrowsize="1.0", fontname=_FONT, fontsize="17",
           fontcolor=FLOW_GREY)
    g._outdir = outdir
    return g


def box(g, nid: str, title: str, detail: str | None = None, tone: str = "neutro", dashed: bool = False) -> None:
    """Caja con título en negrita y detalle gris. detail admite <BR/> para cortar líneas:
    cortalas a ~35 caracteres, que el ancho de la caja es lo que define el ancho del diagrama."""
    fill, stroke, _ = TONES[tone]
    body = f"<B>{_esc(title)}</B>"
    if detail:
        body += f'<BR/><FONT POINT-SIZE="16" COLOR="{FLOW_GREY}">{detail}</FONT>'
    g.node(nid, f"<{body}>", fillcolor=fill, color=stroke,
           style="rounded,filled,dashed" if dashed else "rounded,filled")


def group(g, key: str, label: str, tone: str = "neutro", same_rank: bool = False):
    """Grupo con el color del tono. with group(g, "t1", "Tramo 1", "ia", same_rank=True) as c: box(c, ...)"""
    _, stroke, bg = TONES[tone]
    c = g.subgraph(name=f"cluster_{key}")
    sub = c.__enter__()
    sub.attr(label=f'<<B><FONT COLOR="{stroke}">{_esc(label)}</FONT></B>>', style="rounded,dashed",
             color=stroke, bgcolor=bg, fontname=_FONT, fontsize="19", margin="14", penwidth="1.4")
    if same_rank:
        sub.attr(rank="same")

    class _Ctx:
        def __enter__(self):
            return sub

        def __exit__(self, *exc):
            return c.__exit__(*exc)

    return _Ctx()


def render(g) -> str:
    """Escribe <outdir>/<name>.png y .svg."""
    out = os.path.join(g._outdir, g.name)
    os.makedirs(g._outdir, exist_ok=True)
    for fmt in ("png", "svg"):
        g.render(out, format=fmt, cleanup=True)
    return out


def step(n: int, text: str = "") -> str:
    """Label de flecha con un marcador de paso (cuadro oscuro con el número) y, opcional, el texto.
    Los pasos se listan debajo de la figura con el mismo número, como en las Guidance de AWS:
    edge(step(1, "objeto nuevo")). No usar los mismos números que las etapas de un flujo."""
    badge = (f'<TD BGCOLOR="{SQUID_INK}" STYLE="rounded" CELLPADDING="3">'
             f'<FONT COLOR="white"><B> {n} </B></FONT></TD>')
    cell = f"<TD>{_esc(text)}</TD>" if text else ""
    return f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="4"><TR>{badge}{cell}</TR></TABLE>>'
