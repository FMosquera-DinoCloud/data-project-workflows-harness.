---
name: backlog
description: "Gestiona el backlog interno de un proyecto (backlog/backlog.toon): agregar, editar, cerrar, priorizar y vincular tareas con ClickUp, y aplicar las propuestas que dejó la ingesta. Usar cuando se pida anotar, agregar, mover, cerrar, repriorizar o listar tareas propias del proyecto, revisar propuestas de backlog, o subir una tarea a ClickUp."
---

# backlog

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md` y `toon.md`. Redacción de tareas: skill `task-writer` (obligatoria).

## Operaciones

- **Agregar**:
  1. Redactar la tarea con `task-writer`.
  2. Asignarle el próximo `T-NNN` libre.
  3. Agregar la fila en `backlog.toon` (actualizar `[N]`) y el bloque en `notes.md`.
  4. Calcular `priority` con la regla de prioridad.
- **Editar o cerrar**: reescribir la fila, actualizar `updated` y anotar en `notes.md` una línea con fecha y motivo. `done` y `dropped` no se borran.
- **Listar**: por defecto, lo abierto ordenado por prioridad y fecha, en una tabla corta. Se puede filtrar por owner, fase o estado.
- **Priorizar**:
  1. Recalcular todas las abiertas con la regla bloqueos → fecha → camino crítico.
  2. Mostrar solo lo que cambió, con el motivo.
  3. Escribir con OK.
- **Aplicar propuestas**:
  1. Juntar las `## Propuestas` de los digests desde la última aplicación (buscar en `index.toon` los digests con tag `propuesta`).
  2. Presentarlas numeradas: aplicar, editar o descartar cada una.
  3. Aplicar solo lo aprobado y marcar en el digest `✔ aplicada T-NNN` o `✘ descartada`.
- **Subir a ClickUp** (siempre con OK explícito, mostrando antes el contenido):
  1. Revisar duplicados y consistencia contra las tareas de ClickUp (`clickup_filter_tasks`) y el backlog interno, y elegir la épica, como dice `task-writer`.
  2. Crear la tarea con `clickup_create_task` en la lista de `project.toml [clickup].list_id` (o preguntar la lista), con `parent` = la épica. La descripción es el bloque de `task-writer`.
  3. Cargar sus dependencias con `clickup_add_task_dependency`.
  4. Guardar el id devuelto en `clickup_id`.
  5. No usar `technical-story` ni `tech-redactor`: sugieren implementación y chocan con `task-writer`.
- **Sincronizar estado**: en las tareas con `clickup_id`, si el estado de ClickUp difiere, proponer actualizar el interno. Nunca al revés sin OK.

## Cierre

Actualizar `index.toon` (`backlog/backlog.toon` y `backlog/notes.md`) y hacer commit `harness(backlog): <qué cambió>`.
