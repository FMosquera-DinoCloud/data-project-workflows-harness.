---
name: pr-brief
description: "Arma la descripción de una PR para quien la valida: qué criterio de la tarea resuelve, qué se implementó contra el diseño de solución con un diagrama del flujo que toca, las decisiones que tomó la implementación, los valores provisionales, dónde mirar y la evidencia de que funciona. Usar siempre que se abra, prepare o actualice una PR en un repo de proyecto, o cuando se pida la descripción, el resumen o la guía de revisión de una PR."
---

# pr-brief

Con el código escrito por agentes, el revisor ya no lee el diff línea por línea. Lo que necesita es entender **qué se resolvió, qué se decidió en el camino y dónde mirar**. Esta skill arma esa descripción, en markdown dentro de la PR. Del otro lado está `task-review`, que valida partiendo de ella. Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`.

## Principios

- **Para el validador, no para el autor.** El validador es el dueño del área: el que figura en la tarea del tracker o, si no hay, el que pidió el usuario. Se escribe con su vocabulario y se pone arriba lo que él tiene que decidir.
- **Lo que importa revisar son las decisiones, no el código.** Todo lo que la implementación resolvió y que el diseño no decía va explícito. Un desvío del diseño se marca como desvío, nunca se esconde en el diff.
- **Nada sin verificar.** Cada afirmación sale del diff, de los tests que corrieron o de una corrida real. Si algo no se probó, se dice.
- **Corto.** Que se lea en 3 a 5 minutos. El detalle va en secciones plegables.
- **Idioma:** el que diga el proyecto (`project.toml` o su CLAUDE.md). Si no dice nada, español.
- **Título de la PR:** en el mismo idioma que la descripción. Si el cliente habla español, el título va en español aunque el repo, el código o los commits estén en inglés. Corto, y dice el resultado, no la implementación (por ejemplo "v1: timecode del master y archivo de recorte (EDL)").

## 1. Juntar

1. **El diff:** `gh pr diff` o `git diff <base>...HEAD`, más la lista de archivos y los commits.
2. **La tarea** que resuelve, desde el tracker del proyecto: sus criterios de aceptación, las restricciones y el validador. Si la PR no tiene tarea, preguntar cuál es antes de escribir.
3. **El diseño vigente:** la sección del documento de diseño que corresponde y las decisiones del proyecto (`docs/decisions/`) que aplican. Buscar primero en `index.toon`.
4. **La evidencia:** salida de los tests, el `verify` del módulo y, si hubo, la corrida real (salidas de ejemplo, tiempos, costo).

## 2. Escribir la descripción

Plantilla (las secciones vacías se omiten):

````markdown
## Qué resuelve
<1 a 3 líneas: el resultado, en términos del producto.>
Tarea: [<nombre en el tracker>](<link>) · Valida: <persona>
- [x] <criterio de la tarea que esta PR cumple>
- [ ] <criterio que queda para otra PR, y cuál>

## Qué se implementó
<Párrafo corto que ubica la PR en la sección del diseño: "<sección del diseño>".>

```mermaid
flowchart LR
  <solo el flujo que toca esta PR, hasta 12 nodos; lo nuevo resaltado>
```

## Decisiones de implementación
| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| <lo que el diseño no decía y se resolvió acá> | | |

**Desvíos del diseño:** <cada uno, con el motivo; o "ninguno".>

## Valores provisionales
| Valor | Dónde vive | Lo define |
|---|---|---|

## Dónde mirar
1. [`<archivo>#L<n>`](<link al archivo en la rama>): <qué decidir o verificar ahí>.
2. …
(3 a 5 puntos, donde hace falta criterio humano: contratos, cálculo de timecode, permisos, costo, manejo de errores.)

## Evidencia
- Tests: <qué cubren y el resultado>.
- <Corrida real: salida de ejemplo, tiempos, costo.>

<details><summary>Salida de ejemplo</summary>

```text
<fragmento corto y representativo>
```
</details>

## Fuera de esta PR
- <lo que no incluye y dónde va>

## Cómo probarlo
```bash
<comando para reproducir localmente>
```
````

La descripción no lleva la línea "Generated with Claude Code" ni otra atribución.

**Reglas del texto:**

- **Sin ids internos del harness** (`T-012`, `D-004`, `A-13`, `Ref 108`) ni rutas de la carpeta del proyecto en el harness. Las rutas del propio repo de la PR sí van, con link. El fundamento se escribe en palabras, con los términos del tracker y del documento de diseño. Antes de mostrarla se revisa con grep `[TDAH]-[0-9]+` y `Ref [0-9]+`.
- **Sin credenciales ni datos del cliente** en las salidas de ejemplo. Los nombres de novelas y episodios del piloto sí van.
- **El diagrama** es mermaid, porque GitHub lo renderiza. No va HTML con estilos ni scripts, porque GitHub no lo renderiza.
- **Los links de "Dónde mirar"** apuntan al archivo en la rama de la PR, con la línea.

## 3. Presentar y publicar

1. Mostrar la descripción completa al usuario. Una PR en un repo del cliente es una escritura externa: no se publica sin OK.
2. Con OK: `gh pr create --title "<título en el idioma del cliente>" --body-file <archivo en el scratchpad>` o `gh pr edit <n> --body-file …`. Revisor: el validador de la tarea.
3. Si la PR cambia después de publicada (commits nuevos, decisiones nuevas), actualizar la descripción con las mismas reglas y avisar qué cambió en un comentario corto.

## Lo que no hace

- No revisa ni aprueba la PR: eso es `task-review`.
- No inventa evidencia: si no corrió, dice que no corrió.
- No publica, no mergea ni asigna revisores sin OK.
