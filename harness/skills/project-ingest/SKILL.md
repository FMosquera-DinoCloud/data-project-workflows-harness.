---
name: project-ingest
description: "Incorpora al proyecto lo nuevo de reuniones (notas y transcripts de Meet vía Calendar), Gmail, Slack, Teams, Google Chat y GitHub según project.toml: resume, registra decisiones y action items, y propone cambios de backlog. Usar cuando se pida ponerse al día, qué se habló, qué pasó en las reuniones, qué hay nuevo en mails o canales de un proyecto, o al correr la rutina diaria."
---

# project-ingest

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`. Configuración: `project.toml` del proyecto.

## Ventana y alcance

- Ventana: desde `[last].ingest` de `.harness/state.toml` hasta ahora. Si falta, los últimos 7 días. Si se pide un período explícito, usar ese.
- `scope_confirmed = false` → solo fuentes internas (`[[internal]]`, reuniones sin invitados externos). Anotar en Pendientes: "Material del cliente sin procesar: falta confirmar alcance".
- Fuente sin configurar → se saltea. Tipo sin conector (hoy `gchat`, `teams` hasta autenticar) → se saltea y va a Pendientes. `whatsapp` nunca se lee.

## 1. Reuniones → `context/meetings/`

1. `list_events` en la ventana. Un evento es del proyecto si el título contiene algún `calendar.match` y ningún `calendar.exclude`. Solo eventos con invitados y que no estén cancelados.
2. Buscar en `attachments` el Doc "Notas de Gemini" y leerlo con `read_file_content(fileId)`. Si no tiene adjunto: buscar en Drive `title contains '<título del evento>' and title contains 'Notas de Gemini'`. Si tampoco aparece, registrar la reunión igual (fecha, participantes, sin notas) y listarla en Pendientes.
3. Se resume a partir de la sección de notas (Resumen, Decisiones, Próximos pasos, Detalles). La transcripción se consulta solo para confirmar algo ambiguo. **No se copia.**
4. Escribir `context/meetings/AAAA-MM-DD-<slug-del-título>.md`:

```markdown
> **DinoCloud Internal - Confidential**
# <título> — AAAA-MM-DD
**Participantes:** nombres (externos: nombre y rol) · **Fuente:** [Notas de Gemini](link) · [Evento](link)
## Resumen            (3-6 viñetas)
## Decisiones         (cada una con D-NNN si se registró)
## Action items       (- [ ] Responsable: qué · fecha si se dijo · T-NNN o ClickUp si existe)
## Riesgos y bloqueos
## Preguntas abiertas
```

   Si ya existe el archivo de esa reunión (en `context/meetings/` o en `memory/privado/reuniones/`), se actualiza; no se duplica.

5. **Separar lo privado antes de escribir** (ver "Información compartida y privada" en `conventions.md`): asignaciones, dedicaciones, horas, presupuesto, otros proyectos o clientes de las personas, temas comerciales o de cuenta, feedback o temas personales, y datos de contacto del cliente. La nota compartida solo trata del proyecto; lo privado no se menciona ahí. Una reunión toda privada (asignación, staffing, cuenta, 1:1) se escribe entera en `memory/privado/reuniones/AAAA-MM-DD-<slug>.md`; en una mixta, lo privado va a `memory/privado/reuniones.md`. Las decisiones privadas van a `memory/privado/decisiones.md` como `P-NN`.

## 2. Canales → `context/digest/AAAA-MM-DD.md`

- **Slack** (`[[internal]]` y `[[client_channels]]` de tipo `slack`/`slack-connect`): `slack_read_channel` con `oldest` = inicio de ventana. **Abrir siempre todos los hilos** que indiquen respuestas (`Thread: N replies`) con `slack_read_thread`, en paralelo y antes de sacar conclusiones, incluso si el mensaje raíz parece menor: las respuestas del cliente y las aclaraciones del equipo viven ahí. Un hilo con actividad dentro de la ventana se abre aunque el mensaje raíz sea anterior. Si un hilo no se puede abrir, decirlo en el digest. El mismo criterio vale al leer Slack desde `slack_search_*`.
- **Gmail** (`gmail.query` y canales de tipo `gmail`): `search_threads` con `after:` de la ventana, excluyendo `exclude_senders`; leer el hilo solo si el asunto o el snippet es del proyecto.
- **GitHub** (`github.repos`), si hay conector: PRs e issues abiertos o actualizados en la ventana.
- Relevante = decisión, pedido, compromiso con fecha, bloqueo, cambio de alcance, riesgo, entrega, pregunta sin responder. El small talk y las notificaciones automáticas se descartan.
- Formato: dos secciones, **Interno** y **Cliente**. Cada ítem en una línea: `- [canal · autor · hora](link) qué pasó → qué implica`. Un archivo por día de la ventana que tenga ítems.

## 3. Consecuencias

- **Decisiones** tomadas (en reunión o canal) → nueva entrada `D-NNN` en `docs/decisions/decisions.md` con fuente, sin datos privados: esos van como `P-NN` en `memory/privado/decisiones.md`. Son privados el staffing y las asignaciones, lo comercial (precios, márgenes, horas, fondeo), otros proyectos, la relación con la cuenta (percepción del cliente, fricciones, escalamientos), el feedback o los comentarios sobre un colaborador puntual, los temas de RR. HH. y lo que salga de una reunión 1 a 1. `decisions.md` y `docs/architecture/` se comparten con el equipo (ver "Información compartida y privada" en `conventions.md`). Si contradice una vigente, marcar la anterior como `reemplazada por D-NNN`.
- **Backlog**: no se modifica `backlog.toon`. Las propuestas (tarea nueva, cambio de estado, cambio de owner o de fecha) se escriben en la sección `## Propuestas` del digest del día, con formato `task-writer` resumido y fuente. Las aplica `backlog` con OK del usuario.
- **Índice de decisiones:** cada `D-NNN` nuevo o reemplazado lleva su propia fila en `index.toon` (`type=decision`, `path` = archivo y ancla, `summary` = la decisión en una línea, `tags` = `D-NNN` y tema). Las filas agregadas de rango ("D-01..D-16") no reemplazan a las individuales.
- **Personas y riesgos nuevos** → se anotan en el digest; `project-consolidate` los pasa a `memory/`.
- **Tiempo**: por cada reunión del proyecto a la que el usuario asistió, agregar una fila a `time/AAAA-Www.toon` (`source=meeting`, minutos del evento, `evidence` = link).

## 4. Cierre

1. Actualizar `index.toon` (una fila por archivo escrito o modificado).
2. `.harness/state.toml`: `[last].ingest` = fin de la ventana; `[sources].<fuente>` = ahora para cada fuente que respondió bien.
3. Commit `harness(ingest): <N> reuniones, <M> ítems de canales`.
4. Interactivo: resumir en 5 líneas qué entró y cuántas propuestas quedaron. Desatendido: nada más, `project-status` lo reporta.

## Modo ingeniero (`config.toml [user].role = "engineer"`)

- **Reuniones:** además del `calendar.match`, el usuario tiene que figurar como invitado que no rechazó el evento. Las reuniones del proyecto a las que no fue no se ingieren.
- **Canales:** de los canales internos y con el cliente, solo los hilos donde el usuario escribió o lo mencionaron, más los mensajes que contienen una decisión. Gmail, solo los hilos donde el usuario está en `to` o `cc`.
- Los action items se registran todos, pero las propuestas de backlog solo son las que tienen al usuario como responsable.
