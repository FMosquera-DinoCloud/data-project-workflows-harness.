# CLAUDE.md — {{NAME}}

> **DinoCloud Internal - Confidential.**

Cliente: {{CLIENT}} · {{DESCRIPTION}} · Owner técnico: {{OWNER}}. La configuración del proyecto (fuentes, canales, equipo, fases) está en `project.toml`. El estado vigente está en `docs/00-overview.md`.

Este proyecto usa el harness de `~/claude-workspace`. Las reglas comunes están en `~/claude-workspace/harness/reference/conventions.md`.

## Cómo encontrar información

Ante cualquier pedido, **buscá primero en `index.toon`**: grep por palabra clave, persona o id (`T-012`, `D-004`). Después abrí solo los archivos que correspondan. No leas carpetas enteras. Para traer todo lo relacionado con un tema, id o palabra, correr `py -X utf8 ~/claude-workspace/harness/scripts/related.py <proyecto> <consulta>` (tarea, ClickUp, decisiones y fuentes en una salida).

Orden de carga, de más barato a más caro:

1. `docs/00-overview.md`: estado, fase, riesgos y próximos hitos.
2. `status/`: el último archivo es el update del día.
3. `backlog/backlog.toon`: nuestras tareas, con estado y prioridad. El detalle de cada una está en `backlog/notes.md` (`grep -A15 "## T-NNN"`).
4. `docs/decisions/decisions.md`: decisiones `D-NNN`. Se busca por id; no se lee entero.
5. `memory/`: personas, riesgos, preguntas abiertas y línea de tiempo consolidadas.
6. `context/meetings/` y `context/digest/`: lo reciente de reuniones y canales.
7. `drive/`: espejo de solo lectura de la carpeta de Drive del proyecto.
8. `docs/diagrams/` (diagramas como código) y `reports/` (reportes HTML).

## Situación → skill

Skills propias del proyecto: `.claude/skills/` (se listan también en esta tabla).

| Si el pedido es… | Skill |
|---|---|
| crear, redactar o reescribir una tarea, ticket o historia | `task-writer` (+ `backlog`) |
| ver, priorizar o cambiar nuestras tareas | `backlog` |
| ponerse al día con reuniones, mails o canales | `project-ingest` |
| estado del proyecto, qué hace cada persona, qué está trabado | `project-status` |
| agenda o reporte para la daily, pendientes por persona para la reunión | `daily-report` |
| traer o actualizar archivos de Drive, o subir un cambio a Drive | `drive-mirror` |
| compactar contexto viejo o actualizar el overview | `project-consolidate` |
| revisar o validar el entregable de una tarea (doc, PR, IaC) | `task-review` |
| abrir o actualizar una PR, o armar su descripción | `pr-brief` |
| cerrar la sesión de trabajo (resumen, horas, commit y push) | `session-close` |
| cargar o preparar horas en ClickUp | `weekly-hours` |
| estimar esfuerzo | `estimate` |
| novedades de AWS relevantes | `aws-radar` |
| diagrama de arquitectura | `aws-diagram` |
| leer o editar un Google Doc, Sheet o .docx, o subir un archivo a Drive | `google-api` |
| una tarea que se repite, o una skill que se puede mejorar | `harness-evolve` |

## Fuentes de verdad

- **Nuestras tareas:** `backlog/`. Toda tarea se escribe con `task-writer`: objetivo, no implementación.
- **Ejecución del equipo:** ClickUp (ver `project.toml [clickup]`). Se lee siempre; solo se escribe con aprobación.
- **Documentos compartidos:** Drive. `drive/` es un espejo local; cualquier cambio en Drive se hace con aprobación.
- **Decisiones:** `docs/decisions/decisions.md`.

## Reglas

- Sin credenciales ni PII en este directorio. Personas externas: nombre y rol.
- Texto para otras personas (ClickUp, Drive, mail, Slack, cliente o equipo): sin ids internos (T-, D-, A-, H-, Ref) ni archivos locales; el fundamento va en palabras.
- Los archivos de `drive/` no se editan a mano: para cambiar algo en Drive se usa `drive-mirror`.
