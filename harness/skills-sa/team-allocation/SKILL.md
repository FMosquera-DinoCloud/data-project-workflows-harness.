---
name: team-allocation
description: "Trae y analiza las asignaciones del equipo de un proyecto desde la fuente de verdad (Resource Planner por la copia central de planner.dinocloud.com; respaldo: planilla Resource Planner - Assignations): quién está asignado, con qué rol, cuántas horas mensuales, desde y hasta cuándo, si es facturable y la carga total de cada persona. Detecta asignaciones por vencer, sobreasignación y diferencias con quién trabaja realmente en ClickUp. Usar cuando se pregunte quién está en el proyecto, qué dedicación tiene alguien, hasta cuándo está asignado, capacidad del equipo, o antes de estimar, planificar o cargar horas."
---

# team-allocation

Configuración: `~/claude-workspace/harness/config.toml [allocation]`. Por proyecto: `project.toml [allocation].sheet_projects` (nombres o prefijos tal como figuran en la columna "Project Name" de la planilla). Reglas comunes: `.../reference/conventions.md`.

**La planilla es la fuente de verdad de las asignaciones.** Si difiere de `project.toml [[team]]` o de ClickUp, manda la planilla, y la diferencia se reporta.

## Confidencialidad (obligatorio)

- La planilla tiene pestañas de costos y sueldos (`TeamCost*`), de contactos de clientes (`Contact Points`) y de forecast de contratación. **Nunca se leen.** Solo se leen las pestañas de `allowed_tabs` y el script lo hace cumplir.
- No leer la planilla con `read_file_content` ni `download_file_content`: traen muestras de todas las pestañas, incluidas las prohibidas. Se usa únicamente el script.
- No hacer copias de la planilla: duplicarían los datos sensibles.
- `memory/allocations.toon` no lleva emails, costos ni tarifas.

## Traer

**Primero la copia central del planner.** `~/claude-workspace/planner/allocations.toon` (la deja `planner_mirror.py` cada semana o ad hoc; ver `conventions.md`, "Planner") tiene el mismo esquema que la salida de abajo más `absences[N]{person,start,end}` (licencias), para todos los proyectos activos. Se filtran las filas cuyo `sheet_project` coincide con `[allocation].sheet_projects` del proyecto y se escriben en `memory/allocations.toon`. Si el usuario pide datos al día y la copia tiene `.fetched_at` de más de un día, se refresca antes con `~/claude-workspace/harness/.venv/Scripts/python.exe ~/claude-workspace/harness/scripts/planner_mirror.py` (Mac/Linux: `.venv/bin/python`). Si la copia no existe, está a más de 8 días, o no hay token / da 401, se avisa en Pendientes y se sigue con la planilla.

Respaldo por la planilla de Sheets:

```bash
~/claude-workspace/harness/.venv/bin/python ~/claude-workspace/harness/scripts/allocations.py \
  fetch --project "<sheet_project 1>" [--project "<sheet_project 2>"] --out memory/allocations.toon
```

- Si responde "falta login", el usuario tiene que correr, con `!` en el prompt: `! ~/claude-workspace/harness/.venv/bin/python ~/claude-workspace/harness/scripts/allocations.py login`. Claude nunca hace el login ni pide que le peguen un token.
- Si `sheet_projects` está vacío: mostrar los nombres de proyecto candidatos (`grep` sobre el nombre del cliente en la salida de una corrida con `--project "<cliente>"`) y pedir cuál o cuáles corresponden. Guardarlos en `project.toml` con OK.
- `unmatched_projects` con valores → avisar que ningún nombre coincidió.
- La salida es `allocations[N]{person,role,seniority,start,end,monthly_hours,billable,sheet_project,state}` (state: active | upcoming | ended) + `load[N]{person,assigned_hours_all_projects,available_hours,load_pct}`.

## Analizar

1. **Por vencer:** asignaciones activas con `end` dentro de `ending_alert_days`. Cruzar con el próximo hito de `project.toml`: si la persona tiene tareas del camino crítico después de su `end`, es un riesgo.
2. **Sobreasignación:** `load_pct > 100`. Se informa la carga total, sin detallar los otros proyectos.
3. **Diferencias con la realidad**:
   - asignada y activa, pero sin tareas ni actividad en ClickUp en 7 días;
   - con tareas asignadas en el folder de ClickUp del proyecto, pero sin asignación vigente;
   - que figura en `project.toml [[team]]` sin asignación, o al revés.
4. **Capacidad del mes:** la suma de `monthly_hours` activas por rol. Sirve para `estimate` y para planificar.
5. Actualizar `project.toml [[team]]` (nombres, roles y aliases) solo con OK. La dedicación no se copia ahí; vive en `memory/allocations.toon`.

## Salida

- Interactivo: una tabla por persona (rol, horas por mes, hasta cuándo, facturable, carga total %) y después las alertas.
- `.harness/state.toml`: `[sources].allocation` = el `.fetched_at` de la copia del planner (o la hora de la lectura de la planilla si se usó el respaldo), no la fecha de la última corrida de la skill.
- `index.toon`: la fila de `memory/allocations.toon` (`type=memory`, tags `asignaciones` y los nombres).
- Commit `harness(allocation): <N> asignaciones, <M> alertas`.

## Quién lo usa

- `project-status`: la sección Equipo muestra la dedicación; las alertas de vencimiento y sobreasignación van a Alertas.
- `weekly-hours`: las horas mensuales asignadas del usuario son la "asignación" contra la que `clickup-time-logging` compara el total cargado.
- `portfolio-update`: las asignaciones que vencen antes del deadline son un riesgo del proyecto.
- `estimate`: la capacidad real por rol.
