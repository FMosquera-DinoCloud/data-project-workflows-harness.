---
name: solution-design
description: Redacta o actualiza el documento de Diseño de Solución de un proyecto (contrato de diseño que valida el cliente) en .docx con marca DinoCloud, diagramas AWS y de flujo legibles, y solo datos verificados. Usar cuando se pida armar, actualizar, revisar o cerrar el diseño de la solución, el documento de arquitectura, el SDD, o subir una nueva versión del diseño.
---

# solution-design

El Diseño de Solución es un **contrato de lo que se va a implementar** que valida el cliente. Dice qué se construye, con qué servicios de AWS y con qué decisiones. **No** es la implementación: el detalle de cada componente lo resuelve cada responsable en el repo y en sus tareas.

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`.

## Principios (no negociables)

1. **Conciso y al grano.** Solo lo que el cliente necesita para validar el diseño. Si una frase no cambia una decisión del cliente, no va. Para ampliar, se citan los documentos que armó el equipo (Benchmark Design, contrato OpenAPI, propuestas); no se copia su contenido.
2. **Sin información interna.** Nada de historial de cambios, estado de tareas, ids internos (T-, D-, ClickUp), nombres de archivos locales, horas ni capacidad del equipo. Las versiones se guardan en el repo y en Drive, no en una sección del documento.
3. **Lo que falta definir dice "A definir" en su sección**, en un párrafo corto con el responsable (por rol). Al final del documento va un resumen: tabla Qué falta definir / Sección / Responsable, con los mismos ítems (el generador los junta solo). Por cada "A definir" nuevo, proponer la tarea (con `task-writer` / `backlog`) y pedir OK antes de crearla en ClickUp.
4. **Viable en el proyecto.** Antes de escribir, leer el overview, el alcance confirmado y la asignación del equipo (`team-allocation`). Nada que no entre en el tiempo y la capacidad que quedan. Sin sobreingeniería: el componente más simple que cumple el requisito del cliente. Lo que excede el alcance va a "Fuera de alcance" en una línea.
5. **Solo datos verificados.** Costos, tiempos y cifras con fuente: medidos por el equipo, informados por el cliente o de documentación oficial consultada. Nada estimado de memoria ni resultados de simulaciones presentados como pruebas. Si falta el dato: "se mide en …" o "a cuantificar con la calculadora de AWS".
6. **Publicar requiere OK.** Generar el archivo local es libre; subirlo a Drive, reemplazar una versión o comentar en ClickUp, solo con aprobación explícita del usuario.
7. **Productivo separado de lo temporal.** Contexto, arquitectura y red muestran solo lo que queda en producción: un único modelo de inferencia (el que elija el benchmark, como nodo genérico "Modelo elegido"), solo las fuentes de producción. Lo que se usa solo durante el proyecto (muestras, servicio de referencia, candidatos del benchmark) va en su propia sección, con sus fuentes de datos, y dice que no forma parte de lo que se entrega.
8. **A la par con el Scope Confirmation.** Cada cambio en el diseño se cruza en la misma pasada con el Scope Confirmation del proyecto (y viceversa). Cada documento en su alcance: el Scope Confirmation es el contrato con el cliente (contra el SOW, qué se hace y qué queda fuera de alcance, sin detalle técnico); el diseño es el documento técnico (cómo se construye). Un cambio técnico solo toca el Scope si cambia qué se entrega o qué queda fuera. No se duplica contenido; se lista la diferencia y se propone el cambio en el otro documento (con OK para editarlo).
9. **Contrastado contra el SOW, el PRD y los Change Requests.** Antes de cerrar una versión, cruzar el diseño con el SOW, el PRD y los Change Requests vigentes (los que existan), para que no quede nada afuera. **Jerarquía:** el SOW es la base; el PRD y los CR posteriores son la última palabra y lo pisan, porque lo del SOW puede haber quedado fuera de alcance o modificado. Entre un PRD y un CR, el más reciente prevalece. Armar la matriz requisito / fuente (SOW, PRD o CR) / dónde lo cubre el diseño o por qué no aplica, y clasificar cada ítem: cubierto, falta (se agrega o va como "A definir" con tarea propuesta), sobra (no está en ninguna fuente vigente, se saca o se justifica) o contradice (gana la fuente más nueva; se registra el motivo). Un ítem del SOW que el PRD o un CR sacó o cambió no se diseña como estaba. Si el SOW y el PRD chocan en algo que no queda claro, no se resuelve a criterio propio: se pregunta al usuario. La matriz es de trabajo, no va en el documento del cliente.

## Estructura

| # | Sección | Contenido |
|---|---|---|
| — | Portada | Título, proyecto, "Confidential", tabla: preparado por, fecha, versión, audiencia |
| — | Índice | Automático (campo TOC de Word, niveles 1 y 2), actualizado con Word antes de publicar |
| 1 | Propósito y alcance | Qué define el documento; qué se construye (bullets); fuera de alcance (bullets); vocabulario con los términos del dominio y las siglas (EDL, HLS, DLQ…) |
| 2 | Principios de diseño | Las prioridades del cliente, en su orden |
| 3 | Contexto y puntos de contacto | Diagrama de contexto + tabla de puntos de contacto con dirección (lectura/escritura) |
| 4 | Arquitectura | Diagrama de alto nivel, leyenda de colores y líneas (una sola vez) y tabla Componente / Servicio AWS / Responsabilidad; una subsección por capa con su diagrama y sus pasos numerados |
| 5+ | Una sección por pieza que el cliente valida | Interfaz/API, formato de salida, componentes clave del dominio. Cada una corta, con referencia al documento del equipo |
| — | Benchmark / pruebas (si hay) | Sección propia: fuentes de datos, candidatos, regla de selección. Fuera de los diagramas productivos |
| n-3 | Infraestructura y seguridad | Diagrama de cuentas y despliegue (o de red) y tabla Aspecto / Definición; el riesgo aceptado va como fila |
| n-2 | Decisiones de diseño | Tabla Decisión / Alternativa descartada / Motivo, de 8 a 12 filas. Es lo que más consulta quien implementa |
| n-1 | Costos | Tabla por línea, con su fuente |
| n | Resumen de pendientes y supuestos | Tabla de lo que falta definir (con sección y responsable) y tabla Supuesto / Si no se cumple |
| — | Referencias | Tabla Documento (con link) / Qué contiene / Dónde (Drive, ClickUp, GitHub) |

Adaptar las secciones 5+ al proyecto; no agregar secciones por completitud.

## Gráficos

Una idea por figura y una figura por capa del diseño: cuentas o contexto, flujo de alto nivel, una por capa del runtime y los flujos que el cliente valida (estados, reglas, búsqueda). Los flujos internos de implementación (lo que pasa dentro de un worker, task tokens, reintentos) no van. Todo sale de la skill `aws-diagram`, que da el mismo look y el color por etapa a los dos tipos.

**Arquitectura con íconos** (`diagram(..., for_doc=True, show_title=False)`):
- Pasos numerados en las flechas con `edge(step(n, "verbo"))` y, debajo de la figura, la lista numerada con una oración por paso que nombra el servicio. Es el formato de las arquitecturas de referencia de AWS.
- Filas con `row()` para que un flujo largo entre en el ancho: `TB` con filas de 3 o 4 nodos. Agrupar en un nodo lo que la tabla ya detalla.
- Clusters con `tone()` por categoría de servicio. Línea sólida para datos; rayada para lecturas entre cuentas, pasos opcionales o caminos alternativos.
- El modelo va entre paréntesis debajo del servicio: "Bedrock (Claude Haiku)". Nada de "·" como separador.

**Flujos** (`flow()`, `box()`, `group()` y `render()` de `aws-diagram`, sin íconos): la caja lleva solo el título, con el servicio entre paréntesis si hace falta ("Detección de planos (Rekognition)"). Lo que pasa de un paso al siguiente va en la flecha. Nada de texto gris dentro de las cajas. Un solo color de acento (`clave`, ámbar) para la regla o la validación que decide.

**Sin título ni marca dentro de la imagen.** El título va en el pie y "Confidential" en el documento: repetirlos achica el diagrama.

**Cómo se presenta cada figura en el documento:**
1. Antes, una oración que dice para qué está, con `keepNext` para que no quede sola al pie de la página.
2. El pie: "Figura N." y una oración con la conclusión que deja la figura, no su título.
3. Después, solo lo que el diagrama no muestra: los pasos numerados (si tiene), el porqué y las restricciones. **No** un párrafo que describa lo que se ve: repite la imagen.

**Legibilidad y página:** `check_legibility.py --width-in 6.5` en verde y un alto máximo de unos 6,3": más alto, la figura salta de página y deja medias páginas en blanco. Mirar cada página con figura en el PDF de revisión.

## Texto

- Voz activa, frases cortas, una idea por bullet. Bullets con un comienzo en negrita ("**Reproceso.** …").
- Tablas en lugar de prosa cuando hay más de tres ítems paralelos (componentes, salidas, aspectos, decisiones).
- **Servicios de AWS resaltados** con un color propio (en el generador, una lista de servicios que se colorea sola en texto y tablas). El modelo va entre paréntesis: "Bedrock (Pegasus 1.2)".
- **Sin "·" como separador**, ni en tablas ni en diagramas: comas, "y" o paréntesis.
- Términos unificados en todo el documento (por ejemplo "episodio" y no "capítulo" y "episodio"; "archivo de recorte (EDL)" la primera vez y "EDL" después).
- Al final de cada sección, una línea **"Para profundizar:"** con los links al documento fuente o a la tarea donde está el detalle.

## Generación

Implementaciones de referencia:
- `~/dino-projects/mediablocks/docs/architecture/scripts/build_diseno_v1.py` (python-docx): parte del .docx de la versión anterior para heredar estilos, encabezado y pie; helpers `figure()`, `steps()`, `pending()`, `table()`, `deeper()`, índice y resaltado de servicios. `update_toc.ps1` actualiza el índice con Word y exporta el PDF de revisión.
- `~/dino-projects/truefire/docs/architecture/` (`build-docx.js`, docx-js).

1. **Formato:** si el proyecto ya tiene un documento cuyo formato usa el equipo (letra, interlineado, títulos, tablas), replicarlo: leer sus `pPr` y `rPr` y copiar los valores. Si no, skill `dino-brand`. Instalar las fuentes antes de renderizar: si faltan, Word las reemplaza sin avisar.
2. **Diagramas:** Graphviz en el PATH (`C:\Program Files\Graphviz\bin`) y el python del venv `~/.dino/aws-diagram/.venv`. Verificar con `check_legibility.py --width-in 6.5` y mirar el PNG: el checker no detecta etiquetas encimadas ni flechas que cruzan clusters.
3. **Documento:** las medidas reales de cada PNG en `figure()`. **El entregable es solo el .docx.** Para la revisión visual, actualizar el índice y convertir a PDF con Word por COM en el scratchpad, renderizar las páginas y mirarlas todas; ese PDF no se versiona ni se sube.
4. **Pie de página:** si se cambia su texto, tocar solo los `w:t`: asignar `run.text` borra los campos de número de página.
5. **Versionado:** commit en el repo del proyecto. En Drive, antes de reemplazar, comparar la copia con la última publicada (un diff del texto) para detectar ediciones humanas y avisar si las hay. Reemplazar el .docx por Drive desktop conserva el ID; un Google Doc (`.gdoc`) no se puede pisar con un .docx (archivo nuevo, con OK).

## Checklist antes de entregar

- [ ] Ninguna sección de historial, estado interno, ids ni archivos locales.
- [ ] Cada "A definir" está en su sección, figura en el resumen final y tiene tarea propuesta en el backlog.
- [ ] Cada figura tiene oración de entrada, pie con conclusión y, si es de arquitectura, pasos numerados; ningún párrafo que describa la imagen.
- [ ] Sin título ni "Confidential" dentro de las imágenes; sin "·" en texto, tablas ni diagramas.
- [ ] Índice actualizado; cada sección con su "Para profundizar" y todas las fuentes en Referencias, con link.
- [ ] Sin medias páginas en blanco por figuras que saltan de página.
- [ ] Cada cifra tiene fuente; ninguna es estimación propia ni simulación.
- [ ] Nada fuera del alcance confirmado ni de la capacidad del proyecto.
- [ ] Todos los diagramas pasan `check_legibility.py` y se revisaron en la página renderizada.
- [ ] Diagramas productivos sin nada del benchmark ni de pruebas; un solo modelo de inferencia.
- [ ] Ningún flujo de implementación entre las figuras; tabla de decisiones con sus alternativas.
- [ ] Cruzado con el Scope Confirmation; diferencias propuestas en el otro documento.
- [ ] Contrastado con el SOW, el PRD y los CR vigentes (PRD/CR sobre SOW): sin requisitos faltantes, sin diseño de lo que salió de alcance, contradicciones resueltas o consultadas.
- [ ] Solo .docx en el repo y en Drive (sin PDF).
- [ ] Marca DinoCloud aplicada; documento marcado como Confidential.
- [ ] Publicación en Drive/ClickUp pendiente de OK del usuario.
