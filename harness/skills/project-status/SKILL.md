---
name: project-status
description: "Arma el status priorizado de un proyecto leyendo ClickUp (tareas de todo el equipo), el backlog interno y lo ingerido recientemente: qué hace cada persona, qué está trabado, vencido o estancado, y qué conviene atender hoy. Usar cuando se pregunte por el estado del proyecto, cómo va el sprint, qué está haciendo cada uno, qué está bloqueado, qué priorizar hoy, o en la rutina diaria. Use for daily project status, sprint health, who-is-doing-what and priorities."
---

# project-status

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md` (sobre todo la sección Prioridad).

## Entradas

1. **ClickUp** (`project.toml [clickup]`): `clickup_filter_tasks` con `folder_ids` (o `list_ids` si no hay folder), incluyendo tareas cerradas en los últimos 7 días. Por tarea: estado, asignados, fecha de vencimiento, `date_updated`, prioridad y dependencias.
2. **Backlog interno**: `backlog/backlog.toon`.
3. **Contexto reciente**: digests y reuniones desde el último status (con `index.toon` se encuentran sin listar carpetas).
4. **Estado del harness**: `.harness/state.toml` y `.harness/run-status` (errores o fuentes caídas).
5. **Asignaciones** (opcional): `memory/allocations.toon`, si existe. Si tiene más de 7 días, se avisa en Pendientes.
6. Fase actual e hitos: `project.toml [project].stage` y `[[phases]]`.

## Análisis

- **Por persona** (equipo de `project.toml`; se matchean `aliases` con los asignados de ClickUp): dedicación asignada si hay `allocations.toon`, en qué está, qué cerró desde el último status y qué tiene vencido. Las alertas de asignación (por vencer, sobreasignación, trabaja sin asignación) van a Alertas.
- **Alertas**:
  - vencidas;
  - sin movimiento hace más de `stale_task_days` (de `config.toml`);
  - trabadas o con dependencia abierta;
  - en `review` hace más de 2 días hábiles;
  - sin asignado;
  - action items de reuniones sin tarea en ClickUp ni en el backlog.
- **Prioridad del día**: aplicar la regla bloqueos → fecha → camino crítico a todo lo que depende del usuario (backlog interno + tareas de ClickUp asignadas a él + revisiones que esperan por él). Recalcular `priority` en `backlog.toon` si cambió y anotar el motivo en `notes.md`.
- **Hito**: días hábiles al próximo `end` de fase y % de tareas del camino crítico cerradas.

## Salida: `status/AAAA-MM-DD.md`

```markdown
> **DinoCloud Internal - Confidential**
# Status <proyecto> — AAAA-MM-DD
**Fase:** · **Próximo hito:** fecha (N días hábiles) · **Salud:** VERDE/AMARILLO/ROJO + motivo en una frase

## Hoy te toca                (máx. 5, ordenado por prioridad, cada uno con por qué y link)
## Alertas                    (bloqueos, vencidas, estancadas, review demorado)
## Equipo                     (una línea por persona: en qué está · cerró · vencido)
## Novedades desde el último status   (decisiones D-NNN, reuniones, lo clave de canales)
## Propuestas pendientes de backlog   (cantidad + link al digest)
## Pendientes del harness     (fuentes caídas, canales sin conector, reuniones sin notas)
```

La salud es ROJO si hay algo del camino crítico vencido o bloqueado, AMARILLO si hay alertas sin impacto en el hito y VERDE en el resto de los casos. Los primeros 12 renglones tienen que alcanzar para entender el día, porque es lo que muestra el hook de sesión.

## Entrega

1. `index.toon` + `.harness/state.toml` (`[last].status`) + commit `harness(status): AAAA-MM-DD`.
2. **DM de Slack** al `slack_user_id` de `config.toml` (nunca a otra persona): `*<proyecto>* <salud> · próximo hito <fecha>` + las 3 primeras de "Hoy te toca" + cantidad de alertas + ruta del archivo. Menos de 800 caracteres. Si hay varios proyectos en la corrida, `harness-run` hace un solo DM combinado y esta skill no manda nada (el prompt lo indica con `SIN DM`).
3. Interactivo: mostrar el contenido de "Hoy te toca" y "Alertas".

## Modo ingeniero (`config.toml [user].role = "engineer"`)

El status es del usuario, no del equipo:

- **Entradas de ClickUp:** las tareas asignadas al usuario (`clickup_resolve_assignees` con `me`) y las que esperan una revisión suya. Del resto del equipo, solo lo que lo bloquea o lo que él bloquea.
- **Salida:** las mismas secciones, pero `## Equipo` se reemplaza por `## Mis tareas` (una línea por tarea: estado · vence · próximo paso) y una línea final con lo que el usuario bloquea a otros. La salud refleja sus tareas y el hito de la fase.
- El backlog interno se filtra por `owner` = el usuario (o vacío).
