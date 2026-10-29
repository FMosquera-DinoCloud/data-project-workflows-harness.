---
name: team-mirror
description: "Crea y mantiene el espejo curado de un proyecto para el equipo: un repo en la org de DinoCloud con solo lo técnico ya procesado (diseño, decisiones técnicas, copia de ClickUp), publicado desde el repo privado del proyecto después de controles estáticos y una revisión de confidencialidad con un LLM. Nunca reuniones, digests, status, horas, memoria ni nada sensible. Usar cuando se pida compartir el contexto del proyecto con el equipo, crear o configurar el repo del equipo, publicar o actualizar el espejo, revisar o aprobar contenido retenido, cambiar qué se publica, o ver por qué el espejo no se actualizó."
---

# team-mirror

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md` (sobre todo "Información compartida y privada"). Script: `~/claude-workspace/harness/scripts/team_mirror.py`. Configuración: `project.toml [team_mirror]`. Registro de revisión: `.harness/team-mirror-review.csv` (commiteado en el repo privado).

El repo del proyecto (privado) es la fuente. El espejo es un repo aparte en la org `dinocloud` que lee toda la org y escribe solo el usuario. Si el repo del proyecto vive en una cuenta personal, no se transfiere a la org: en una transferencia se pierde el rol admin y el historial completo queda a la vista de todos.

## Qué se publica

Solo lo técnico y de alcance, ya procesado: `docs/architecture/`, `docs/decisions/decisions.md` y, si el proyecto la tiene, la copia de ClickUp (`clickup/`). **Nunca**: reuniones, `context/digest/`, `status/`, `time/`, `memory/`, `project.toml`, `estimations/`, `reports/`, `.harness/` (salvo el registro), `CLAUDE.md`, `drive/`.

Lo privado no se escribe en lo compartible (regla de `project-ingest` y "Información compartida y privada"). Si una decisión o pasaje privado ya está en un archivo compartible, se marca la sección con `<!-- privado -->` y el script la quita al publicar.

## Controles antes de publicar (en el script, sobre el commit, nunca sobre la copia de trabajo)

1. **Privado:** archivo con `<!-- privado -->` en sus primeras 5 líneas no sale; sección `## ...` marcada se quita.
2. **1 a 1:** una reunión con dos participantes o menos no sale (red de seguridad si alguna vez se incluyen reuniones).
3. **Términos bloqueados:** lista fija (1 a 1, RR. HH., comercial) + `block` del proyecto, como palabra completa. Si aparecen, no se publica nada.
4. **Revisión por LLM:** solo sale el contenido cuyo hash está aprobado en el registro. Lo nuevo o modificado queda retenido hasta que `--review` (Haiku, en la rutina diaria) lo aprueba. Lo que el LLM retiene queda con el motivo en el registro. Los binarios solo se aprueban a mano (`--approve`).

## Crear el espejo (una vez por proyecto, interactivo)

1. **Repo en la org, creado por el usuario** (quien lo crea queda admin): `gh repo create dinocloud/<cliente>-<proyecto>-team-context --private --add-readme`. Verificar `permissions.admin = true` con `gh api repos/dinocloud/<cliente>-<proyecto>-team-context --jq .permissions`.
   - **Nombre:** `<cliente>-<proyecto>-team-context`, en minúsculas y con guiones. `<proyecto>` es el nombre corto del proyecto según el SOW. Ejemplo: `truefire-transcription-mvp-team-context`.
2. **Solo el admin escribe:** ruleset sobre todas las ramas (`~ALL`) con `creation`, `update`, `deletion` y `non_fast_forward`, y bypass solo para el rol admin (`RepositoryRole` id 5). Sin protección clásica de rama, porque choca con el ruleset.
3. **Configuración** en `project.toml`:
   ```toml
   [team_mirror]
   repo    = "dinocloud/<cliente>-<proyecto>-team-context"
   include = ["docs/architecture/", "docs/decisions/decisions.md", "clickup/tasks.toon", "clickup/tasks/"]
   exclude = []
   block   = []          # términos propios del proyecto: canal de cuenta, equipo comercial, etc.
   ```
4. **Decisiones privadas:** revisar `decisions.md` y marcar con `<!-- privado -->` las de staffing, comerciales, de relación con la cuenta o de personas (o moverlas a `memory/privado/decisiones.md`).
5. **Revisión inicial:** `team_mirror.py <proyecto> --review`; mostrar al usuario lo retenido y corregir el contenido (no forzar). Binarios: `--approve <rutas>` con OK del usuario.
6. **Hook:** `team_mirror.py <proyecto> --install-hook` en **cada PC** donde se pushea el proyecto (el hook vive en `.git/hooks` y no viaja con el repo).
7. Commit del registro y push: el hook publica.

## Funcionamiento diario

- `--review` se corre después de las skills del día (a mano, o desde la rutina si el SA/TL la agrega); se commitea el registro y se pushea, y el hook publica lo aprobado.
- En una sesión interactiva, un push publica solo lo ya aprobado; lo nuevo espera a la rutina o a `--review` a mano.
- `--dry-run` muestra qué sale, qué está pendiente (con el motivo si fue retenido) y qué quedó fuera por privado.

## Resolver lo retenido

Abrir el motivo en el registro, corregir el archivo de origen (reescribir, marcar `<!-- privado -->` o mover a `memory/privado/`) y volver a correr `--review`. Aprobar a mano (`--approve`) solo con OK explícito del usuario y cuando el motivo es un falso positivo.

## Qué no hace

- No da accesos ni cambia permisos de la org.
- No reescribe historia del espejo. Si algo sensible llegó a publicarse, se avisa al usuario: sacarlo del contenido actual no lo saca del historial.
