# Claude Workspace

> DinoCloud Internal - Confidential

Workspace personal con el **harness de contexto de proyectos**: skills, plantilla de proyecto, rutinas y memoria en git. Es general y sirve para cualquier proyecto. Los proyectos viven aparte, uno por repo, en `~/dino-projects/<proyecto>/`.

## Harness

| Ruta | Qué es |
|---|---|
| `harness/skills/` | Skills del harness (fuente). `install.ps1` (Windows) o `install.sh --skills` (macOS) las enlazan en `~/.claude/skills/`. |
| `harness/reference/` | `conventions.md` (reglas comunes), `toon.md` (formato y esquemas), `project-toml.md` (configuración de un proyecto), `perfil-sa.md` (lo que suma el perfil SA/TL). |
| `harness/config.toml` | Configuración personal (no se versiona): nombre, `role`, Slack, zona horaria, umbrales. Se crea desde `config.example.toml`. |
| `harness/bin/harness-run` | Rutinas `daily`, `weekly` y `friday` sobre los proyectos activos. |
| `harness/windows/`, `harness/launchd/` | Agenda de las rutinas en Windows y en macOS. |
| `harness/hooks/` | `session-start.sh` muestra el último status y avisa cierres pendientes; `session-end.sh` anota sesiones sin cierre; `guard.sh` y `guards.py` son las guardas (envíos, rutinas desatendidas, marca de confidencialidad). |
| `harness/scripts/` | OAuth de Google (`google-login.py`, `google_auth.py`), `harness_lint.py`, `related.py`, `session_close.py`, `apply_profile.py`, `install_hooks.py`, `aws_price.py`. |
| `harness/tests/` | Tests de las guardas y los scripts: `py -X utf8 -m unittest discover -s harness/tests`. |
| `harness/skills-sa/` | Skills del perfil SA/TL (`solution-design`, `team-allocation`, `portfolio-update`, `team-mirror`). Se instalan con `-SA` / `--sa`. Ver `harness/reference/perfil-sa.md`. |
| `harness/improvements.md` | Backlog de mejoras del harness (lo mantiene `harness-evolve`). |
| `templates/project/` | Plantilla que copia `project-new`. |
| `projects.toon` | Registro de proyectos: nombre, ruta, activo. |
| `docs/guia-harness.html` | Guía paso a paso para empezar. |

**Principio:** las skills, los scripts y la plantilla no tienen nada propio de un proyecto. Todo lo específico va en el `project.toml` de cada proyecto. Si una mejora solo sirve para un proyecto, va a ese proyecto.

**Al cambiar el harness:**

- Una tarea que se repite se convierte en skill: pedile a Claude que la cree en `harness/skills/<nombre>/SKILL.md`, con `description` y disparadores concretos.
- Probar la skill en un proyecto de prueba antes de usarla en uno real.
- Una skill que sirve a todo el equipo va en `harness/skills/`; una propia de un rol (SA/TL) va en `harness/skills-sa/`. Una guarda nueva lleva su test en `harness/tests/`.
- Anotar el cambio en `improvements.md` (estado `aplicada`).

## Reglas

- Sin credenciales, sin PII de clientes y sin código de clientes sin autorización. Los tokens de Google viven en `~/.config/claude-harness/`, nunca en el repo.
- Contenido de un cliente específico: confirmar el nombre y el alcance autorizado antes de documentarlo.
- `logs/` no se versiona.
- Trabajo de un proyecto: Claude se abre en `~/dino-projects/<proyecto>`; trabajo del harness, en `~/claude-workspace`. La auto memory se guarda por carpeta y no entra en git: ahí van solo preferencias personales y correcciones de forma de trabajo. Lo que es del proyecto (decisiones, responsables, pendientes, contexto) va al repo del proyecto. Si en una sesión fuera de un proyecto aparece algo de un proyecto, se anota en su repo, no en la memoria.
