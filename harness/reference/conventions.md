> **DinoCloud Internal - Confidential**

# Convenciones del harness

Todas las skills del harness siguen este documento. Si una skill contradice algo de acá, manda la skill.

## Resolver el proyecto

1. Subir desde el directorio actual hasta encontrar `project.toml`: esa es la raíz del proyecto.
2. Si no hay, leer `~/claude-workspace/projects.toon` y preguntar a qué proyecto se refiere el pedido. En modo desatendido nunca pasa, porque `harness-run` corre dentro de la raíz.
3. Configuración personal (usuario de Slack, zona horaria, horario): `~/claude-workspace/harness/config.toml`.

Nada de un proyecto se escribe en las skills. Todo sale de `project.toml`. Si una sección no está o está vacía, esa fuente se saltea sin error y el status lo menciona una vez.

## Modos

- **Interactivo** (por defecto): se puede preguntar. Toda escritura fuera del repo del proyecto (ClickUp, Drive, Slack a otras personas, mail) muestra antes lo que va a hacer y espera un OK explícito.
- **Desatendido**: el prompt empieza con `MODO DESATENDIDO`.
  - No preguntar nada. Si falta un dato, anotarlo en la sección "Pendientes" del archivo que se escribe y seguir.
  - Escribir solo dentro del repo del proyecto y hacer commit.
  - Única escritura externa permitida: un DM de Slack al usuario (`slack_user_id` de `config.toml`), y solo si la skill lo indica. Nunca a otra persona ni a un canal.
  - Nunca escribir en ClickUp, Drive, Gmail, Calendar ni en ningún otro sistema.

## Qué se guarda y qué no

- Todo archivo nuevo empieza con `> **DinoCloud Internal - Confidential**`.
- No se guardan transcripts crudos ni cuerpos de mail o de chat: se guarda un resumen, las decisiones, los action items y el link a la fuente.
- No se guardan credenciales ni tokens. Si aparece uno en una fuente, se omite y se avisa.
- Personas externas a DinoCloud: nombre y rol, sin email ni teléfono. Las internas se identifican por nombre.
- El contenido traído de conectores no sale de canales internos.
- Qué se publica para todo el equipo y qué queda privado: ver "Información compartida y privada".
- **Precios de AWS:** un precio o un modelo de precio (escalones, cargos extra) que va a un documento, a una tarea o al cliente sale de la Price List, con la fecha de vigencia. Se consulta con `harness/scripts/aws_price.py <service-code> [campo=valor] --grep <texto>`. Lo que no esté verificado así se dice como no verificado.
- **Antes de editar el harness** (skills, scripts, `conventions.md`): `git -C ~/claude-workspace pull --rebase --autostash` y buscar si el tema ya tiene sección o skill. Si la tiene, se edita esa; no se agrega una regla paralela. Puede haber otra sesión editando el harness al mismo tiempo.

### Al compactar

`hooks/session-start.sh` avisa cuando una sesión sigue después de compactarse (`source=compact`). Antes de seguir con el pedido se revisa el resumen, y el transcript si hace falta detalle, para guardar lo que todavía no está en el repo:

| Qué | Dónde |
|---|---|
| Decisiones tomadas en la sesión | `docs/decisions/decisions.md` con su fila en `index.toon` |
| Preguntas para el cliente o el equipo | `memory/open-questions.md` |
| Pendientes y estado del trabajo en curso | `status/<fecha>-cierre.md` (el mismo que usa `session-close`) |
| Preferencias o correcciones del usuario sobre cómo trabajar | auto memory (`feedback`) |
| Personas, roles o riesgos nuevos | `memory/` |

Lo que ya está en el repo, en ClickUp o en el historial de git no se duplica. Si no hay nada nuevo, se sigue sin escribir nada.

## Texto que sale del repo

Todo texto para ClickUp, Drive, mails, el cliente o el equipo (comentarios, descripciones de tareas, documentos) va **sin referencias internas**:

- nada de ids de tareas o decisiones (`T-012`, `D-004`, `A-13`, `H-02`, `Ref 108`) ni rutas o nombres de archivos locales;
- se explica el fundamento en palabras ("usamos Terraform para la infraestructura") y se usan los términos tal como figuran en ClickUp o en el documento de Drive.

Antes de mostrar un texto para aprobar, se revisa con grep: `[TDAH]-[0-9]+`, `Ref [0-9]+` y `/`, `.md`, `.toon`. Los ids internos quedan solo en los archivos del repo.

Un texto que el usuario va a copiar y pegar (comentario, mail, mensaje) se entrega en un bloque de código ```text, uno por destino, en texto plano: sin `>` de cita, sin `**`, sin encabezados `#`. Listas con `-` o `1.` y nada más, para que al copiarlo no arrastre marcas. Un comentario para una tarea lleva, justo arriba del bloque y fuera de él, el link a esa tarea en el tracker (por ejemplo, ClickUp) con su nombre.

## Formatos

- Prosa, decisiones y resúmenes: Markdown.
- Datos tabulares uniformes (backlog, índice, horas, estimaciones, manifest): TOON. Ver `toon.md`.
- Fechas `AAAA-MM-DD`; semanas ISO `AAAA-Www`; horas en la zona de `config.toml`.
- Nombres de archivo en minúscula y con guiones: `AAAA-MM-DD-slug.md`.

## Índice del proyecto (`index.toon`)

- Toda skill que crea, renombra o modifica un archivo del proyecto actualiza su fila en `index.toon` en el mismo paso: `path,type,date,summary,tags`.
- `summary`: una línea de 15 palabras como máximo, que diga qué se va a encontrar en el archivo.
- `tags`: tema, personas, ids de tareas (`T-012`) o decisiones (`D-004`), separados por `;`.
- Al borrar o archivar un archivo, su fila se borra.
- Para responder un pedido: primero buscar en `index.toon` con grep por palabra clave, id o persona, y después abrir solo los archivos que correspondan. No leer carpetas enteras.

## Backlog interno

- Fuente de verdad: `backlog/backlog.toon`. El texto largo de cada tarea va en `backlog/notes.md` bajo `## T-NNN`.
- Estados: `todo`, `doing`, `blocked`, `review`, `done`, `dropped`.
- Toda tarea se redacta con `task-writer`: objetivo y resultado esperado, nunca la implementación.
- Una tarea que también está en ClickUp guarda el id en `clickup_id`. ClickUp es la verdad del estado de ejecución del equipo; el backlog interno es la verdad de nuestras tareas.

## API directa o MCP

Regla: **la lectura masiva, repetitiva y determinista va por API con un script; el trabajo interactivo y toda escritura van por MCP.**

- **Script por API** cuando la tarea:
  - lee mucho volumen o pagina (copias locales, exportes, métricas);
  - corre en una rutina y tiene que salir igual cada vez;
  - no necesita criterio del modelo, solo traer y dar formato.

  El script va en `harness/scripts/`, usa la biblioteca estándar o dependencias de PyPI, corre desde `harness-run` antes de Claude y, si falla, deja que la skill siga por MCP como respaldo.
- **MCP** cuando:
  - hay que escribir (crear, comentar, cambiar estados), con el OK de siempre;
  - la consulta es puntual o necesita interpretar;
  - no se justifica manejar un token.
- **Tokens:**
  - Claude no los genera ni los ve. Propone el token que hace falta y con qué permisos mínimos, y le da al usuario el paso a paso para crearlo en la herramienta y guardarlo él mismo.
  - El token nunca se pega en la conversación. Se lee de forma oculta (`read -s` o `Read-Host -AsSecureString`) y se guarda fuera de todo repo: variable de entorno o un archivo en `~/.config/harness/` con permisos `600`. Para credenciales de AWS, AWS Secrets Manager.
  - La ruta o el nombre de la variable se declara en `config.toml`; el valor, nunca.
  - **Credenciales de un proyecto** (claves de API del cliente, bases de datos): nunca en el repo ni en el chat. Variable de entorno, almacén del sistema o AWS Secrets Manager; `project.toml` declara solo el nombre de la variable. Se prefieren credenciales temporales (perfil de AWS con rol, SSO) a claves estáticas.
  - Cada PC que corre rutinas necesita su copia del token.
- Cuando una skill repite lecturas por MCP que encajan en la primera categoría, `harness-evolve` lo propone como script.

## Tareas en ClickUp: estructura

ClickUp se organiza en pocas tareas grandes y sus subtareas, no en una lista plana de tareas chicas.

- **Épica:** una tarea padre por frente o entregable (por ejemplo "Identidad de personajes", "Consola: revisión y selección"). Agrupa todo lo de ese frente y tiene un dueño.
- **Subtarea:** un resultado verificable de al menos medio día de trabajo, dentro de la épica que corresponda. Lo más chico va como criterio de aceptación o checklist de una tarea existente, no como tarea nueva.
- **Un solo responsable y a lo sumo un validador.** Cada tarea o subtarea tiene un único asignado y, como mucho, un validador (campo Validator). Si el trabajo necesita a más de una persona, se separa en subtareas, cada una con su dueño; lo que ya es otra tarea va como dependencia. Nada de "X con Y" ni de varios asignados.
- **Responsable y validador solo en los campos.** En ClickUp viven en Assignee y Validator; la descripción no lleva línea de responsables ni los nombra como dueño o validador, para no mantener lo mismo en dos lugares. Al cambiar uno, se cambia el campo y nada más. Las personas se nombran en la descripción solo cuando son parte del contenido (quién entrega un insumo, quién decidió algo).
- **Validadores:** las tareas de diseño (documentos, especificaciones, spikes, decisiones) las valida quien lleva el diseño de la solución (TL o SA). Las de ejecución e implementación las valida otra persona del equipo que conozca el frente: quien consume el resultado, quien especificó o quien lleva lo vecino, nunca el mismo responsable.
- **Dependencias explícitas:** toda tarea o subtarea que se crea o se reescribe carga en ClickUp sus "waiting on" y "blocking" (`clickup_add_task_dependency`), no solo en el texto.
- **Antes de crear,** se revisa contra ClickUp (`clickup_search`, `clickup_filter_tasks`) y contra el backlog interno:
  - **duplicado:** si ya hay una tarea que cubre el resultado, se amplía esa (criterio, subtarea) o no se crea;
  - **consistencia:** que no contradiga decisiones vigentes ni lo que quedó fuera de alcance, que el dueño y las fechas cierren con sus dependencias, y que tenga épica;
  - se dice en una línea qué se revisó y dónde queda ("subtarea de X; espera a Y; la más cercana era Z").
- Crear una épica nueva o mover tareas entre épicas requiere OK explícito, como toda escritura en ClickUp.

## Skills del proyecto

- Las skills del harness (`harness/skills/`) son symlinks en `~/.claude/skills/`: un cambio llega al instante a todos los proyectos. Las convenciones también, porque se leen de acá. Lo que **no** se replica solo es lo que se copió de la plantilla al crear cada proyecto (`CLAUDE.md`, `project.toml`): un cambio de plantilla se aplica a los proyectos existentes a mano o con `project-new` en modo sumar.
- Cada proyecto puede tener skills propias en `<proyecto>/.claude/skills/<nombre>/SKILL.md` (se versionan con el repo del proyecto y Claude Code las carga solo dentro de ese proyecto). Siguen estas convenciones y se listan en la tabla "Situación → skill" del `CLAUDE.md` del proyecto.
- Una skill de proyecto que sirva para otros se generaliza al harness: `harness-evolve` las revisa y propone la promoción en `improvements.md`.

## Prioridad

Orden, del más al menos urgente:

1. **Bloquea a otra persona.** La tarea está en el `blocks` de otra o alguien la espera según una reunión o un canal.
2. **Tiene fecha:** `due` o hito de `project.toml` en los próximos 5 días hábiles, o ya vencida.
3. **Está en el camino crítico** de la fase actual de `project.toml`.
4. Todo lo demás.

`priority` guarda `P1` a `P4` según ese orden. Dentro de una misma prioridad, gana la fecha más cercana. Cuando una prioridad cambia, se escribe el motivo en una línea en `notes.md`.

## Información compartida y privada

Parte del repo del proyecto puede compartirse con el equipo (en el perfil SA, con el espejo `team-mirror`): solo lo técnico y de alcance ya procesado, es decir `docs/decisions/decisions.md`, `docs/architecture/` y `docs/diagrams/`. Las reuniones, los digests, el status, las horas y la memoria no. Lo que se escribe en lo compartido **solo trata del proyecto**: diseño, alcance, decisiones técnicas, tareas, entregas y quién hace qué a nivel de tarea. Lo demás va en `memory/privado/`.

Va a `memory/privado/`:
- asignaciones, dedicaciones, capacidad, horas y presupuesto del equipo, y la reunión donde se hablan;
- otros proyectos o clientes de las personas del equipo (por ejemplo, con qué otro proyecto reparten su tiempo);
- temas comerciales o de cuenta: horas vendidas, tarifas, exceso sobre lo contratado, renovaciones;
- feedback, desempeño y temas personales o de salud de alguien, y lo que salga de una reunión 1 a 1;
- la relación con la cuenta: percepción del cliente sobre personas, fricciones, escalamientos;
- datos de contacto del cliente (emails, teléfonos): en los archivos compartidos va nombre y rol.

Cómo se escribe:
1. **Antes de escribir** una reunión, una decisión o una tarea compartida, se separa lo privado. Lo privado no se menciona en el archivo compartido ni se resume en una línea: se omite.
2. **Reunión toda privada** (asignación, staffing, cuenta, 1:1 de feedback): la nota entera va a `memory/privado/reuniones/AAAA-MM-DD-<slug>.md` y no se crea en `context/meetings/`.
3. **Reunión mixta:** la nota compartida lleva solo lo del proyecto; lo privado va a `memory/privado/reuniones.md` (fecha, título, qué se habló, link a la fuente).
4. **Decisión privada** (staffing, comercial): `memory/privado/decisiones.md`, con numeración `P-NN`. Una decisión mixta se parte: el efecto sobre el proyecto va como `D-NNN` y el resto como `P-NN`, sin repetir lo privado en la `D-NNN`.
5. Cada archivo privado lleva su fila en `index.toon` (`type=memory`) para encontrarlo.
6. Cómo se publica lo compartido (controles del espejo y revisión por LLM): ver `perfil-sa.md`.

## Git

- Cada corrida que escribe en el proyecto termina con un commit: `harness(<skill>): <resumen corto>`.
- Solo `git add` de las rutas tocadas. Las skills no hacen `push`.
- `harness-run` hace `pull --rebase` antes de cada proyecto y `push` al terminar. En una sesión interactiva: `git pull` al empezar, y al cerrar, commit + `push` de lo trabajado. Un conflicto no se resuelve solo: se avisa al usuario.
- **Cierre de sesión:** al cerrar una sesión interactiva se corre la skill `session-close` (resumen en `status/AAAA-MM-DD-cierre.md`, horas sin registrar, commit y push). Si la sesión termina con `/exit` sin cierre, el hook `SessionEnd` la anota en `.harness/local/` (fuera de git) y el `SessionStart` de la próxima sesión pide armar ese cierre desde el transcript antes de seguir. Ninguno de los dos hooks llama al modelo.
- Si el árbol tenía cambios sin commitear al empezar, no se incluyen en el commit.

## Estado de ingesta (`.harness/state.toml`)

Lo escriben las skills; `harness-run` escribe aparte en `.harness/run-status`.

```toml
[last]
ingest   = "2026-09-30T08:40:00-03:00"   # fin de la última ventana ingerida
status   = "2026-09-30"
drive    = "2026-09-30T08:40:00-03:00"
consolidate = "2026-09-28"

[sources]                                  # última vez que cada fuente respondió bien
calendar = "2026-09-30T08:40:00-03:00"
```

La ventana de ingesta va desde `last.ingest` hasta ahora. Si no hay `last.ingest`, se toman los últimos 7 días.

## Guardas y chequeos (determinísticos)

Las reglas que no pueden fallar se hacen cumplir con código, no con texto (`CLAUDE.md` se sigue ~80% de las veces; un hook, el 100%).

- `hooks/guards.py` (registrado con `scripts/install_hooks.py`): bloquea envíos por MCP con credenciales o con ids internos dentro de un proyecto; bloquea que una rutina desatendida (`HARNESS_UNATTENDED=1`, lo exporta `harness-run`) modifique `CLAUDE.md`, `project.toml`, `.claude/` o el harness; exige la marca "DinoCloud Internal - Confidential" en los `.md` nuevos; y, con `secrets` (Bash, Read y Grep), impide leer o imprimir credenciales: archivos de `~/.config/harness`, `.env`, claves, volcados del entorno, valores del almacén del sistema o de Secrets Manager.
- `scripts/harness_lint.py <proyecto>`: rutas del índice que no existen, decisiones sin indexar, `.md` sin marca, `memory/` vacía, consolidate vencido. Lo corre `harness-run` después de cada proyecto y `project-new` al cerrar.
- `tests/test_harness.py`: `py -X utf8 -m unittest discover -s ~/claude-workspace/harness/tests`. Toda guarda nueva lleva su test.
- Plugins por proyecto: `scripts/apply_profile.py` activa solo los grupos de `config.toml [plugin_groups]` que el proyecto necesita.
- Principio: todo archivo que se genera tiene un lector nombrado; si ninguna skill lo lee, no se genera.
- Contexto de un tema: `scripts/related.py <proyecto> <T-xxx|D-xx|id de ClickUp|palabra>` junta en una salida la tarea, su equivalente en ClickUp (padre, dependencias), las decisiones vinculadas y las reuniones, digests y status donde aparece. Las relaciones se calculan al vuelo (id citado o nombre exacto de la tarea); no hay archivo de relaciones que mantener.
