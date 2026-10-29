---
name: task-writer
description: "Formato obligatorio para redactar tareas orientadas a objetivo, no a implementación. Usar SIEMPRE que se cree, redacte, reescriba, divida o delegue una tarea, ticket, historia, issue o ítem de backlog, sea del backlog interno de un proyecto o de ClickUp, incluso si el pedido es informal ('anotá una tarea para…', 'armá un ticket', 'dividí esto en tareas', 'delegale esto a…')."
---

# task-writer

Una tarea describe **qué hay que lograr y por qué**, y deja que quien la toma decida **cómo**. Es la regla que distingue a este formato; el resto es estructura.

## Formato

```markdown
## T-NNN — <verbo en infinitivo + resultado> (máx. 10 palabras)

**Objetivo:** qué tiene que ser cierto cuando la tarea esté terminada (1-2 frases).
**Por qué importa:** qué destraba o qué riesgo reduce, en lenguaje de negocio o de proyecto.
**Contexto:** lo que ya se sabe, con links (decisión D-NNN, reunión, doc de Drive, hilo). Sin copiar contenido largo.
**Criterios de aceptación:**
- [ ] verificable por alguien que no es quien la hizo
- [ ] …
**Restricciones:** lo que no es negociable (plazo, presupuesto, seguridad, compatibilidad, qué NO entra).
**Dependencias:** T-NNN / personas / accesos necesarios. Vacío si no hay.
**Entregable:** qué se entrega y dónde queda (doc, PR, diagrama, decisión registrada).
**Owner:** una sola persona · **Validador:** a lo sumo una · **Fecha:** · **Estimación:** (opcional, con `estimate`)
```

Si el resultado necesita a más de una persona, se divide en subtareas, cada una con su owner (ver "Tareas en ClickUp: estructura" en `conventions.md`). El owner no es el usuario cuando la tarea es de ejecución o implementación.

En ClickUp, owner y validador van **solo en los campos** Assignee y Validator: la descripción no lleva la línea de responsables. La línea `**Owner:** · **Validador:**` del formato es para el backlog interno y para la propuesta que se muestra al usuario antes de crear.

## Antes de escribir: que no esté ya cubierta

Toda tarea nueva (o subtarea, o criterio que se agrega a una existente) se contrasta antes con lo que ya hay, para no pisar ni duplicar el trabajo de otro:

1. **ClickUp:** `clickup_search` con las palabras clave del objetivo y `clickup_filter_tasks` de la lista del proyecto (incluidas las cerradas recientes). Leer la descripción y las subtareas de las candidatas: muchas veces el tema está como criterio, dependencia o subtarea de otra tarea más grande.
2. **Backlog interno:** grep en `backlog/backlog.toon` y `backlog/notes.md`.
3. **Decisiones y alcance:** las decisiones vigentes (`docs/decisions/`) y lo que quedó fuera de alcance.
4. **Contexto:** action items de reuniones y propuestas de digests recientes (`index.toon`).

Según lo que aparezca:
- **Ya cubierta:** no se crea. Se dice cuál la cubre y, si hace falta, se propone sumar un criterio o un comentario ahí.
- **Cubierta en parte:** se propone ampliar la existente (criterio, subtarea dentro de ella) antes que una tarea paralela.
- **Solapa con la de otra persona:** se avisa y se define el límite entre las dos antes de crearla.
- **Contradice una decisión o algo fuera de alcance:** no se crea; se avisa.
- **No existe:** se crea siguiendo "Estructura en ClickUp".

Al proponer la tarea, decir en una línea qué se revisó y dónde queda ("subtarea de la épica X; espera a Y; la más cercana era Z, que cubre W").

## Estructura en ClickUp

Evitar llenar ClickUp de tareas sueltas (ver "Tareas en ClickUp: estructura" en `conventions.md`):

- **Épica primero:** toda tarea nueva va como subtarea (`parent`) de la épica del frente al que pertenece. Si no encaja en ninguna, se propone una épica nueva con su dueño, con OK explícito.
- **Tamaño:** una subtarea es un resultado de al menos medio día. Lo más chico va como criterio de aceptación o checklist de una tarea existente.
- **Dependencias cargadas:** además de nombrarlas en el texto, se cargan en ClickUp con `clickup_add_task_dependency` (`waiting_on` / `blocking`) al crear o reescribir. Si una dependencia no tiene tarea, se dice.
- **Consistencia:** el dueño y las fechas tienen que cerrar con las dependencias (no puede vencer antes de lo que espera).

## Reglas

- **Nada de implementación.** No incluir pasos, servicios elegidos, código, comandos ni "usar X para Y", salvo que sea una restricción real ya decidida (y en ese caso va en **Restricciones**, con su D-NNN).
  - Mal: "Crear una Lambda que lea de S3 y escriba en DynamoDB".
  - Bien: "Que los metadatos de cada archivo nuevo estén consultables en menos de 5 minutos desde que llega".
- Los criterios de aceptación se pueden comprobar con un sí o un no. Nada de "funciona bien" ni "es performante"; sí "p95 < 2 s con 100 archivos".
- Una tarea = un resultado. Si el objetivo tiene "y" entre dos resultados distintos, son dos tareas.
- Si falta el objetivo o el porqué, preguntarlo antes de escribir (en modo desatendido, dejar la tarea como propuesta con `[falta: objetivo]`).
- Para ClickUp: el mismo contenido en la descripción, pero **sin referencias internas**. El título va sin `T-NNN` y en el Contexto cada `D-NNN`, `A-xx` o archivo local se reemplaza por lo que se decidió, dicho en palabras, con links solo a ClickUp o a Drive. Ver "Texto que sale del repo" en `conventions.md`. No se crea en ClickUp sin OK explícito.
- Revisión final antes de entregar: releer y borrar toda frase que diga *cómo* hacerlo.

## Dónde se guarda

- Backlog interno: fila en `backlog/backlog.toon` + texto en `backlog/notes.md` (lo hace la skill `backlog`).
- Si se pide solo el texto (para pegar en otro lado), devolver el bloque y no escribir nada.
