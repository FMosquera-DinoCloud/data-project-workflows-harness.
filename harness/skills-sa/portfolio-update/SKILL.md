---
name: portfolio-update
description: "Update semanal (lunes) del estado de los proyectos en la lista de seguimiento de ClickUp [Gestión de cuentas][Delivery]: prepara para cada proyecto registrado el comentario de estado y los cambios de deadline, Healt score, Semaforo, % scope complete, riesgo, status y Real closing date, y los aplica en ClickUp solo con aprobación. Usar cuando se pida actualizar el estado de los proyectos o cuentas en ClickUp, el update de los lunes, el health score, el semáforo o la fecha de cierre de un proyecto."
---

# portfolio-update

Configuración personal: `~/claude-workspace/harness/config.toml [portfolio]`. Por proyecto: `project.toml [portfolio]`. Reglas comunes: `.../reference/conventions.md`.

Se actualiza la **subtarea del proyecto** (`project_task_id`). La tarea de la cuenta (`account_task_id`) solo recibe cambios si el proyecto la cierra o si el usuario lo pide.

## Modo preparar (desatendido los lunes, o a pedido)

Por proyecto, **sin escribir nada en ClickUp**:

1. **Estado actual en ClickUp:** `clickup_get_task(project_task_id, include=[custom_fields])` y `clickup_get_task_comments` (el último comentario sirve para no repetir lo mismo). Los IDs de las columnas se resuelven por nombre con `clickup_get_custom_fields(list_id)`; los nombres están en `config.toml`.
2. **Evidencia de la semana:** los `status/` de los últimos 7 días, `docs/00-overview.md`, `memory/risks.md`, `backlog.toon`, las decisiones nuevas y los hitos de `project.toml [[phases]]`.
3. **Qué se propone cambiar:**
   - **Comentario**: siempre. 2 a 4 líneas en español con el estilo de los comentarios anteriores: hechos, sin adjetivos. Qué se cerró, en qué se está, qué sigue y con qué fecha, y el bloqueo o riesgo si lo hay. Sin datos sensibles del cliente ni montos, y **sin referencias internas** (ids `T-`/`D-`/`A-`/`Ref`, archivos locales), según "Texto que sale del repo" en `conventions.md`.
   - **Deadline** (`due_date`): si está vacío, proponer el `end` de la fase final o el hito comprometido, con su fuente. Si el avance muestra que no se llega, proponer la fecha nueva con el motivo. Si la fecha sigue siendo válida, no se toca.
   - **Healt score**: según la rúbrica de abajo. Cambia solo si la evidencia lo justifica, y el motivo va en una línea.
   - **Semaforo**: Verde, Amarillo o Rojo. Tiene que ser coherente con la salud del último `project-status`.
   - **% scope complete**: tareas del camino crítico cerradas sobre el total, o el avance del backlog si no hay camino crítico. Se redondea a 5.
   - **Riesgo**: si en `memory/risks.md` hay un riesgo principal abierto, proponer `Risk Probability`, `Risk Impact`, `Risk Description` y `Risk Actions`. Si se cerró, proponer limpiarlos. Una asignación de `memory/allocations.toon` que vence antes del deadline, con trabajo pendiente de esa persona, también cuenta como riesgo.
   - **Status**: `in progress`, `blocked` (con bloqueo activo), `in review`, `completed`, etc. Solo valores de la lista.
   - **Real closing date**: solo cuando el proyecto terminó (entrega final aceptada o cierre formal). Es la fecha efectiva del cierre, con su fuente (reunión, mail). Va junto con status `completed`.
   - **Nunca** se tocan las columnas de `never_touch` (clasificaciones comerciales, contrato, etc.).
4. **Archivo** `status/portfolio-AAAA-Www.md` (va en el índice con `type=status` y tag `portfolio`):

```markdown
> **DinoCloud Internal - Confidential**
# Update de portfolio — <proyecto> — AAAA-Www
**Tarea:** [<nombre>](url) · **Estado:** pendiente de aprobación

## Comentario propuesto
<texto tal cual se va a publicar>

## Cambios propuestos
| Campo | Actual | Propuesto | Motivo / fuente |
|---|---|---|---|
(solo filas que cambian)
```

5. Hacer commit. En modo desatendido, `harness-run` avisa por DM que hay updates para aprobar.

## Modo aplicar (solo interactivo, siempre con aprobación)

1. Juntar los `status/portfolio-<semana>.md` pendientes de todos los proyectos activos y mostrar un resumen: por proyecto, el comentario y la tabla de cambios.
2. Pedir aprobación **por proyecto**. Se puede editar el texto o sacar un cambio antes de aprobar. Un "sí a todo" explícito aprueba todos los proyectos mostrados.
3. **Revalidar**: volver a leer la tarea. Si alguien la cambió desde que se preparó la propuesta, mostrar la diferencia y volver a pedir OK.
4. Aplicar lo aprobado:
   - el comentario, con `clickup_create_comment` sobre la tarea y sin notificar a todos (salvo que se pida);
   - `due_date`, `status` y los campos personalizados, con `clickup_update_task` (dropdown: UUID de la opción; labels: arreglo de UUIDs; date: `AAAA-MM-DD`; progress: `{"current":N}`).
5. Marcar el archivo como `aplicado AAAA-MM-DD HH:MM` (o `descartado`), con lo que quedó efectivamente, y hacer commit.

## Rúbrica de Healt score

| Valor | Cuándo |
|---|---|
| 100 | En fecha, sin riesgos abiertos, el cliente conforme. |
| 90 | En fecha. Alertas menores ya resueltas o sin impacto. |
| 80 | En fecha, con un riesgo abierto que tiene mitigación en curso. |
| 70 | El próximo hito está en riesgo (camino crítico atrasado o bloqueo de menos de una semana), pero es recuperable. |
| 50 | El hito se va a correr, hay bloqueo en el camino crítico o insatisfacción del cliente. Requiere acción del TL o del AM. |
| 30 | El proyecto está fuera de rumbo: replanificación o escalamiento necesario. |

Semaforo: Verde entre 90 y 100, Amarillo entre 70 y 80, Rojo en 50 o menos.

## Tareas de la lista sin proyecto registrado

Al preparar, listar las tareas abiertas de la lista asignadas al usuario que no están en ningún `project.toml` (por ejemplo, oportunidades o cuentas sin repo), solo con nombre, status y días sin actualizar. No se propone nada para ellas: sirve para decidir si conviene dar de alta el proyecto con `project-new`.
