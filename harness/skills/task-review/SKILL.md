---
name: task-review
description: "Revisa como validador el entregable de una tarea (documento de diseño, spike, PR, repositorio de IaC o de aplicación, modelo de datos, estándar, informe) contra sus criterios de aceptación y el diseño de solución vigente del proyecto, y deja el veredicto y un comentario listo para pegar. Usar cuando se pida revisar, validar o aprobar una tarea o entregable, qué hay en review, si algo se puede aprobar, o preparar el comentario de una revisión. También cuando se pida ver o mirar el entregable o el documento de alguien del equipo (\"vamos a ver la estimación de X\", \"mirá el doc de Y\"), un documento de Drive o un PR asociado a una tarea, o una tarea que está en review."
---

# task-review

Revisión de un entregable desde el rol de validador. La pregunta no es "¿cómo lo haría yo?", sino **"¿cumple lo que la tarea pidió y coincide con el diseño de solución vigente?"**. Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`.

## Principios

- **Por defecto, solo lo crítico.** Salvo que el usuario pida una revisión exhaustiva, se verifica que las definiciones importantes para el diseño estén y sean correctas; no tiene que ser perfecto. La descripción de la tarea es una propuesta, no un checklist: lo que propone como contenido queda a criterio de cada desarrollador. Un hallazgo entra en el comentario solo si cambia una decisión del diseño, contradice una decisión vigente o es un riesgo de seguridad, de datos del cliente o de costo. Menores y puntos de la descripción que no cambian el diseño no se piden ni bloquean el cierre.
- **Según la fase.** En una fase de diseño solo bloquea lo que cambia el diseño o incumple un criterio de aceptación. El detalle de implementación (concurrencia, umbrales de alarma, particionado, reintentos, estructura de datos internos) va como nota para la construcción y no bloquea. Antes de marcar algo como bloqueante: ¿se puede cerrar la tarea con esto como nota? Si sí, no bloquea.
- **Una sola vuelta.** Todos los hallazgos juntos en el primer comentario, no por capas. Antes de comentar se sigue de punta a punta cada flujo que cruza documentos (por ejemplo, rostros: indexado, agrupado, nombrado, borrado) y se cruzan los números entre los documentos de la misma entrega. La segunda vuelta solo verifica lo pedido.
- **Un número no se afirma sin fuente.** Precios, tarifas y medidas no se citan de memoria ni de otro documento: se verifican contra la fuente primaria (API de precios, factura, datos medidos) y, si se puede, con una cuenta propia; si no se pudo verificar, se dice. Un valor que parece "diez veces menor" o "distinto" puede ser el documento viejo el equivocado.
- **Revisor, no autor.** Se marca qué no cumple y por qué. El cómo resolverlo es del responsable. Cuando el responsable es el especialista del tema (infraestructura, seguridad, front, datos; ver su rol en `project.toml [[team]]`), solo se marca lo crítico y lo que se desvía del diseño; el resto queda a su criterio.
- **Leer todo el entregable antes de opinar.** Un resumen ajeno no alcanza para un veredicto.
- **Ningún hallazgo crítico se reporta sin verificarlo en la fuente** (el archivo y la línea, o la cita del documento).
- **La vara es el diseño vigente**, no preferencias personales ni el estado del diseño cuando se creó la tarea.

## 1. Juntar

1. **La tarea**, desde el tracker del proyecto (`project.toml`): descripción completa, criterios de aceptación, lo marcado como "ya decidido", qué destraba, dueño y validador, adjuntos, subtareas, dependencias y comentarios.
2. **El entregable**, según el tipo:
   - Documento o PDF (adjunto o Drive): leerlo entero. Si el conector lo corta por tamaño, guardar el texto en el scratchpad y leerlo por partes.
   - Repositorio: clonarlo en una carpeta nueva del scratchpad. Solo lectura: no se ejecuta nada del repo (ni scripts, ni build, ni terraform). `git log`/`git show` sí.
   - PR: el diff (`gh pr diff`) y la descripción. Si la descripción sigue `pr-brief`, se arranca por sus decisiones, desvíos y "Dónde mirar", pero cada punto crítico se verifica en el diff.
3. **El diseño vigente del proyecto.** Buscar primero en `index.toon` y abrir solo lo que aplique:
   - las decisiones (`docs/decisions/`), con más atención a las **posteriores a la creación de la tarea**: son las que más desvíos explican;
   - el documento de arquitectura vigente;
   - reuniones y digests recientes que toquen el tema.
4. **Estándares de la práctica** que apliquen al tipo de entregable (por ejemplo, la skill de estándar de Terraform para IaC).

Si el entregable es grande o tiene varias dimensiones (por ejemplo, pipeline de CI/CD e infraestructura), se puede repartir en agentes en paralelo, uno por dimensión. Cada uno recibe los criterios explícitos y un formato de salida: tabla criterio → estado con evidencia, hallazgos por severidad con un escenario concreto de falla, y veredicto. Los agentes trabajan en solo lectura. El veredicto final lo arma la sesión principal después de verificar en la fuente cada hallazgo bloqueante o importante: lo que un agente reporta y no se verificó no se presenta como hecho.

## 2. Evaluar

- **Criterios de aceptación**, uno por uno: Cumple / Parcial / No cumple, con evidencia (sección del documento o `archivo:línea`).
- **Contra el diseño.** Listar las decisiones que aplican y marcar los desvíos. Distinguir entre "quedó desactualizado frente a una decisión posterior" (se actualiza, no es un error del autor) y "contradice una decisión vigente".
- **Verificar en la fuente** cada hallazgo que vaya a ser bloqueante y marcarlo como verificado.
- **Clasificar:**
  - **Bloqueante:** no cumple un criterio, contradice el diseño, o es un riesgo de seguridad, de datos del cliente o de costo. Se verifica en la fuente.
  - **Para la fase siguiente:** detalle de implementación o mejora que no cambia el diseño. Va en el comentario aparte, sin bloquear, o directo a la especificación de la construcción.
  - **A criterio del responsable:** menores, prolijidad, estilo. No se piden.
- **Medición que depende de otro.** Si el criterio exige una medición cuyo insumo el responsable no controla (una anotación, datos de otro equipo), se aprueba el diseño y la medición pasa a una tarea de la fase siguiente, con el pendiente escrito (`task-writer`). No se devuelve la tarea por eso.
- **Decisiones que la tarea deja al validador:** recomendación con fundamento y la alternativa. La decide el usuario.
- **Pendientes que deja el autor:** responder los que ya tienen respuesta en el diseño; el resto queda abierto.
- **Aprobación parcial:** si una parte destraba a otras personas y está bien, se puede aprobar esa parte y devolver el resto.

## 3. Presentar al usuario

1. Qué entrega, en 2 a 4 líneas.
2. Tabla de criterios.
3. Hallazgos por severidad, con los verificados marcados.
4. Decisiones para el usuario, con recomendación.
5. **Veredicto:** aprobar, aprobar con condiciones (cuáles) o devolver.
6. **Comentario para la tarea**, en un bloque ` ```text ` de texto plano (ver "Texto que sale del repo" en `conventions.md`):
   - sin ids internos, rutas ni nombres de archivos locales;
   - sin elogios ni resumen de lo que está bien: solo lo que falta agregar o cambiar (si se aprueba, una línea que lo diga);
   - "Para cerrar:" con un máximo de 4 puntos numerados, con el qué y el porqué, no el cómo. Si salen más, se reagrupa dejando solo los que cambian el diseño;
   - "Para la fase siguiente (no bloquea):" en una línea aparte, con lo que no bloquea;
   - lo que el validador ya decidió se dice como hecho ("aceptado como está: ..."), no como pregunta;
   - si el responsable es el especialista, en forma de observación o pregunta;
   - no se pide una sesión o reunión que no exija la tarea y que la revisión escrita ya cubre;
   - los menores no se piden.
7. **Acciones propuestas:** cambio de estado, tareas a separar, dependencias a cargar, decisiones a registrar.

## 4. Con OK del usuario

- **Comentario:** lo publica el usuario, salvo que pida que lo publique la skill.
- **Estado:** aprobada → completada; devuelta → en progreso.
- **Corregir un comentario ya publicado:** se edita (`clickup_update_comment`) en lugar de sumar otro, y se borran las aclaraciones propias que hayan quedado de más. Editar no avisa a nadie: el comentario termina con "Actualizado el <fecha>: <qué cambió>" y se avisa por el canal del equipo.
- **Comentarios que se acumulan:** si el responsable no resuelve después de dos vueltas, se revisa antes de pedir más: ¿el comentario es claro, tiene más de 4 puntos, mezcla lo que bloquea con lo que no? Se reescribe con el criterio de arriba.
- **Alcance que se separa:** tarea nueva con `task-writer`, con sus dependencias en el tracker.
- **Decisiones que salen de la revisión:** entrada nueva en `docs/decisions/decisions.md`.
- Si se escribió algo en el repo del proyecto: commit `harness(review): <tarea>`.

## Lo que no hace

- No reescribe el entregable ni propone la implementación.
- No publica comentarios, no cambia estados ni crea tareas sin OK explícito.
- No ejecuta código del entregable.
