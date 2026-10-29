> **DinoCloud Internal - Confidential**

# Mejoras del harness

Lo mantiene `harness-evolve` y cada sesión cuando detecta un patrón (una tarea que pediste 3 veces, una corrección que repetiste, una skill que no se disparó). Las entradas se agregan al final y no se reordenan. Nada se implementa sin OK.

Formato de cada entrada:

```markdown
## <título corto>
- **Detectado:** AAAA-MM-DD · **Tipo:** skill nueva | mejora a <skill> | descripción | permisos | bug
- **Patrón:** qué se repitió y cuántas veces
- **Propuesta:** qué cambiar
- **Beneficio:** qué se gana
- **Estado:** propuesta | aplicada (commit) | descartada (motivo)
```

## DM de Slack con destino fijo
- **Detectado:** 2026-10-08 · **Tipo:** permisos
- **Patrón:** el DM de la rutina diaria lo manda el modelo con `slack_send_message`, después de leer status que incluyen contenido ingerido de reuniones y canales. Un texto malicioso en esa fuente podría intentar cambiar el destino del mensaje; hoy solo lo frena la instrucción del prompt.
- **Propuesta:** mandar el DM con un incoming webhook de una Slack app propia (URL en variable de entorno), de modo que el modelo solo arme el texto y el destino quede fijo fuera de su alcance.
- **Beneficio:** el contenido de terceros no puede redirigir información a otro canal.
- **Estado:** propuesta

## Rutinas corriendo sin proyectos
- **Detectado:** 2026-10-12 · **Tipo:** mejora a harness-run / project-new
- **Patrón:** `projects.toon` está vacío. Las rutinas del 09-oct (daily y friday) y del 12-oct (daily) terminaron con "0 proyectos" y sin aviso. En la misma semana hubo sesiones en 6 carpetas de trabajo bajo `~/Desktop`, fuera de `~/dino-projects`. En varias de ellas la sesión empezó preguntando "¿en qué estado quedó esto?" o "¿tenés el historial de esta carpeta?", que es lo que resuelven el hook de SessionStart y `project-status` en un proyecto del harness.
- **Propuesta:** (1) si una rutina no encuentra proyectos activos, `harness-run` lo deja en el log como advertencia y lo incluye en el DM. (2) `project-new` suma un modo "sumar carpeta existente" que deja el repo de código donde está y crea el repo de contexto en `~/dino-projects/<proyecto>` apuntando a él.
- **Beneficio:** las rutinas producen status de los proyectos reales y se dejan de reconstruir a mano el contexto al abrir una sesión.
- **Evidencia 2026-10-19:** siguió igual toda la semana: daily del 13, 14, 15, 16 y 19-oct y friday del 16-oct terminaron con "0 proyectos" y sin aviso. Mientras tanto hubo más de 12 sesiones en 2 carpetas de trabajo bajo `~/Desktop`, que siguen fuera del harness.
- **Evidencia 2026-10-26:** tercera semana igual: daily del 20, 21, 22, 23 y 26-oct y friday del 23-oct, todas con "0 proyectos". Hubo sesiones en 3 carpetas de `~/Desktop` y dos de ellas arrancaron con "¿en qué estado está este proyecto?" o "¿en qué estado estamos de las ramas?" (23-oct).
- **Estado:** propuesta

## task-writer: borrador primero e idioma del destino
- **Detectado:** 2026-10-12 · **Tipo:** mejora a task-writer
- **Patrón:** en una misma sesión (semana del 05-oct), después de cargar `task-writer` se creó una tarea en ClickUp sin mostrar el texto antes. El usuario corrigió tres veces: "me hubieras preguntado", "no la crees, solo dame el texto" y "no la crees de una, esperá mi validación". También pidió dos veces el título en inglés para que fuera coherente con el resto del tablero. La regla de pedir OK ya existe, pero está al final de la sección de ClickUp y no se respetó.
- **Propuesta:** subir la regla a un paso explícito del flujo ("1. mostrar el borrador completo; 2. crear solo con OK") y agregar a `project.toml` un campo `[clickup] language` (por ejemplo `en`) para el título y la descripción de lo que sale del repo.
- **Beneficio:** se evitan tareas creadas sin validar y retrabajo de traducción.
- **Evidencia 2026-10-26:** el usuario lo volvió a pedir de forma explícita: "antes de crearlas validalas conmigo" (19-oct) y "decime cómo la armarías en inglés y la sumamos una vez que te confirme" (22-oct). También corrigió el formato del título con un prefijo fijo del tablero (`[<workstream>] <tema>:`), que encaja en `project.toml` como `[clickup] title_prefix` junto con `language`.
- **Estado:** propuesta

## Commits agrupados por tema
- **Detectado:** 2026-10-12 · **Tipo:** skill nueva
- **Patrón:** el pedido "armá commits por tema, con fix/feat, y pusheá" (o "volvé atrás y commiteá de a un tema") aparece 3 o más veces entre dos sesiones del mismo repo, con varias vueltas de "avancemos un commit más".
- **Propuesta:** skill `commit-topics`. Agrupa el diff pendiente por tema, propone la lista de commits (conventional commits: tipo, alcance y mensaje) y, con OK, los crea en orden. El push se hace solo si se pide.
- **Beneficio:** historial prolijo para la revisión de PR sin ir commit por commit.
- **Evidencia 2026-10-19:** en una sesión del 14-oct, "commiteá y pasá al paso N" se pidió 6 veces seguidas. En otra, "arreglá primero los minors en un commit y después el major". El patrón ahora incluye commits por severidad después de una revisión.
- **Estado:** propuesta

## "¿Cómo lo corro?" en la plantilla
- **Detectado:** 2026-10-12 · **Tipo:** mejora a project-new (plantilla)
- **Patrón:** "¿cómo lo ejecuto?" o "¿cómo levanto la aplicación?" se preguntó 4 veces en un mismo repo, en sesiones distintas. En otros 2 repos hubo preguntas equivalentes sobre cómo desplegar ("¿qué comandos ejecuto?", "¿cómo vuelvo a desplegar?").
- **Propuesta:** agregar al `CLAUDE.md` de la plantilla una sección "Cómo correrlo y desplegarlo" (comandos y restricciones de prueba), que `project-new` completa al dar de alta y que se actualiza cuando cambia.
- **Beneficio:** la respuesta queda una sola vez en el repo y deja de reconstruirse en cada sesión.
- **Evidencia 2026-10-19:** en el mismo repo se volvió a preguntar "¿qué comando corro?" (14-oct) y "dame el comando para correr la evaluación y la comparación" (15-oct), además de cómo apuntar las pruebas al entorno sandbox (13 y 14-oct).
- **Evidencia 2026-10-26:** en otro repo se preguntó "¿cómo levanto la demo?" (21-oct) y el usuario pegó el comando de arranque con sus variables de entorno 3 veces (21 y 23-oct) para que la sesión lo corriera. En el primer repo preguntó qué hacía falta para pasar del entorno sandbox al de dev (26-oct). La sección debería incluir los entornos disponibles y cómo se elige cada uno.
- **Estado:** propuesta

## harness-evolve desatendido sin poder leer las sesiones
- **Detectado:** 2026-10-12 · **Tipo:** permisos
- **Patrón:** en la corrida semanal del 12-oct, `harness-evolve` no pudo ejecutar un script de solo lectura sobre `~/.claude/projects/*.jsonl` (pedía aprobación) y tuvo que reconstruir las fechas y los pedidos con Grep, de forma parcial. `git` con `cd` previo también pidió aprobación.
- **Propuesta:** agregar `harness/bin/session-digest` (solo lectura: fecha, carpeta, mensajes del usuario recortados y conteo de tools en la ventana) y sumarlo a la allowlist de la rutina weekly. En las skills, usar `git -C <dir>` en lugar de `cd && git`.
- **Beneficio:** la revisión semanal cubre todas las sesiones de la ventana con fechas exactas y sin prompts.
- **Evidencia 2026-10-26:** esta corrida pudo leer las sesiones sin pedir aprobación, pero con un script armado en el momento en `$TMPDIR`. La primera versión, en un heredoc, la bloqueó el parser del shell. Sigue haciendo falta un script versionado para que el resultado sea el mismo todas las semanas.
- **Estado:** propuesta

## Revisión de PR por número con comentarios en GitHub
- **Detectado:** 2026-10-19 · **Tipo:** skill nueva
- **Patrón:** el 14 y el 15-oct, en 5 sesiones del mismo repo, se pidió revisar PRs por número, encadenando varios ("¿y el 120?", "¿y el 121?"). Después se pidió publicar en GitHub los hallazgos "major". En una sesión hubo que repetirlo 3 veces ("comentalos", "hacé los comentarios en el repo", "en el PR") porque no se publicaban. También se pidió aplicar los comentarios recibidos, responderlos y corregir por severidad (primero los minors en un commit, después el major).
- **Propuesta:** skill `pr-review` (o una mejora a `/code-review`) que reciba uno o más números de PR, clasifique los hallazgos en major y minor, muestre el borrador de los comentarios y, con OK, los publique inline con `gh`. Que también tenga un modo "atender comentarios" para implementar, commitear por severidad y responder cada hilo.
- **Beneficio:** el ciclo de revisión queda en un paso, sin repetir el pedido de publicar ni el de ir PR por PR.
- **Evidencia 2026-10-26:** del 20 al 23-oct se revisaron o atendieron los comentarios de 6 PRs distintos del mismo repo, encadenados en 4 sesiones. Se repitieron los pedidos "armá el plan con un commit por comentario", "corregí los major", "arreglá los 3 minor", "pusheá y armá el comentario", "publicá las respuestas y actualizá el cuerpo del PR" y "no pushees todavía, explicame qué hiciste". El modo "atender comentarios" es ahora el uso más frecuente, y conviene que pare antes del push y muestre un resumen.
- **Estado:** propuesta

## dino-doc sin registrar ni versionar
- **Detectado:** 2026-10-19 · **Tipo:** mejora a dino-doc
- **Patrón:** el 15-oct se pidió que los documentos en Drive tuvieran el formato de otro documento de referencia. Se eligió una opción y se creó `harness/skills/dino-doc/`, que ya está enlazada en `~/.claude/skills/`. Sigue sin commitear y sin entrada en este backlog.
- **Propuesta:** probarla en un proyecto de prueba (generar un .docx y subirlo con `google-api`), commitearla y registrarla acá como `aplicada`. Revisar que los assets (logo y fondo) no traigan nada de un cliente.
- **Beneficio:** la skill queda disponible en las otras PCs y respeta el flujo de cambios del harness.
- **Evidencia 2026-10-26:** se usó en una sesión real el 22-oct (manual de QA) y sigue sin commitear: `git status` muestra `?? harness/skills/dino-doc/`.
- **Estado:** propuesta

## aws-diagram: cerrar con el comando para abrir
- **Detectado:** 2026-10-19 · **Tipo:** mejora a aws-diagram
- **Patrón:** el 15-oct, después de generar el diagrama, el usuario tuvo que pedir "dame el comando para hacer un open". El sandbox bloquea `open`, así que la skill no puede mostrarlo sola. Ese mismo día, en otra carpeta, preguntó si había alguna skill para diagramas de AWS: la skill existe, pero no se ofreció.
- **Propuesta:** que la skill termine siempre con la ruta absoluta y el comando `open <archivo>` listo para copiar. Sumar a la `description` disparadores como "¿hay algo para diagramas?" o "¿con qué armo un diagrama?".
- **Beneficio:** menos idas y vueltas al revisar diagramas.
- **Estado:** propuesta

## Telemetría: falta el script de headers de OpenTelemetry
- **Detectado:** 2026-10-19 · **Tipo:** bug
- **Patrón:** el log de la weekly del 19-oct registra `otelHeadersHelper failed` porque falta `/opt/dinocloud/otel-headers.sh`. Esa ruta viene de la configuración administrada, no del harness. El 15-oct, además, el pull y el push de la daily fallaron por DNS; la rutina siguió con lo local, que es lo correcto, pero no avisó.
- **Propuesta:** avisarle a IT o al admin de Claude de la organización que falta el helper en esta Mac (no se toca desde el harness). En `harness-run`, contar los pull o push fallidos y sumarlos al aviso de la rutina.
- **Beneficio:** la telemetría corporativa vuelve a funcionar y un repo desincronizado no pasa desapercibido.
- **Evidencia 2026-10-26:** el log de la weekly del 26-oct vuelve a registrar `otelHeadersHelper failed` por el mismo archivo faltante.
- **Estado:** propuesta

## Sincronización con el harness de origen: base general y perfil SA/TL
- **Detectado:** 2026-10-21 · **Tipo:** mejora a todo el harness
- **Patrón:** el repo del equipo quedó en el starter del 08-oct; el harness de origen sumó skills, guardas y chequeos que sirven a cualquier ingeniero, y otras que son del rol de SA/TL.
- **Propuesta:** base para ingeniería: `pr-brief`, `task-review`, `session-close`, guardas determinísticas (`hooks/guard.sh`, `guards.py`, `install_hooks.py`), `harness_lint.py`, `related.py`, `apply_profile.py`, `aws_price.py`, tests, hooks de cierre de sesión y de compactación, reglas nuevas de `task-writer`, `project-ingest` y `project-consolidate`, y mejoras de `aws-diagram`. Perfil SA/TL aparte en `harness/skills-sa/` (`solution-design`, `team-allocation`, `portfolio-update`, `team-mirror`), con `-SA` / `--sa` en los instaladores y `reference/perfil-sa.md`. Quedan fuera: las copias locales de ClickUp y Drive por API, la copia central del planner en la rutina, el espejo del equipo en la rutina, los DM de bandeja y de status semanal.
- **Beneficio:** el equipo recibe las mejoras generales sin skills propias de un rol, y quien lleva diseño y cuenta puede sumar las suyas.
- **Estado:** aplicada

## Entregables: cerrar con ruta, comando para abrir y subida a Drive
- **Detectado:** 2026-10-26 · **Tipo:** mejora a conventions.md (y a las skills que generan archivos)
- **Patrón:** después de generar un archivo (una PPT el 21-oct; un manual de QA en .docx el 22-oct), el usuario tuvo que preguntar cómo abrirlo o dónde quedó en 6 mensajes: "¿cómo abro la ppt?", "abrime el documento", "abrilo", "¿dónde lo puedo ver?", "¿en qué carpeta está?". En las dos sesiones terminó pidiendo subirlo a Drive. Es el mismo patrón que la entrada "aws-diagram: cerrar con el comando para abrir", pero alcanza a todas las skills que generan archivos.
- **Propuesta:** sumar a `conventions.md` una regla de cierre para todo entregable: ruta absoluta, comando `open "<ruta>"` listo para copiar (el sandbox bloquea `open`) y ofrecer subirlo a la carpeta de Drive del proyecto con `google-api`. Aplicarla en `dino-doc`, `aws-diagram` y cualquier skill que genere .docx, .pptx, .png o .html.
- **Beneficio:** se ahorran 2 o 3 idas y vueltas por entregable.
- **Estado:** propuesta

## project-status: ramas y PRs cruzados con las tareas
- **Detectado:** 2026-10-26 · **Tipo:** mejora a project-status
- **Patrón:** del 19 al 23-oct, en 2 repos, se pidió 6 veces el estado del trabajo en git: "¿en qué estado estamos de las ramas?", "¿qué ramas hay?", "¿en qué orden deberían hacerse los PRs pendientes?", "diagrama de ramas y PRs y en qué orden mergear" (2 veces) y "compará las ramas de GitHub con mis tareas activas" (23-oct). `project-status` hoy lee ClickUp y el backlog, pero no git.
- **Propuesta:** sumar a `project-status` una sección "Ramas y PRs" que, si `project.toml` declara el repo de código, liste las ramas activas y los PRs abiertos con `gh` (estado de revisión, CI, base y dependencias entre ellos), proponga un orden de merge y marque las ramas sin tarea y las tareas sin rama.
- **Beneficio:** la pregunta más repetida al abrir una sesión de código se contesta con el status diario, sin reconstruirla a mano.
- **Estado:** propuesta

## weekly-hours: no se activó con "¿con qué estuve esta semana?"
- **Detectado:** 2026-10-26 · **Tipo:** descripción
- **Patrón:** el 23-oct (viernes) se pidió "¿con qué estuve esta semana? Cada día y las horas dedicadas aprox." y después "¿y en ClickUp qué tareas actualicé?". Encaja con `weekly-hours`, que no se activó: se resolvió a mano. La rutina friday del mismo día terminó con 0 proyectos, así que tampoco preparó nada.
- **Propuesta:** sumar a la `description` disparadores como "¿con qué estuve esta semana?", "¿qué hice cada día?", "¿cuántas horas le dediqué a…?" y "¿qué tareas actualicé?". Que la skill también funcione con las sesiones de `~/.claude/projects` cuando no hay proyectos del harness.
- **Beneficio:** la carga de horas de los viernes sale de la skill, con sus reglas, en lugar de una estimación hecha a mano.
- **Estado:** propuesta
