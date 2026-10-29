---
name: weekly-hours
description: "Prepara y carga las horas semanales en ClickUp a partir de la evidencia de los proyectos del harness (reuniones, commits, status, backlog, time/), siguiendo las reglas de la skill clickup-time-logging. Usar cuando se pida cargar, preparar o revisar horas, time tracking, cuánto tiempo se trabajó en una tarea o proyecto, o los viernes."
---

# weekly-hours

Reglas de estimación, formato de descripción y carga: skill **`clickup-time-logging`**. Esta skill no las repite; le cambia la fuente de evidencia. En Claude Code no existen `recent_chats` ni `conversation_search`, y la evidencia está en los repos de los proyectos.

## Modo preparar (desatendido, viernes; o a pedido)

Por cada proyecto activo de `projects.toon`, para la semana ISO en curso:

1. Evidencia, desde el último día cargado (ver `clickup_get_time_entries` en modo interactivo; en desatendido, desde el lunes):
   - `time/AAAA-Www.toon`: reuniones, que ya las carga `project-ingest`.
   - `git log --since` en el repo del proyecto y en los repos de `project.toml [github]` accesibles localmente: commits del usuario, agrupados por día y tema.
   - `status/` y `context/digest/`: tareas que el usuario movió, revisó o cerró.
   - `backlog.toon`: tareas cerradas o actualizadas en la semana, con `clickup_id` si tienen.
   - Sesiones de Claude Code del proyecto (`~/.claude/projects/<cwd-codificado>/*.jsonl`): solo fecha, duración aproximada y tema. No se copia contenido.
2. Mapear cada bloque de trabajo a una tarea de ClickUp (`clickup_id`) o dejarlo `task_ref=sin-tarea`.
   La "asignación" contra la que se compara el total es la dedicación mensual del usuario en `memory/allocations.toon` de cada proyecto, prorrateada a la semana (horas por mes × 12 / 52). Si no existe ese archivo, se compara contra `config.toml [user].weekly_hours`.
3. Escribir las filas en `time/AAAA-Www.toon` (`source` = meeting | git | status | session | backlog) y un resumen en `time/AAAA-Www.md` con la propuesta de carga por día en el formato de tabla de `clickup-time-logging`.
4. Commit `harness(hours): propuesta AAAA-Www`. **No se carga nada.**

## Modo cargar (solo interactivo)

1. Leer la propuesta, completar lo que falte con el flujo de `clickup-time-logging` (rol, billable, asignación) y validar contra lo ya cargado.
2. Mostrar la tabla final con la descripción de cada entrada y cargar solo con OK explícito (`clickup_add_time_entry`). **Siempre con descripción, sin preguntar.**
3. **Descripción de alto nivel**, en el idioma que use el equipo en ClickUp: el entregable o la actividad en pocas palabras, sin el detalle de qué incluyó. Esta regla reemplaza el formato `<entregable>: <qué incluyó>` de `clickup-time-logging`. El detalle queda en `time/AAAA-Www.md`.
   - Bien: `Solution design document v0.3`, `Benchmark design review`, `Video delivery PoC effort estimate`, `Internal sync - delivery team`.
   - Mal: `Solution design document v0.3: AWS architecture and flow diagrams (API, state machine...)`.
4. Marcar en `time/AAAA-Www.md` qué se cargó, con fecha, y hacer commit.

## Tiempo por tarea

Para "¿cuánto llevamos en T-NNN / en la tarea X?": sumar las filas de `time/*.toon` con ese `task_ref` y los time entries de ClickUp de ese `clickup_id`. Mostrar las dos cifras por separado (evidencia local y cargado).
