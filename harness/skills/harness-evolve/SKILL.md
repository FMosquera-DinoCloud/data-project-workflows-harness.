---
name: harness-evolve
description: "Revisa cómo viene trabajando el usuario (sesiones de Claude Code, logs del harness, correcciones, pedidos repetidos) y propone skills nuevas o cambios a las existentes del harness, registrándolos en harness/improvements.md. Usar cuando se pida mejorar, revisar o evolucionar el harness o las skills, qué se podría automatizar, qué patrones se detectaron, o en la rutina semanal."
---

# harness-evolve

Backlog de mejoras: `~/claude-workspace/harness/improvements.md`. Principios del harness: `~/claude-workspace/harness/reference/conventions.md` y la sección "Principio" de `~/claude-workspace/CLAUDE.md`.

## Qué buscar (ventana: 7 días o desde la última revisión)

- **Pedidos repetidos** sin skill: el mismo tipo de pedido 3 o más veces (por ejemplo "armame el resumen para el cliente", "compará estas dos opciones de AWS").
- **Pasos manuales repetidos:** secuencias de tools o comandos que se repiten entre sesiones.
- **Correcciones:** el usuario corrigió lo mismo 2 o más veces (formato, tono, un campo que falta, una regla). Suele ser una regla que falta en una skill existente.
- **Skills que no se activaron** cuando debían: el pedido encajaba con la `description` y no se usó. Hay que mejorar la descripción.
- **Skills que fallan o se saltean:** errores en `logs/`, fuentes caídas repetidas en `.harness/run-status` o `state.toml`.
- **Fricción de permisos:** prompts de permiso repetidos para la misma tool en rutinas o skills.
- **Lecturas por MCP que convienen por API:** una skill o rutina que lee mucho volumen, pagina o repite la misma consulta todos los días. Se propone un script en `harness/scripts/` según "API directa o MCP" en `conventions.md`, con el token que haría falta y sus permisos mínimos.
- **Skills de proyecto para generalizar:** las de `<proyecto>/.claude/skills/` de cada proyecto activo. Si una resuelve algo que otro proyecto también necesita, o se copió entre proyectos, se propone llevarla al harness (sacándole lo específico a `project.toml`).

## Fuentes

- `~/.claude/projects/*/*.jsonl` de la ventana: solo mensajes del usuario y nombres de tools usadas. No se copia contenido de clientes a `improvements.md`: se describe el patrón.
- `~/claude-workspace/logs/`, `.harness/run-status` y `state.toml` de cada proyecto activo.
- `git log` de los proyectos: commits manuales que repiten lo que haría una skill.

## Salida

Agregar al final de `improvements.md`, sin reordenar lo anterior, una entrada por hallazgo:

```markdown
## <título corto>
- **Detectado:** AAAA-MM-DD · **Tipo:** skill nueva | mejora a <skill> | descripción | permisos | bug
- **Patrón:** qué se vio y cuántas veces (fechas o sesiones)
- **Propuesta:** qué se crearía o cambiaría, en 1-3 líneas
- **Beneficio:** qué ahorra o qué evita
- **Estado:** propuesta
```

- Antes de agregar, ver si ya hay una entrada igual. Si la hay, sumar la evidencia a esa entrada.
- **No se implementa nada.** Los cambios se hacen con el OK del usuario. Al hacerlos, la entrada pasa a `aplicada (commit)` o `descartada (motivo)`.
- Una propuesta nunca agrega un caso especial para un proyecto: si algo es de un solo proyecto, va a su `project.toml` o a su `CLAUDE.md`.
- En modo interactivo, presentar las propuestas nuevas ordenadas por beneficio, en una línea cada una.
- Commit en `claude-workspace`: `harness(evolve): <N> propuestas`.
