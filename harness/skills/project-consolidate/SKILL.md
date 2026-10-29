---
name: project-consolidate
description: "Consolida la memoria de un proyecto: comprime reuniones y digests viejos en memory/ y en el overview, cierra preguntas resueltas, marca lo obsoleto y limpia el índice. Usar cuando se pida actualizar el overview, resumir lo que pasó en el proyecto, compactar o limpiar contexto, o en la rutina semanal."
---

# project-consolidate

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`. Umbral: `config.toml [policy].consolidate_after_days` (por defecto 14).

Es la etapa de "olvido": el objetivo es que el contexto útil quepa en pocos archivos, sin perder decisiones ni compromisos.

## Pasos

1. **Candidatos:** archivos de `context/meetings/` y `context/digest/` con fecha anterior al umbral y sin tag `consolidado` en `index.toon`. Además, siempre se leen los `status/`, las decisiones `D-NNN` y los digests de los últimos 7 días para `risks.md` y `timeline.md`: esos dos archivos no esperan al umbral. Si `risks.md` o `timeline.md` solo tienen encabezado, se completan desde lo vigente aunque no haya candidatos.
2. **Extraer hacia `memory/`** (con fecha y link a la fuente en cada ítem):
   - `people.md`: personas nuevas, cambios de rol, quién decide qué, preferencias de comunicación (sin PII de externos).
   - `risks.md`: riesgos nuevos, cambios de severidad y riesgos cerrados (se tachan, no se borran).
   - `open-questions.md`: preguntas nuevas. Las respondidas se marcan con la respuesta y la fuente.
   - `timeline.md`: hitos, entregas, cambios de alcance, una línea por evento.
3. **Overview** (`docs/00-overview.md`): reescribir siempre, aunque no haya candidatos, el encabezado (fuente y fecha: nunca "exportado de Notion" una vez que `backlog/` y `docs/` son la fuente) y las secciones "Estado actual", "Próximos hitos" y "Riesgos principales" con lo vigente, y actualizar la fecha. Máximo una pantalla.
4. **Decisiones:** comprobar que toda decisión de los candidatos tenga su `D-NNN`. Si falta, registrarla. Comprobar también que cada `D-NNN` de `decisions.md` y de la bitácora tenga su fila en `index.toon`; si falta, agregarla.
5. **Action items:** los que no quedaron en el backlog ni en ClickUp pasan como propuesta al digest de hoy, para que lo decida quien lleva el proyecto.
6. **Marcar:** en `index.toon`, agregar el tag `consolidado` a cada candidato y dejar su `summary` como la línea más útil. Los archivos **no se borran**; quedan en git y en el índice.
7. **Memoria gruesa:** si `docs/decisions/decisions.md` supera las ~400 líneas, mover las decisiones reemplazadas a `docs/decisions/archive.md` y dejar en su lugar una línea con el link.
8. Si no había nada que consolidar, dejarlo dicho en una línea del log ("consolidate: sin candidatos") en vez de salir en silencio.
9. `state.toml [last].consolidate`, `index.toon`, commit `harness(consolidate): <N> archivos consolidados`.

## Criterio

Si una información no cambiaría ninguna decisión futura, no pasa a `memory/`. En la duda, se deja la línea con el link a la fuente.
