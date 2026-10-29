---
name: daily-report
description: "Arma el reporte HTML para llevar a la daily del equipo: una tarjeta por colaborador con los temas para hablar hoy (con link a la tarea o al documento) y el estado de sus tareas según ClickUp, para darle seguimiento a cada uno. Después de la daily lo actualiza con lo que se acordó. Usar cuando se pida un reporte, resumen o agenda para la daily, los pendientes por persona para la reunión, el seguimiento del equipo en la daily, o actualizar el reporte con lo que salió en la daily. Use for daily standup agenda/report per team member with ClickUp status."
---

# daily-report

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`. Configuración: `project.toml` del proyecto (equipo, ClickUp, zona horaria en `config.toml`).

Con `config.toml [user].role = "engineer"` aplica la sección **Modo ingeniero** del final. Con `tl-sa`, es la agenda de la daily, no el status: `project-status` prioriza el día del usuario; este reporte le sirve al usuario para recorrer al equipo persona por persona y se puede compartir en pantalla.

## Entradas

1. **Último status** (`status/AAAA-MM-DD.md` de hoy si existe; si no, el último) y el cierre de sesión más reciente en `status/`: pendientes, alertas, vencidas.
2. **ClickUp:** `clickup_filter_tasks` con `list_ids`/`folder_ids` de `project.toml`, `include_closed: true`, `order_by: updated`. Si `has_more`, seguir paginando. Por tarea: nombre, estado, asignados, `date_updated`, `due_date`, `parent`. Las fechas se pasan a la zona horaria de `config.toml` (`dd/mm`).
3. **Contexto reciente:** digests y reuniones desde la última daily (buscar en `index.toon`), decisiones nuevas en `docs/decisions/`, propuestas de backlog sin aplicar.
4. Lo que el usuario pida en la conversación ("recordame decirle a X…", "agregá Y para la daily"): va como tema en la tarjeta de esa persona.

## Qué entra

- **Una tarjeta por persona** del equipo con algo para hablar o con tareas abiertas. Personas que trabajan juntas en el mismo frente pueden ir en una tarjeta (`"Ana · Bruno"`). El usuario va último.
- **"Para hablar hoy"** (checklist): pedidos concretos a esa persona. Cada ítem tiene:
  - `title`: la acción en una línea ("Sacar el campo X del esquema", "Confirmar que la prueba incorporó los ajustes").
  - `why`: el contexto mínimo para que se entienda en la reunión sin abrir nada (qué falta, por qué importa, qué frena). Si el usuario pregunta "¿qué era esto?", el `why` estaba corto: ampliarlo con **Qué es / Para qué / Quién**.
  - `links`: la tarea de ClickUp o el documento (Drive, notas de reunión) que el ítem referencia. Siempre que exista, link.
  - `status`: el estado en ClickUp de la tarea principal del ítem, si la hay.
- **"En qué está según ClickUp"** (tabla): tareas de la fase actual o del sprint que estén abiertas o se hayan movido en la última semana. Fuera: tareas de implementación con fecha lejana, las `[Borrar]` y las cerradas hace más de una semana. Subtareas con `↳` debajo de su padre. Columna `note` solo cuando aporta: `Vencida (dd/mm)`, `Vence hoy`, `Sin movimiento desde el dd/mm` (más de `stale_task_days`), `En review desde…`, `Nueva hoy`, o una inconsistencia ("marcada completa pero falta X").
- **Cabecera:** próximos hitos con fecha (de `project.toml [[phases]]` o del status), links a los documentos centrales y la hora de la foto de ClickUp.

## Reglas de texto

- El reporte se muestra al equipo: **sin IDs internos** (D-xx, T-xxx, A-xx, Ref xx), sin rutas locales ni nombres del harness. Los nombres de tareas, tal como figuran en ClickUp.
- Detectar y marcar inconsistencias entre ClickUp y la realidad (completa con pendientes abiertos, en review algo ya incorporado, bloqueada sin motivo visible): son los mejores temas para la daily.
- No crear tareas ni cambiar estados en ClickUp para armar el reporte. Si un tema necesita una tarea que no existe, se dice en el reporte ("no tiene tarea ni dueño") y se propone al usuario; se crea solo con su OK.

## Salida

1. Datos en `reports/daily-AAAA-MM-DD.json` (formato abajo). Arrancar copiando el JSON de la daily anterior si existe y actualizar: estados, temas resueltos fuera, temas nuevos adentro.
2. HTML: `py ~/claude-workspace/harness/skills/daily-report/render.py reports/daily-AAAA-MM-DD.json reports/daily-AAAA-MM-DD.html` (en Mac `python3`).
3. Abrirlo: en Windows `start "" <html>`; en Mac `open <html>` lo corre el usuario si el sandbox lo bloquea.
4. `index.toon` (una fila por el HTML) + commit `harness(status): reporte para la daily del dd/mm` + push.

```json
{
  "title": "Daily <Proyecto> d/m",
  "heading": "Daily <Proyecto> — lunes d/m",
  "subtitle": "Pendientes por persona y estado de sus tareas en ClickUp. Foco: …",
  "milestones": [{"label": "Mar 6/10", "text": "checkpoint de F2"}],
  "doc_links": [{"label": "Documento de arquitectura", "url": "https://…"}],
  "status_asof": "5/10 10:20",
  "footnote": "Tareas de la fase abiertas o movidas en la última semana. Los checks son solo de esta pantalla.",
  "people": [
    {"name": "Nombre", "role": "Frente que lleva",
     "talk": [{"title": "Acción (admite <code>/<b>)", "why": "Contexto", "status": "in review",
               "links": [{"label": "Tarea", "url": "https://app.clickup.com/t/…"}]}],
     "tasks": [{"id": "86e3…", "name": "Nombre en ClickUp", "status": "in progress", "updated": "05/10", "note": "Vence hoy"}]}
  ]
}
```

`id` arma el link con `task_url_base` (por defecto `https://app.clickup.com/t/`); para algo que no es de ClickUp, `url`.

## Después de la daily

Cuando el usuario lo pida (o pida "tomar el transcript de la daily"):

1. Bajar las notas de Gemini del evento de hoy (`list_events` → adjunto "Notas de Gemini" → `read_file_content`) y registrarlas como hace `project-ingest` (reunión en `context/meetings/`, decisiones nuevas en `docs/decisions/`).
2. Contrastar con el reporte: qué quedó resuelto (marcarlo `completed` en el JSON con "resuelto" en el título y la fuente en `why`), qué cambió y qué action items nuevos no tienen tarea. Avisar si un action item de las notas duplica algo que ya está en otra tarea.
3. Re-renderizar, commitear y resumir al usuario qué cambia respecto del reporte.

## Modo ingeniero (`config.toml [user].role = "engineer"`)

Es mi update para la daily, no la agenda del equipo. Una sola tarjeta (`people` con un elemento: el usuario), con:

- **`talk`** en tres bloques, cada ítem con link: **Ayer** (tareas de ClickUp que movió, commits y PRs de los repos de `[github]` con autor = el usuario, decisiones que registró), **Hoy** (las 3 primeras de "Mis tareas" del status) y **Bloqueos** (qué necesita y de quién). El bloque va como prefijo del `title`: "Ayer · …", "Hoy · …", "Bloqueo · …".
- **`tasks`**: solo sus tareas abiertas o movidas en la última semana.
- **Texto para pegar:** además del HTML, `reports/daily-AAAA-MM-DD.txt` con las tres listas en texto plano (máximo 8 líneas), listo para Slack o para leer en la reunión.
- **Después de la daily:** lo mismo que arriba, pero solo los action items que son del usuario.
