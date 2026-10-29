> **DinoCloud Internal - Confidential**

# Perfil SA / TL

El harness tiene dos perfiles. La base (`harness/skills/`) es para quien ejecuta: ingeniería de datos, de IA o de ML. El perfil SA/TL suma lo que necesita quien lleva el diseño de la solución, la cuenta y la capacidad del equipo. No cambia la base: se instala aparte y cada skill sigue las reglas de `conventions.md`.

| | Ingeniero (base) | SA / TL (suma) |
|---|---|---|
| Skills | `harness/skills/` | `harness/skills-sa/` |
| Instalación | `install.ps1` / `install.sh --all` | el mismo comando con `-SA` / `--sa` |
| `config.toml [user].role` | `engineer` | `tl-sa` |

## Skills del perfil

| Skill | Para qué |
|---|---|
| `solution-design` | Documento de Diseño de Solución (.docx con marca DinoCloud), contrato de diseño que valida el cliente. |
| `team-allocation` | Asignaciones del equipo (Resource Planner o planilla), carga, vencimientos y diferencias con ClickUp. |
| `portfolio-update` | Update semanal de los proyectos en la lista de seguimiento de cuentas de ClickUp, con aprobación. |
| `team-mirror` | Espejo curado del proyecto para el equipo (solo lo técnico), en un repo de la org. |

Scripts de apoyo en `harness/scripts/`: `planner_mirror.py`, `allocations.py`, `team_mirror.py` (y `harness/tests/test_team_mirror.py`).

## Configuración

`harness/config.toml`, además de `[user]`. Los tokens no van acá: variable de entorno o archivo fuera de todo repo (ver "API directa o MCP" en `conventions.md`).

```toml
[planner]                  # Resource Planner por API, solo lectura (planner_mirror.py)
url        = ""            # URL base de la API del planner
token_file = "~/.config/dinocloud/planner.token"   # o variable RP_TOKEN

[allocation]               # respaldo: planilla "Resource Planner - Assignations", solo lectura
spreadsheet_id = ""
allowed_tabs   = ["Assignations", "Team", "Nomenclature"]   # el resto de la planilla nunca se lee
google_client_secret = "~/.config/claude-harness/google_client_secret.json"
token_path     = "~/.config/claude-harness/google_token.json"
ending_alert_days = 14

[portfolio]                # lista de seguimiento de cuentas y proyectos
list_id          = ""
health_field     = "Healt score"
semaphore_field  = "Semaforo"
closing_field    = "Real closing date"
scope_field      = "% scope complete"
risk_fields      = ["Risk Probability", "Risk Impact", "Risk Description", "Risk Actions"]
never_touch      = []      # columnas que la skill no toca
```

Por proyecto, en `project.toml`:

```toml
[allocation]
sheet_projects = []        # nombre o prefijo del proyecto en el Resource Planner; vacío = fuera de alcance

[portfolio]
account_task_id = ""       # tarea de la cuenta (milestone)
project_task_id = ""       # subtarea del proyecto: la que recibe el update semanal

[team_mirror]              # ver la skill team-mirror
repo    = "dinocloud/<cliente>-<proyecto>-team-context"
include = ["docs/architecture/", "docs/decisions/decisions.md"]
exclude = []
block   = []
```

## Convenciones del rol

- **Validación:** el SA/TL valida las tareas de diseño. La ejecución la valida otra persona del equipo (regla general en `conventions.md`, "Tareas en ClickUp: estructura").
- **El SA/TL no se asigna ejecución.** Las tareas de ejecución e implementación las toma el equipo; el SA/TL queda con diseño, revisión y validación, decisiones y lo propio del rol. Si igual ejecuta algo, se registra (horas, comentario), pero la tarea es de otro. Si aparece una tarea de ejecución a su nombre, se propone a quién pasarla, con OK antes de cambiarla.
- **Reasignar tareas:** primero una propuesta y después, con OK, el cambio en ClickUp. La propuesta es una tabla Tarea (con link) / Responsable propuesto / Subtareas nuevas (con su dueño) / Dependencias, armada así:
  1. listar las tareas abiertas de la persona y separar ejecución de lo propio del rol;
  2. elegir el responsable por quién ya lleva ese frente (sus tareas en ClickUp) y por su capacidad (`team-allocation`: carga, horas en el proyecto, fin de la asignación);
  3. lo que necesita a otra persona va como subtarea con su dueño; lo que ya es otra tarea, como dependencia;
  4. lo que ya está hecho se propone cerrar, no reasignar;
  5. avisar lo que aparezca: fechas que no cierran con sus dependencias, personas asignadas sin tareas o con tareas sin asignación, sobrecarga y asignaciones que vencen antes que las tareas.

## Asignaciones: copia central del planner

Una sola copia para todos los proyectos, en `~/claude-workspace/planner/` (`allocations.toon` + `.fetched_at`, fuera de git: cada PC la regenera). La genera `planner_mirror.py` con los proyectos activos de `projects.toon`: `py ~/claude-workspace/harness/scripts/planner_mirror.py [--project "Nombre"]`. Esquema: `allocations[N]{person,role,seniority,start,end,monthly_hours,billable,sheet_project,state}`, `load[N]{person,assigned_hours_all_projects,available_hours,load_pct}` y `absences[N]{person,start,end}`.

- Para leer asignaciones, primero esa copia, filtrando las filas cuyo `sheet_project` coincide con `project.toml [allocation].sheet_projects`. Se cae a `team-allocation` (planilla, `memory/allocations.toon`) si la copia no existe o tiene más de 8 días.
- Proyecto nuevo: cargar `sheet_projects` y correr la copia ad hoc. Sin `sheet_projects`, el proyecto no entra al alcance.
- El token actúa como el usuario con rol `team_lead`: solo lectura, sin tarifas. Vence; ante un 401 el usuario genera uno nuevo en el planner y lo guarda él (Claude no lo ve). El harness no escribe en el planner.
- No hay paso en `harness-run` para esto: se corre a mano o se agrega a la rutina `weekly` en la PC del SA/TL.

## Espejo del equipo

El repo del proyecto es privado y no se transfiere a la org. Lo que el equipo necesita se publica en un repo aparte de `dinocloud`, `<cliente>-<proyecto>-team-context` (skill `team-mirror`). Un hook `pre-push`, que se instala en cada PC, lo publica en cada push a `main`, desde el commit pusheado.

Complemento de "Información compartida y privada" en `conventions.md`:

1. `block` y `exclude` de `[team_mirror]` son la red de seguridad, no el método: el contenido compartido ya sale limpio de origen. Antes del primer `--dry-run` de un proyecto se revisan los archivos incluidos con las reglas de lo privado.
2. Lo que ya está en ClickUp no se reescribe ahí. Si una tarea del espejo trae datos privados (por ejemplo, emails del cliente), se excluye en `exclude`.
3. Si un pasaje privado tiene que quedar en un archivo compartible, la sección `## ...` se marca con `<!-- privado -->` (o el archivo entero, en sus primeras líneas): el espejo la quita al publicar.
4. **Revisión por LLM:** el espejo publica solo contenido aprobado por hash en `.harness/team-mirror-review.csv`. `team_mirror.py <proyecto> --review --model haiku` revisa lo nuevo o modificado; lo retenido queda con el motivo y se corrige en el origen. La aprobación a mano (`--approve`) es para binarios y falsos positivos, con OK del usuario.
5. Se corre `--review` después de las skills del día, se commitea el registro y se pushea; el hook publica lo aprobado.
