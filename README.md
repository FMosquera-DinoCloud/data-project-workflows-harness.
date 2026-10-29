# claude-harness

> DinoCloud Internal - Confidential

Harness de Claude Code para el equipo de Data & AI: skills, plantilla de proyecto, rutinas y memoria en git. Cada proyecto tiene su propio repo de conocimiento (reuniones, decisiones, backlog, diagramas, reportes) que hereda quien entra al proyecto.

La guía completa, con los recorridos para Data Engineer, AI Engineer y ML Engineer, está en [`docs/guia-harness.html`](docs/guia-harness.html). Descargala y abrila en el navegador.

## Empezar

```bash
git clone https://github.com/JuanMartinezDinoCloud/claude-harness.git ~/claude-workspace
```

**Windows** (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File ~\claude-workspace\harness\install.ps1 -Diagrams
```

**macOS:**

```bash
bash ~/claude-workspace/harness/install.sh --all          # con --sa para el perfil SA/TL
bash ~/.claude/skills/aws-diagram/setup.sh
```

Después:

1. Completá `harness/config.toml` (`[user]`: nombre, mail, `role = "engineer"`, ID de Slack).
2. En claude.ai, conectá Calendar, Gmail, Drive, Slack, ClickUp y GitHub.
3. Abrí Claude Code en `~/dino-projects` y pedí: *"dá de alta el proyecto `<tu-proyecto>` en el harness"*.
4. Opcional: rutinas con `harness\windows\install-tasks.ps1` (Windows) o `install.sh --launchd` (macOS), y la API de Google según la guía.

Diagnóstico: `install.ps1 -Status` o `install.sh --status`.

## Skills

| Skill | Para qué |
|---|---|
| `project-new` | Alta de un proyecto con la plantilla y su repo privado en la org. |
| `project-ingest` | Reuniones, mails y canales → resumen, decisiones y action items. |
| `project-status` | Status del día: mis tareas, alertas, qué atender. |
| `daily-report` | Mi update para la daily (HTML + texto para pegar). |
| `backlog` / `task-writer` | Backlog interno y tareas orientadas a objetivo. |
| `aws-diagram` | Diagramas de arquitectura AWS como código, con íconos oficiales. |
| `google-api` | Leer y editar Docs, Sheets y archivos de Drive. |
| `estimate` | Estimaciones de tres puntos con ajuste por IA. |
| `drive-mirror` | Espejo local de la carpeta de Drive del proyecto. |
| `aws-radar` | Novedades de AWS cruzadas con tus proyectos. |
| `project-consolidate` | Compacta el contexto viejo en la memoria del proyecto. |
| `weekly-hours` | Prepara la carga de horas de la semana. |
| `pr-brief` | Descripción de una PR para quien la valida: criterio que resuelve, decisiones, dónde mirar, evidencia. |
| `task-review` | Revisa como validador el entregable de una tarea contra sus criterios y el diseño vigente. |
| `session-close` | Cierre de sesión: resumen, horas sin registrar, commit y push. |
| `harness-evolve` | Detecta patrones y propone skills nuevas en `improvements.md`. |

Además, el harness trae guardas determinísticas (hooks que bloquean envíos con credenciales, escrituras de las rutinas sin supervisión y archivos sin la marca de confidencialidad), `harness_lint.py` y tests. `install.ps1` / `install.sh --hook` los registran.

### Perfil SA / TL

Las skills de quien lleva el diseño y la cuenta (`solution-design`, `team-allocation`, `portfolio-update`, `team-mirror`) están aparte, en `harness/skills-sa/`, y no se instalan por defecto. Para sumarlas: `install.ps1 -SA` o `install.sh --skills --sa`, y `role = "tl-sa"` en `config.toml`. Detalle en [`harness/reference/perfil-sa.md`](harness/reference/perfil-sa.md).

Este repo es la base. Tu harness es tuyo: forkealo o trabajalo en tu clon, y sumá las skills de tus tareas repetitivas.
