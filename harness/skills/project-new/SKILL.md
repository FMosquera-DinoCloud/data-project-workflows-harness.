---
name: project-new
description: "Crea un proyecto nuevo con el harness de contexto: estructura de carpetas, project.toml, CLAUDE.md, índice, backlog y git. Usar cuando se pida dar de alta, arrancar, inicializar o preparar un proyecto nuevo en ~/dino-projects, o sumar un proyecto existente al harness."
---

# project-new

Plantilla: `~/claude-workspace/templates/project/`. Registro: `~/claude-workspace/projects.toon`. Convenciones: `~/claude-workspace/harness/reference/conventions.md`. Esquema de configuración: `.../reference/project-toml.md`.

## Pasos

1. **Datos mínimos** (preguntar todos juntos, una vez):
   - nombre (slug en minúscula con guiones), cliente, descripción de una línea, owner técnico;
   - confirmación del cliente y del **alcance autorizado** para procesar su material en este entorno (política DinoCloud). Sin confirmación, `scope_confirmed = false`.
2. **Crear** `~/dino-projects/<slug>/` copiando la plantilla (incluye `.harness/`, `.gitignore` y `.gitattributes` con `eol=lf`) y reemplazar `{{NAME}}`, `{{CLIENT}}`, `{{DESCRIPTION}}`, `{{OWNER}}` y `{{DATE}}` en `CLAUDE.md`, `project.toml` y `docs/00-overview.md`.
   - Si el directorio ya existe con contenido: no pisar nada. Agregar solo lo que falta y mostrar la lista antes de escribir.
3. **Fuentes.** Proponer valores para `project.toml` buscándolos con los conectores (solo lectura):
   - Drive: carpeta con el nombre del proyecto o del cliente → `folder_id`.
   - ClickUp: `clickup_search` con el nombre → folder y lista.
   - Slack: `slack_search_channels` con el nombre → canales internos y Slack Connect.
   - Calendar: títulos de eventos recurrentes de las últimas 2 semanas → `match`.
   - Gmail: armar un `query` que no traiga notificaciones.
   - Preguntar por canales sin conector: WhatsApp (solo se registra), Teams, Google Chat.
   Mostrar lo encontrado en una tabla y escribir solo lo que el usuario confirma.
4. **Equipo y fases:** pedir o inferir de ClickUp (asignados) las personas y roles; las fases e hitos, del SOW o PRD si existe (`prd-generator`, `sow-evaluator`).
5. **Skills de plugins:** por defecto el proyecto arranca solo con las skills del harness; los grupos de `config.toml [plugin_groups]` (code, iac, setup) se activan a pedido. Correr `py -X utf8 ~/claude-workspace/harness/scripts/apply_profile.py <dir> --list`, mostrar qué grupos sugiere el repo (SUGERIDO) y preguntar cuáles activar, recomendando los sugeridos. Aplicar con `--groups <lista>` (puede ser ninguno). Cada skill activa cuesta ~100-200 tokens por sesión.
6. **Git:** `git init`, primer commit `harness(project-new): alta de <slug>`. Remoto: con OK del usuario, `gh repo create dinocloud/<slug>-harness --private --source . --push`. El repo de conocimiento va **privado en la org de DinoCloud**, nunca en una cuenta personal: es lo que hereda quien entre al proyecto (KT). Si el proyecto ya tiene repo de conocimiento, `git clone` en lugar de crear.
7. **Registrar** en `projects.toon`: fila `<slug>,~/dino-projects/<slug>,true` (actualizar `[N]`).
8. **Indexar:** filas en `index.toon` para los archivos iniciales.
9. **Cierre:** correr `harness_lint.py <dir>` y dejar el resultado limpio; decir qué quedó configurado, qué fuentes faltan y que la primera ingesta puede correrse ya con `project-ingest` (ventana de 7 días) o esperar a la corrida diaria.

## No hacer

- No inventar IDs: todo `folder_id`, `list_id` o `id` de canal sale de una respuesta de conector.
- No copiar material del cliente en esta etapa; eso lo hace `project-ingest`.
