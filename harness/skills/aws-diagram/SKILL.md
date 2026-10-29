---
name: aws-diagram
description: >
  Genera diagramas de arquitectura AWS con los íconos oficiales, como código
  versionable (mingrammer/diagrams + graphviz), y los diagramas de flujo del mismo
  diseño (pasos, máquinas de estados, decisiones) con el mismo look y color por
  etapa. Salida PNG y SVG para docs y entregables, o un Artifact HTML para
  compartir por link. Usar siempre que el
  usuario mencione: diagrama de arquitectura, architecture diagram, "dibujá la
  arquitectura", diagrama AWS, diagrama de infra, VPC diagram, diagrama de red,
  diagrama de flujo de datos, ARCHITECTURE.md, "cómo se conecta esto", o pida
  ilustrar una solución AWS para un SOW, PRD, README, runbook o presentación.
  También triggear cuando haya que documentar visualmente un repo con Terraform,
  CDK, CloudFormation o SAM.
---

# aws-diagram — diagramas de arquitectura AWS como código

Produce diagramas con el set oficial de íconos de AWS. El diagrama es un `.py`
que se commitea junto al PNG: se regenera, se diffea y se revisa en un PR como
cualquier otro código. Nada de arrastrar cajas en draw.io y perder el fuente.

**Un solo look**, sin branding: estilo AWS estándar (Squid Ink + grises) con
**color por etapa** tomado de las categorías de los íconos AWS. Un diagrama sin
marca sirve para un entregable a cliente, un `ARCHITECTURE.md`, un PRD y una pieza
interna por igual; uno con marca no.
**Dos tipos de diagrama, el mismo look:**
- **Topología con íconos** (`diagram`, `cluster`, `edge`): qué servicio habla con cuál.
- **Flujos para documentos** (`flow`, `box`, `group`, `render`): pasos, tramos de una
  máquina de estados, decisiones, reglas. Sin íconos, graphviz puro, PNG para `.docx`.

Un documento de diseño mezcla los dos y tienen que leerse como un set: mismos
tonos, misma letra, mismo pie de confidencialidad.
**Dos salidas.** Archivos PNG/SVG, o un Artifact HTML para compartir por link.

## Cuándo NO usar esta skill

- **Un flujo dentro de un README o un Artifact** → mermaid: se edita en el mismo
  archivo y GitHub lo renderiza. `flow()` es para cuando hace falta PNG (`.docx`,
  `.pdf`, `.pptx`) o tiene que combinar con diagramas de íconos.
- **Secuencia de mensajes entre actores o gantt** → mermaid (`sequenceDiagram`, `gantt`).
- **Arquitecturas que no son AWS.** El paquete tiene nodos de GCP y Azure, pero el
  catálogo, los templates y la paleta de esta skill son AWS.
- **Tres cajas dentro de un Artifact o un README.** No vale levantar graphviz y un
  venv para eso: un bloque mermaid alcanza y se edita en el mismo archivo.

---

## Paso 0 — Verificar el entorno

```bash
bash ~/.claude/skills/aws-diagram/setup.sh --check
```

Si falta algo, corré `bash ~/.claude/skills/aws-diagram/setup.sh` (instala
graphviz, crea el venv en `~/.dino/aws-diagram/.venv`, instala `diagrams` desde
PyPI en una versión pineada y genera el catálogo de nodos). Es idempotente, y
`--check` valida las cinco piezas: graphviz, venv, `diagrams`, el theme
importable y el catálogo.

Si la skill está instalada en el proyecto y no globalmente, el script está en
`.claude/skills/aws-diagram/setup.sh` — ajustá el path en este paso y en el 6.

De acá en adelante, **todo script de diagrama se corre con ese python**:

```bash
PY=~/.dino/aws-diagram/.venv/bin/python            # macOS / Linux
PY=~/.dino/aws-diagram/.venv/Scripts/python.exe    # Windows (Git Bash)
```

En Windows, `setup.sh` instala graphviz con `winget` en `C:\Program Files\Graphviz\bin`.
Si `dot` no está en el PATH de la sesión, anteponelo:
`export PATH="/c/Program Files/Graphviz/bin:$PATH"`. Los paths que recibe `$PY`
van en formato Windows (`cygpath -w`), igual que `OUTDIR`.

Nunca con `python3` del sistema ni con el venv del proyecto: `diagrams` sólo está
instalado en el venv de la skill, a propósito, para no meter una dependencia de
documentación en el `requirements.txt` de nadie.

---

## Paso 1 — Entender la arquitectura de verdad

**No dibujes lo que suponés.** Antes de escribir una línea, leé la fuente real:

| Si el repo tiene | Leé |
|---|---|
| Terraform | `*.tf` — recursos, `depends_on`, security groups, subnets |
| CDK / SAM / CloudFormation | el stack y sus constructs |
| Docker Compose | servicios, redes, volúmenes |
| Sólo código | el entrypoint, los clientes AWS SDK que instancia, y las env vars |

Si después de leer siguen quedando huecos (¿va por VPC endpoint o por internet?
¿el consumer es EFO o polling?), **preguntá**. Un diagrama con un hop inventado
es peor que no tener diagrama: se copia a un SOW y nadie lo vuelve a chequear.

---

## Paso 2 — Resolver los imports contra el catálogo

**Esta es la regla que más importa.** `diagrams` tiene ~562 nodos AWS y los
nombres no son adivinables: es `Dynamodb` (no `DynamoDB`), `Appsync` existe en
`diagrams.aws.integration` **y** en `diagrams.aws.mobile`, Amazon Connect es
`diagrams.aws.engagement.Connect`, y varios servicios nuevos directamente no
están. Un import inventado explota recién al renderizar.

`setup.sh` genera el catálogo real desde el paquete instalado. Consultalo:

```bash
grep -i kinesis  ~/.dino/aws-diagram/aws-nodes.txt
grep -i 'aws.ml' ~/.dino/aws-diagram/aws-nodes.txt
```

Cada línea es un import válido. **Prohibido escribir un `from diagrams.aws...`
sin haberlo visto en el catálogo.**

Nodos que no son AWS (usuarios, browser, on-prem, colas genéricas) salen de
`diagrams.onprem.*`, `diagrams.generic.*` y `diagrams.programming.*`:

```bash
$PY -c "import diagrams.onprem.client as m; print([n for n in dir(m) if n[0].isupper()])"
```

Si un servicio no existe en el paquete (típico con lanzamientos recientes),
usá un nodo `Custom` con el ícono oficial:

```python
from diagrams.custom import Custom
nodo = Custom("Servicio nuevo", "./icons/servicio.png")
```

El PNG hay que bajarlo a mano del [asset pack oficial de AWS](https://aws.amazon.com/architecture/icons/)
— no lo automatices, el egress está restringido por allowlist.

---

## Paso 3 — Escribir el script

Va en `docs/diagrams/<nombre>.py` del repo que se está documentando (el fuente
se commitea junto al PNG). Estructura:

```python
#!/usr/bin/env python
"""Ingesta near-real-time. Correr con ~/.dino/aws-diagram/.venv/bin/python."""

import os

from diagrams.aws.analytics import KinesisDataStreams
from diagrams.aws.compute import Fargate

from aws_diagram_theme import cluster, diagram, edge

OUTDIR = os.environ.get("OUTDIR", "docs/diagrams")

with diagram("Ingesta near-real-time", outdir=OUTDIR, direction="LR"):
    stream = KinesisDataStreams("Kinesis Data Streams")

    with cluster("ECS Fargate"):
        relay = Fargate("Relay")

    stream >> edge("EFO · SubscribeToShard") >> relay
```

### API de `aws_diagram_theme`

| Función | Para qué |
|---|---|
| `diagram(title, outdir="docs/diagrams", filename=None, direction="LR", formats=("png","svg"), caption=None, confidential=False, graph_attr=None, for_doc=False)` | context manager del diagrama, ya temado; `for_doc=True` para documentos (Paso 4b) |
| `cluster(label, graph_attr=None)` | agrupador — VPC, subnet, cuenta AWS, límite de servicio |
| `edge(label, **kwargs)` | flecha con label; acepta `style="dashed"` / `"dotted"` |
| `step(n, texto)` | label de flecha con el número de paso en un recuadro oscuro: `edge(step(1, "objeto nuevo"))`; debajo de la figura va la lista con los mismos números |
| `diagram(..., show_title=False)` / `flow(..., show_title=False)` | sin título ni nota dentro de la imagen: en un documento van en el pie y en la página |
| `tone(nombre)` | `graph_attr` de un `cluster` con el color de su etapa: `cluster("Ingesta", graph_attr=tone("integracion"))` |
| `row(*nodos)` | pone nodos en la misma fila (TB) o columna (LR); es lo que hace entrar un flujo largo en la página |
| `flow(name, title, outdir, direction="TB", caption=None, confidential=True)` | diagrama de flujo sin íconos, mismo look; PNG a 220 dpi |
| `box(g, id, título, detalle=None, tone="neutro", dashed=False)` | caja de un flujo; `detalle` admite `<BR/>` |
| `group(g, key, label, tone, same_rank=False)` | grupo coloreado de un flujo (`with group(...) as c: box(c, ...)`) |
| `render(g)` | escribe el `.png` y el `.svg` del flujo |

**Tonos** (`TONES`), por la categoría de los servicios que contiene el grupo:
`integracion` (EventBridge, SQS, Step Functions), `ia` (Bedrock, Rekognition,
Transcribe), `datos` (DynamoDB, catálogo), `red` (CloudFront, API Gateway, consola),
`computo` (Lambda, ECS, MediaConvert), `almacen` (S3), `clave` (la decisión o
validación que importa, en ámbar) y `neutro`. Un color por etapa, no por nodo: si
todo es de colores, nada se destaca.

```python
from aws_diagram_theme import box, flow, group, render

g = flow("maquina-analisis", "Orquestación del análisis", outdir=OUTDIR, caption="Step Functions")
box(g, "ing", "Máquina de ingesta", "la dispara un master nuevo", tone="integracion")
with group(g, "t1", "Tramo 1 · en paralelo", "ia", same_rank=True) as c:
    box(c, "tr", "Transcripción", "Transcribe · audio del proxy", tone="ia")
    box(c, "pl", "Detección de planos", "Rekognition · proxy", tone="ia")
box(g, "val", "Validación de planos", "si no es coherente, corta", tone="clave")
g.edge("ing", "tr", label="  inicia")
g.edge("ing", "pl")
g.edge("pl", "val")
render(g)
```

`caption` y `confidential=True` se muestran como subtítulo debajo del título
(graphviz sólo admite un label por grafo). No hay parámetro `theme`: el módulo
tiene un único look. La env var `DINO_DIAGRAM_THEME` quedó sin efecto y avisa
por stderr si está seteada.

Hay tres templates listos para copiar y adaptar en `templates/`:
`serverless-api.py`, `vpc-3tier.py`, `streaming-relay.py`.

---

## Paso 4 — Renderizar

```bash
$PY docs/diagrams/mi-arquitectura.py
```

Genera `.png` (para `.docx`, `.pptx` y GitHub) y `.svg` (para web y modo
Artifact) en una sola pasada. **Miralo antes de entregarlo** — abrí el PNG y
verificá que no haya flechas cruzadas ni labels encimados. Si quedó feo, el
arreglo casi siempre es `direction="TB"`, menos nodos, o un `cluster` de más.

El fondo sale transparente, así que el PNG se adapta a cualquier página clara.
Sobre una slide **oscura** el texto es Squid Ink y queda ilegible: para esos
casos, `graph_attr={"bgcolor": "white"}`.

Al repo van el `.py`, el `.png` y el `.svg`. El `.inline.svg` del Paso 6 **no**
se commitea: es el mismo diagrama con los íconos en base64, cientos de KB de
blob que no se diffean.

---

## Paso 4b — Legibilidad en documentos (obligatorio si va a un .docx, .pdf o .pptx)

Un diagrama se escala para entrar en el ancho útil de la página. **Lo que importa es
la letra impresa, no los dpi**: un diagrama de 2000 pt de ancho en una página Letter
vertical (468 pt útiles) queda al 23 %, y un label de 11 pt se imprime a 2,5 pt aunque
el PNG tenga 300 dpi.

1. Si el diagrama va a un documento, usá `diagram(..., for_doc=True)`. Sube la letra,
   compacta el espaciado y renderiza el PNG a 220 dpi. `cluster()` y `edge()` toman el
   modo solos.
2. Verificá contra el ancho útil real de la página:

   ```bash
   $PY ~/.dino/aws-diagram/check_legibility.py docs/diagrams/x.svg --width-in 6.5
   ```

   `--width-in`: 6.5 para Letter vertical con márgenes de 1", 9 para Letter horizontal,
   6.3 para A4 vertical. Sirve también para SVG escritos a mano. Exige ≥ 7 pt impresos.
3. Si falla, en este orden:
   - **menos rangos**: sacá nodos que no hacen al punto del diagrama (lo transversal,
     como KMS o CloudWatch, suele ir en otro diagrama);
   - **`direction="TB"`** si el flujo es largo y angosto;
   - **partilo en dos** (contexto + detalle);
   - **página horizontal** para esa figura en el documento.
4. Volvé a correr el chequeo y mirá el PNG insertado en la página (render a PDF), no
   suelto.

Nunca entregues un diagrama para documento sin este chequeo en verde.

---

## Paso 5 — Chequeo de contenido (obligatorio antes de entregar)

Un diagrama se pega en decks y se manda por mail; una vez afuera no se corrige.
Antes de entregarlo, pasale el grep al fuente y al SVG:

```bash
grep -nwE '[0-9]{12}|arn:aws:|AKIA[0-9A-Z]{16}|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
  docs/diagrams/mi-arquitectura.py docs/diagrams/mi-arquitectura.svg
```

Busca account IDs, ARNs, access keys e IPs/CIDRs. El `-w` no es opcional: los node
IDs hex de 32 caracteres que genera `diagrams` contienen 12 dígitos seguidos, y sin
word boundary el chequeo da falsos positivos en todo SVG. Va a marcar los rangos de
ejemplo (`10.0.0.0/16`): revisá cada hit y confirmá que es de ejemplo. Después, las
tres preguntas de cierre:

1. ¿Aparece el nombre del cliente o alguna de sus marcas? → sacalo, salvo
   autorización escrita con alcance confirmado.
2. ¿Hay algún recurso real (bucket, endpoint, cluster, cuenta)? → reemplazalo por
   un nombre por rol.
3. ¿Es una arquitectura interna? → `confidential=True`.

Ver **Reglas de contenido** más abajo para el detalle de la política.

---

## Paso 6 — Modo Artifact (sólo si se comparte por link)

Cuando el diagrama es para que alguien lo abra en el navegador y no un archivo
para un doc, publicalo como Artifact:

```bash
$PY ~/.dino/aws-diagram/embed_svg_assets.py docs/diagrams/x.svg --for-html --stdout
```

El SVG de graphviz referencia los íconos por **path absoluto del disco**, así
que sin este paso el Artifact se ve vacío. El script los reemplaza por data URIs
y deja un SVG autocontenido.

Después: tomá `templates/artifact-shell.html`, reemplazá `{{TITLE}}`,
`{{SUBTITLE}}`, `{{SVG}}`, `{{LEGEND}}` y `{{FOOTER}}` — escapando `&`, `<` y `>`
en los tres primeros — y publicalo con la herramienta Artifact. El lienzo del diagrama queda claro en light y en dark a propósito: el
SVG trae los colores del texto horneados y sobre fondo oscuro sería ilegible.

---

## Reglas de layout

- **`direction="LR"`** por defecto: el flujo de datos se lee de izquierda a
  derecha. `"TB"` para jerarquías (organizaciones, cuentas, capas).
- **Un `cluster` por límite real**: VPC, subnet, cuenta AWS, región. No agrupes
  por gusto estético — un recuadro afirma que hay un borde.
- **Toda flecha lleva label** con el protocolo o el formato: `HTTPS 443`,
  `PutRecord`, `s3:ObjectCreated`. Una flecha pelada obliga a adivinar.
- **`style="dashed"`** para replicación/async, **`style="dotted"`** para
  telemetría y flujos secundarios.
- **No fuerces `splines="ortho"`.** Las flechas en ángulo recto quedan lindas,
  pero graphviz no reserva espacio para los labels cuando están activadas
  (`Warning: Orthogonal edges do not currently handle edge labels`) y los labels
  terminan encima de las líneas. El default de los dos temas es `"spline"`. Si un
  diagrama no tiene ningún label en las flechas, podés pedirlo:
  `diagram("X", graph_attr={"splines": "ortho"})`.
- **Máximo ~15 nodos.** Si no entra, partilo en dos: uno de contexto (el sistema
  y sus vecinos) y uno de detalle (el interior de un componente).
- **Para documentos, filas antes que una línea.** Un flujo de 7 servicios en `LR`
  mide ~4.000 pt y se imprime a 5 pt; en `TB` es una columna de 17" de alto. Lo que
  entra es `TB` con `row()` armando filas de 3 o 4 nodos. Probá también ordenar los
  nodos de una fila en el orden en que los declarás: graphviz respeta ese orden.
- **Fondo blanco y `pad` 0.7 en documentos** (`graph_attr={"bgcolor": "white",
  "pad": "0.7"}`): el fondo transparente se ve negro en algunos visores y sin pad
  el label del primer nodo se corta.
- **Alto máximo ≈ 8,2" al ancho de la página.** Si la relación alto/ancho pasa de
  ~1,3, el diagrama se achica por alto y la letra baja de 7 pt: repartí en filas.
- **Un diagrama de ejemplo no lleva nombres reales** del material del cliente
  (personajes, títulos): usá genéricos.
- **En un documento, sin título ni "Confidential" dentro de la imagen** (`show_title=False`):
  el pie de la figura y el documento ya los llevan.
- **Pasos numerados con `step()`** en los diagramas de arquitectura que muestran un
  recorrido (ingesta, consola, despliegue). No uses los mismos números que las etapas
  de un flujo de alto nivel.
- **Flujos: en la caja solo el título**, con el servicio entre paréntesis si hace
  falta ("Detección de planos (Rekognition)"); lo que pasa de un paso al otro va en
  la flecha. Nada de texto gris dentro de las cajas.
- **Sin "·" como separador** en labels: paréntesis, comas o "y" ("Bedrock (Pegasus y Claude)").
- **Nombrá por rol, no por recurso**: "Relay passthrough" dice más que
  `ecs-svc-prod-01`.

---

## Reglas de contenido — política DinoCloud

Un diagrama se pega en decks, se manda por mail y sobrevive al proyecto. Nunca
incluyas:

- **Nombre del cliente** ni sus marcas, salvo autorización escrita y con el
  alcance confirmado.
- **Account IDs, ARNs con cuenta, IPs o CIDRs reales, endpoints internos,
  nombres de bucket productivos.** Usá valores de ejemplo (`10.0.0.0/16`).
- **Credenciales de cualquier tipo.** Nunca, en ningún caso.

Para arquitecturas internas: anonimizá y pasá `confidential=True`, que estampa
`DinoCloud Internal - Confidential`. Si el diagrama es para un cliente, confirmá
antes el destinatario y el alcance autorizado.

El diagrama en sí nunca lleva branding — no hay tema con marca. Si va dentro de
una pieza branded (`.pptx`, `.docx`, SOW), la marca la aporta el documento que lo
contiene, no el diagrama; ver skill `dino-brand`.

---

## Troubleshooting

| Síntoma | Causa |
|---|---|
| `ImportError` de un nodo | El nombre no existe — verificalo en `aws-nodes.txt` (Paso 2) |
| `ExecutableNotFound: dot` | Falta graphviz → `bash setup.sh`; en Windows, sumar `/c/Program Files/Graphviz/bin` al PATH |
| `ModuleNotFoundError: aws_diagram_theme` | Estás usando otro python; usá el del venv de la skill |
| El Artifact muestra el diagrama vacío | Te salteaste `embed_svg_assets.py` (Paso 6) |
| `Warning: Orthogonal edges do not currently handle edge labels` | Estás forzando `splines="ortho"` en un diagrama con labels — volvé al default `"spline"` |
| Labels encimados o flechas cruzadas | Demasiados nodos, dirección equivocada o `ortho` forzado — ver Reglas de layout |

---

## Red flags — si pensás esto, pará

| Lo que estás pensando | La realidad |
|---|---|
| "Me acuerdo cómo se llama el nodo" | No son adivinables: `Dynamodb` ≠ `DynamoDB`, y varios servicios no existen. Grepeá `aws-nodes.txt` (Paso 2). |
| "Le subo los dpi y se va a leer" | Los dpi no agrandan la letra: el diagrama se escala al ancho de la página. Corré `check_legibility.py` (Paso 4b). |
| "El PNG seguro salió bien" | Abrilo. Los labels encimados sólo se ven mirando, y el diagrama se copia a un SOW sin que nadie lo vuelva a chequear. |
| "Es un diagrama interno, no hace falta anonimizar" | Los diagramas sobreviven al proyecto y migran a decks. Anonimizá y `confidential=True` (Paso 5). |
| "Uso el python del proyecto y listo" | `diagrams` no está ahí a propósito. Usá el venv de la skill. |
| "El cliente pidió su logo, lo pongo" | Hace falta autorización escrita y alcance confirmado. Preguntá primero. |
| "Este hop debe ir por VPC endpoint" | Si es "debe", no lo sabés. Leé el Terraform o preguntá — un hop inventado es peor que no tener diagrama. |
